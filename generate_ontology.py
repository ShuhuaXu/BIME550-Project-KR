"""
Generate Ontology TTL file from TCGA-BRCA Mutation Data
This script creates an RDF ontology in Turtle format from the merged mutation dataset
"""

import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD
import re


def clean_uri_string(s):
    """Clean string to make it suitable for URI"""
    if pd.isna(s):
        return "Unknown"
    # Replace spaces and special characters with underscores
    s = str(s).strip()
    s = re.sub(r'[^\w\-\.]', '_', s)
    s = re.sub(r'_+', '_', s)  # Replace multiple underscores with single
    return s


def create_ontology(input_csv, output_ttl):
    """
    Create an ontology from the TCGA-BRCA mutation data

    Parameters:
    -----------
    input_csv : str
        Path to the input CSV file containing merged mutation data
    output_ttl : str
        Path to the output TTL file
    """

    # Load the data
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} records")

    # Create a new graph
    g = Graph()

    # Define namespaces
    BASE = Namespace("http://example.org/tcga-brca/")
    TCGA = Namespace("http://example.org/tcga-brca/entity/")
    PROP = Namespace("http://example.org/tcga-brca/property/")

    # Bind namespaces to prefixes
    g.bind("base", BASE)
    g.bind("tcga", TCGA)
    g.bind("prop", PROP)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    # Define the ontology
    ontology_uri = BASE["ontology"]
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, RDFS.label, Literal("TCGA Breast Cancer Mutation Ontology")))
    g.add((ontology_uri, RDFS.comment, Literal(
        "An ontology describing TCGA-BRCA mutations with exact matches to Reactome pathways. "
        "Integrates TCGA breast cancer mutation data (MC3 MAF) with Reactome disease variant "
        "annotations, including pathway information, functional status (gain/loss of function), "
        "and disease associations."
    )))

    # Define Classes
    print("Defining ontology classes...")
    classes = {
        "Gene": "A gene that can have mutations",
        "Mutation": "A genetic mutation/variant",
        "Patient": "A patient/sample with mutations",
        "Pathway": "A biological pathway from Reactome",
        "Chromosome": "A chromosome location",
        "VariantClassification": "Classification of variant type",
        "FunctionalStatus": "Functional status of the mutation (gain/loss of function)",
        "Disease": "A disease associated with mutations"
    }

    for class_name, description in classes.items():
        class_uri = TCGA[class_name]
        g.add((class_uri, RDF.type, OWL.Class))
        g.add((class_uri, RDFS.label, Literal(class_name)))
        g.add((class_uri, RDFS.comment, Literal(description)))

    # Define Object Properties
    print("Defining object properties...")
    object_properties = {
        "hasGene": ("Mutation", "Gene", "Links a mutation to its gene"),
        "hasMutation": ("Patient", "Mutation", "Links a patient to their mutations"),
        "involvedInPathway": ("Mutation", "Pathway", "Links a mutation to biological pathways"),
        "locatedOnChromosome": ("Mutation", "Chromosome", "Chromosome location of mutation"),
        "hasVariantClassification": ("Mutation", "VariantClassification", "Type of variant"),
        "hasFunctionalStatus": ("Mutation", "FunctionalStatus", "Functional impact of mutation"),
        "associatedWithDisease": ("Mutation", "Disease", "Diseases associated with mutation")
    }

    for prop_name, (domain, range_class, description) in object_properties.items():
        prop_uri = PROP[prop_name]
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.label, Literal(prop_name)))
        g.add((prop_uri, RDFS.comment, Literal(description)))
        g.add((prop_uri, RDFS.domain, TCGA[domain]))
        g.add((prop_uri, RDFS.range, TCGA[range_class]))

    # Define Data Properties
    print("Defining data properties...")
    data_properties = {
        "geneSymbol": (XSD.string, "Gene symbol"),
        "geneName": (XSD.string, "Gene name from Reactome"),
        "hgvspShort": (XSD.string, "HGVS protein notation (short form)"),
        "displayName": (XSD.string, "Reactome display name for the mutation"),
        "chromosomeNumber": (XSD.string, "Chromosome number"),
        "startPosition": (XSD.integer, "Genomic start position"),
        "variantType": (XSD.string, "Type of variant"),
        "patientBarcode": (XSD.string, "Patient/sample barcode"),
        "caseId": (XSD.string, "TCGA case identifier"),
        "projectId": (XSD.string, "TCGA project identifier"),
        "pathwayName": (XSD.string, "Pathway name"),
        "functionalStatusType": (XSD.string, "Type of functional status"),
        "diseaseName": (XSD.string, "Disease name")
    }

    for prop_name, (datatype, description) in data_properties.items():
        prop_uri = PROP[prop_name]
        g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
        g.add((prop_uri, RDFS.label, Literal(prop_name)))
        g.add((prop_uri, RDFS.comment, Literal(description)))
        g.add((prop_uri, RDFS.range, datatype))

    # Create instances from data
    print("Creating instances from data...")

    # Track created entities to avoid duplicates
    genes = set()
    chromosomes = set()
    pathways = set()
    variant_classifications = set()
    functional_statuses = set()
    diseases_set = set()

    # Process each row
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  Processing record {idx}/{len(df)}...")

        # Create Gene instance
        gene_symbol = str(row['Hugo_Symbol']) if pd.notna(row['Hugo_Symbol']) else "Unknown"
        gene_uri = TCGA[f"gene_{clean_uri_string(gene_symbol)}"]
        if gene_symbol not in genes:
            g.add((gene_uri, RDF.type, TCGA.Gene))
            g.add((gene_uri, RDFS.label, Literal(gene_symbol)))
            g.add((gene_uri, PROP.geneSymbol, Literal(gene_symbol, datatype=XSD.string)))
            # Add Genename from Reactome if available
            if 'Genename' in df.columns and pd.notna(row.get('Genename')):
                genename = str(row['Genename'])
                g.add((gene_uri, PROP.geneName, Literal(genename, datatype=XSD.string)))
            genes.add(gene_symbol)

        # Create Patient instance
        patient_barcode = str(row['Tumor_Sample_Barcode']) if pd.notna(row['Tumor_Sample_Barcode']) else f"Unknown_{idx}"
        patient_uri = TCGA[f"patient_{clean_uri_string(patient_barcode)}"]
        g.add((patient_uri, RDF.type, TCGA.Patient))
        g.add((patient_uri, RDFS.label, Literal(patient_barcode)))
        g.add((patient_uri, PROP.patientBarcode, Literal(patient_barcode, datatype=XSD.string)))

        # Add case_id if available
        if 'case_id' in df.columns and pd.notna(row.get('case_id')):
            case_id = str(row['case_id'])
            g.add((patient_uri, PROP.caseId, Literal(case_id, datatype=XSD.string)))

        # Add project_id if available
        if 'project_id' in df.columns and pd.notna(row.get('project_id')):
            g.add((patient_uri, PROP.projectId, Literal(str(row['project_id']), datatype=XSD.string)))

        # Create Mutation instance
        hgvsp = str(row['HGVSp_Short']) if pd.notna(row['HGVSp_Short']) else "Unknown"
        mutation_id = f"{gene_symbol}_{hgvsp}_{patient_barcode}"
        mutation_uri = TCGA[f"mutation_{clean_uri_string(mutation_id)}"]
        g.add((mutation_uri, RDF.type, TCGA.Mutation))
        g.add((mutation_uri, RDFS.label, Literal(f"{gene_symbol} {hgvsp}")))
        g.add((mutation_uri, PROP.hgvspShort, Literal(hgvsp, datatype=XSD.string)))

        # Add displayName from Reactome if available
        if 'displayName' in df.columns and pd.notna(row.get('displayName')):
            display_name = str(row['displayName'])
            g.add((mutation_uri, PROP.displayName, Literal(display_name, datatype=XSD.string)))

        # Link mutation to gene
        g.add((mutation_uri, PROP.hasGene, gene_uri))

        # Link patient to mutation
        g.add((patient_uri, PROP.hasMutation, mutation_uri))

        # Add chromosome information
        if pd.notna(row['Chromosome']):
            chrom = str(row['Chromosome'])
            chrom_uri = TCGA[f"chromosome_{clean_uri_string(chrom)}"]
            if chrom not in chromosomes:
                g.add((chrom_uri, RDF.type, TCGA.Chromosome))
                g.add((chrom_uri, RDFS.label, Literal(f"Chromosome {chrom}")))
                g.add((chrom_uri, PROP.chromosomeNumber, Literal(chrom, datatype=XSD.string)))
                chromosomes.add(chrom)
            g.add((mutation_uri, PROP.locatedOnChromosome, chrom_uri))

        # Add start position
        if pd.notna(row['Start_Position']):
            try:
                start_pos = int(row['Start_Position'])
                g.add((mutation_uri, PROP.startPosition, Literal(start_pos, datatype=XSD.integer)))
            except (ValueError, TypeError):
                pass

        # Add variant classification
        if pd.notna(row['Variant_Classification']):
            var_class = str(row['Variant_Classification'])
            var_class_uri = TCGA[f"variant_{clean_uri_string(var_class)}"]
            if var_class not in variant_classifications:
                g.add((var_class_uri, RDF.type, TCGA.VariantClassification))
                g.add((var_class_uri, RDFS.label, Literal(var_class)))
                g.add((var_class_uri, PROP.variantType, Literal(var_class, datatype=XSD.string)))
                variant_classifications.add(var_class)
            g.add((mutation_uri, PROP.hasVariantClassification, var_class_uri))

        # Add pathway information
        if pd.notna(row['entityWithAccessionedSequence_pathway_displayName']):
            pathway_name = str(row['entityWithAccessionedSequence_pathway_displayName'])
            pathway_uri = TCGA[f"pathway_{clean_uri_string(pathway_name)}"]
            if pathway_name not in pathways:
                g.add((pathway_uri, RDF.type, TCGA.Pathway))
                g.add((pathway_uri, RDFS.label, Literal(pathway_name)))
                g.add((pathway_uri, PROP.pathwayName, Literal(pathway_name, datatype=XSD.string)))
                pathways.add(pathway_name)
            g.add((mutation_uri, PROP.involvedInPathway, pathway_uri))

        # Add functional status
        func_status_col = 'entityWithAccessionedSequence_reactionLikeEvent_entityFunctionalStatus_functionalStatus_functionalStatusType_displayName'
        if pd.notna(row[func_status_col]):
            func_status = str(row[func_status_col])
            # Handle multiple statuses separated by |
            for status in func_status.split('|'):
                status = status.strip()
                status_uri = TCGA[f"functional_status_{clean_uri_string(status)}"]
                if status not in functional_statuses:
                    g.add((status_uri, RDF.type, TCGA.FunctionalStatus))
                    g.add((status_uri, RDFS.label, Literal(status)))
                    g.add((status_uri, PROP.functionalStatusType, Literal(status, datatype=XSD.string)))
                    functional_statuses.add(status)
                g.add((mutation_uri, PROP.hasFunctionalStatus, status_uri))

        # Add disease information
        if pd.notna(row['disease']):
            diseases_str = str(row['disease'])
            # Handle multiple diseases separated by |
            for disease in diseases_str.split('|'):
                disease = disease.strip()
                disease_uri = TCGA[f"disease_{clean_uri_string(disease)}"]
                if disease not in diseases_set:
                    g.add((disease_uri, RDF.type, TCGA.Disease))
                    g.add((disease_uri, RDFS.label, Literal(disease)))
                    g.add((disease_uri, PROP.diseaseName, Literal(disease, datatype=XSD.string)))
                    diseases_set.add(disease)
                g.add((mutation_uri, PROP.associatedWithDisease, disease_uri))

    # Serialize to TTL
    print(f"\nSerializing ontology to {output_ttl}...")
    g.serialize(destination=output_ttl, format='turtle')

    # Print statistics
    print(f"\nOntology Statistics:")
    print(f"  Total triples: {len(g)}")
    print(f"  Unique genes: {len(genes)}")
    print(f"  Unique chromosomes: {len(chromosomes)}")
    print(f"  Unique pathways: {len(pathways)}")
    print(f"  Unique variant classifications: {len(variant_classifications)}")
    print(f"  Unique functional statuses: {len(functional_statuses)}")
    print(f"  Unique diseases: {len(diseases_set)}")
    print(f"\nOntology file created successfully: {output_ttl}")


if __name__ == "__main__":
    # Configuration
    INPUT_CSV = "./results/final_mutations_with_pathways.csv"
    OUTPUT_TTL = "./results/tcga_brca_ontology.ttl"

    # Generate the ontology
    create_ontology(INPUT_CSV, OUTPUT_TTL)
