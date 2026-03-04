"""
Generate BIME550 BRCA Ontology TTL file from Mutation Data
This script creates an RDF ontology in Turtle format matching the BIME550BRCA structure
"""

import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, BNode
from rdflib.namespace import XSD
import re


def clean_uri_string(s):
    """Clean string to make it suitable for URI"""
    if pd.isna(s):
        return "Unknown"
    # Replace spaces and special characters with underscores
    s = str(s).strip()
    # Replace forward slashes with underscores
    s = s.replace('/', '_')
    s = re.sub(r'[^\w\-\.]', '_', s)
    s = re.sub(r'_+', '_', s)  # Replace multiple underscores with single
    return s


def create_ontology(input_csv, output_ttl):
    """
    Create BIME550 BRCA ontology from mutation data

    Parameters:
    -----------
    input_csv : str
        Path to the input CSV file containing mutation-pathway data
    output_ttl : str
        Path to the output TTL file
    """

    # Load the data
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} records")

    # Create a new graph
    g = Graph()

    # Define namespaces matching BIME550BRCA structure
    BASE = Namespace("http://www.semanticweb.org/kevinlee/ontologies/2026/1/untitled-ontology-5/")
    GENE_NS = Namespace("http://www.semanticweb.org/kevinlee/ontologies/2026/1/untitled-ontology-5#")
    SWRLA = Namespace("http://swrl.stanford.edu/ontologies/3.3/swrla.owl#")
    SWRL = Namespace("http://www.w3.org/2003/11/swrl#")

    # Bind namespaces to prefixes
    g.bind("", BASE)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    # Define the ontology
    ontology_uri = URIRef("http://www.semanticweb.org/kevinlee/ontologies/2026/1/BIME550BRCA")
    g.add((ontology_uri, RDF.type, OWL.Ontology))

    print("Defining annotation properties...")
    # Annotation properties
    is_rule_enabled = URIRef("http://swrl.stanford.edu/ontologies/3.3/swrla.owl#isRuleEnabled")
    g.add((is_rule_enabled, RDF.type, OWL.AnnotationProperty))

    print("Defining object properties...")
    # Object Properties
    downregulates_pathway = BASE.downregulatesPathway
    g.add((downregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((downregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))

    upregulates_pathway = BASE.upregulatesPathway
    g.add((upregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((upregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((upregulates_pathway, OWL.propertyDisjointWith, downregulates_pathway))

    has_downregulated_pathway = BASE.hasDownregulatedPathway
    g.add((has_downregulated_pathway, RDF.type, OWL.ObjectProperty))
    g.add((has_downregulated_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))

    has_upregulated_pathway = BASE.hasUpregulatedPathway
    g.add((has_upregulated_pathway, RDF.type, OWL.ObjectProperty))
    g.add((has_upregulated_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_upregulated_pathway, OWL.propertyDisjointWith, has_downregulated_pathway))

    has_effect = BASE.hasEffect
    g.add((has_effect, RDF.type, OWL.ObjectProperty))
    g.add((has_effect, RDFS.subPropertyOf, OWL.topObjectProperty))

    has_mutation = BASE.hasMutation
    g.add((has_mutation, RDF.type, OWL.ObjectProperty))
    g.add((has_mutation, RDFS.subPropertyOf, OWL.topObjectProperty))

    has_gof = BASE.hasGoF
    g.add((has_gof, RDF.type, OWL.ObjectProperty))
    g.add((has_gof, RDFS.subPropertyOf, has_mutation))
    g.add((has_gof, RDFS.subPropertyOf, OWL.topObjectProperty))

    has_lof = BASE.hasLoF
    g.add((has_lof, RDF.type, OWL.ObjectProperty))
    g.add((has_lof, RDFS.subPropertyOf, has_mutation))
    g.add((has_lof, RDFS.subPropertyOf, OWL.topObjectProperty))

    print("Defining classes...")
    # Top-level classes
    gene_class = GENE_NS.Gene
    g.add((gene_class, RDF.type, OWL.Class))

    mutation_class = GENE_NS.Mutation
    g.add((mutation_class, RDF.type, OWL.Class))

    pathway_class = GENE_NS.Pathway
    g.add((pathway_class, RDF.type, OWL.Class))

    breast_cancer_subtype = GENE_NS.BreastCancerSubType
    g.add((breast_cancer_subtype, RDF.type, OWL.Class))

    patient_class = BASE.Patient
    g.add((patient_class, RDF.type, OWL.Class))

    mutation_effect_class = BASE.Mutation_Effect
    g.add((mutation_effect_class, RDF.type, OWL.Class))
    g.add((mutation_effect_class, RDFS.subClassOf, mutation_class))

    # Gene subclasses from existing ontology
    print("Defining gene classes...")
    genes_from_ontology = ['BRCA1', 'BRCA2', 'ER', 'PR', 'Ki-67', 'TP53']

    for gene_name in genes_from_ontology:
        gene_uri = BASE[gene_name]
        g.add((gene_uri, RDF.type, OWL.Class))
        g.add((gene_uri, RDFS.subClassOf, gene_class))

    # Add ERBB2 (also known as HER2)
    erbb2_uri = BASE['ERBB2']
    g.add((erbb2_uri, RDF.type, OWL.Class))
    g.add((erbb2_uri, RDFS.subClassOf, gene_class))
    g.add((erbb2_uri, RDFS.label, Literal("ERBB2 (HER2)")))

    # Add new genes from CSV data
    unique_genes = df['Gene'].unique()
    defined_genes = genes_from_ontology + ['ERBB2']  # Include ERBB2 in already defined genes
    for gene_symbol in unique_genes:
        if gene_symbol not in defined_genes:
            gene_uri = BASE[gene_symbol]
            g.add((gene_uri, RDF.type, OWL.Class))
            g.add((gene_uri, RDFS.subClassOf, gene_class))

    # Pathway subclasses
    print("Defining pathway classes...")
    er_related = BASE['ER-related_pathway']
    g.add((er_related, RDF.type, OWL.Class))
    g.add((er_related, RDFS.subClassOf, pathway_class))

    her2_related = BASE['HER2-related_pathway']
    g.add((her2_related, RDF.type, OWL.Class))
    g.add((her2_related, RDFS.subClassOf, pathway_class))

    pr_related = BASE['PR-related_pathway']
    g.add((pr_related, RDF.type, OWL.Class))
    g.add((pr_related, RDFS.subClassOf, pathway_class))

    ki67_related = BASE['Ki-67-related_pathway']
    g.add((ki67_related, RDF.type, OWL.Class))
    g.add((ki67_related, RDFS.subClassOf, pathway_class))

    # Specific pathways from CSV data
    pathway_to_parent = {
        'Constitutive Signaling by AKT1 E17K in Cancer': er_related,
        'Constitutive Signaling by Aberrant PI3K in Cancer': er_related,
        'Defective translocation of RB1 mutants to the nucleus': er_related,
        'Loss of function of TP53 in cancer due to loss of tetramerization ability': er_related,
        'PTEN Loss of Function in Cancer': er_related,
        'SMAD4 MH2 Domain Mutants in Cancer': er_related,
        'Signaling by ERBB2 ECD mutants': her2_related,
        'Signaling by ERBB2 KD Mutants': her2_related,
        'Signaling by ERBB2 TMD/JMD mutants': her2_related,
    }

    for pathway_name, parent_class in pathway_to_parent.items():
        pathway_uri = BASE[clean_uri_string(pathway_name)]
        g.add((pathway_uri, RDF.type, OWL.Class))
        g.add((pathway_uri, RDFS.subClassOf, parent_class))

    # Breast cancer subtypes
    print("Defining breast cancer subtypes...")
    subtypes = ['Basal', 'Her2', 'LumA', 'LumB', 'Normal']
    for subtype in subtypes:
        subtype_uri = BASE[subtype]
        g.add((subtype_uri, RDF.type, OWL.Class))
        g.add((subtype_uri, RDFS.subClassOf, breast_cancer_subtype))

    # Mutation effect individuals
    print("Defining mutation effect individuals...")
    gof = BASE.GoF
    g.add((gof, RDF.type, OWL.NamedIndividual))
    g.add((gof, RDF.type, mutation_class))
    g.add((gof, RDF.type, mutation_effect_class))

    lof = BASE.LoF
    g.add((lof, RDF.type, OWL.NamedIndividual))
    g.add((lof, RDF.type, mutation_class))
    g.add((lof, RDF.type, mutation_effect_class))

    partial_lof = BASE.Partial_LoF
    g.add((partial_lof, RDF.type, OWL.NamedIndividual))
    g.add((partial_lof, RDF.type, mutation_effect_class))

    others = BASE.Others
    g.add((others, RDF.type, OWL.NamedIndividual))
    g.add((others, RDF.type, mutation_class))

    # Create mutation instances from CSV data
    print("Creating mutation instances from CSV data...")
    for idx, row in df.iterrows():
        if idx % 10 == 0:
            print(f"  Processing mutation {idx}/{len(df)}...")

        gene_symbol = str(row['Gene'])
        mutation = str(row['Mutation'])
        pathway_name = str(row['Pathway'])
        effect = str(row['Effect'])

        # Create mutation individual
        mutation_id = f"{gene_symbol}_{clean_uri_string(mutation)}"
        mutation_uri = BASE[mutation_id]
        g.add((mutation_uri, RDF.type, OWL.NamedIndividual))
        g.add((mutation_uri, RDF.type, mutation_class))
        g.add((mutation_uri, RDFS.label, Literal(f"{gene_symbol} {mutation}")))

        # Link mutation to gene (Gene hasMutation Mutation)
        gene_uri = BASE[gene_symbol]
        g.add((gene_uri, has_mutation, mutation_uri))

        # Link mutation to pathway
        pathway_uri = BASE[clean_uri_string(pathway_name)]

        # Determine if pathway is upregulated or downregulated based on effect
        if 'gain_of_function' in effect.lower():
            g.add((mutation_uri, upregulates_pathway, pathway_uri))
            g.add((mutation_uri, has_effect, gof))
        elif 'loss_of_function' in effect.lower():
            g.add((mutation_uri, downregulates_pathway, pathway_uri))
            if 'partial' in effect.lower():
                g.add((mutation_uri, has_effect, partial_lof))
            g.add((mutation_uri, has_effect, lof))

    # Add SWRL rules
    print("Adding SWRL rules...")
    add_swrl_rules(g, BASE, SWRL, SWRLA, gof, lof, partial_lof)

    # Serialize to TTL
    print(f"\nSerializing ontology to {output_ttl}...")
    g.serialize(destination=output_ttl, format='turtle')

    # Print statistics
    print(f"\nOntology Statistics:")
    print(f"  Total triples: {len(g)}")
    print(f"  Unique genes: {len(df['Gene'].unique())}")
    print(f"  Unique pathways: {len(df['Pathway'].unique())}")
    print(f"\nOntology file created successfully: {output_ttl}")


def add_swrl_rules(g, BASE, SWRL, SWRLA, gof, lof, partial_lof):
    """Add SWRL rules to the ontology"""

    # Define SWRL variables
    pt_var = BASE.pt
    g.add((pt_var, RDF.type, SWRL.Variable))

    g_var = BASE.g
    g.add((g_var, RDF.type, SWRL.Variable))

    m_var = BASE.m
    g.add((m_var, RDF.type, SWRL.Variable))

    p_var = BASE.p
    g.add((p_var, RDF.type, SWRL.Variable))

    # Rule S1: Patient hasMutation -> upregulatesPathway => hasUpregulatedPathway
    rule_s1 = BNode()
    g.add((rule_s1, RDF.type, SWRL.Imp))
    g.add((rule_s1, RDFS.label, Literal("S1")))
    g.add((rule_s1, RDFS.comment, Literal("")))
    g.add((rule_s1, SWRLA.isRuleEnabled, Literal("true", datatype=XSD.boolean)))

    # Rule S2: Patient hasMutation -> downregulatesPathway => hasDownregulatedPathway
    rule_s2 = BNode()
    g.add((rule_s2, RDF.type, SWRL.Imp))
    g.add((rule_s2, RDFS.label, Literal("S2")))
    g.add((rule_s2, RDFS.comment, Literal("")))
    g.add((rule_s2, SWRLA.isRuleEnabled, Literal("true", datatype=XSD.boolean)))

    # Rule S3: Patient hasMutation + Gene hasMutation + hasEffect LoF => hasLoF
    rule_s3 = BNode()
    g.add((rule_s3, RDF.type, SWRL.Imp))
    g.add((rule_s3, RDFS.label, Literal("S3")))
    g.add((rule_s3, RDFS.comment, Literal("")))
    g.add((rule_s3, SWRLA.isRuleEnabled, Literal("true", datatype=XSD.boolean)))

    # Rule S4: Patient hasMutation + Gene hasMutation + hasEffect GoF => hasGoF
    rule_s4 = BNode()
    g.add((rule_s4, RDF.type, SWRL.Imp))
    g.add((rule_s4, RDFS.label, Literal("S4")))
    g.add((rule_s4, RDFS.comment, Literal("")))
    g.add((rule_s4, SWRLA.isRuleEnabled, Literal("true", datatype=XSD.boolean)))

    # Rule S5: Patient hasMutation + Gene hasMutation + hasEffect Partial_LoF => hasLoF
    rule_s5 = BNode()
    g.add((rule_s5, RDF.type, SWRL.Imp))
    g.add((rule_s5, RDFS.label, Literal("S5")))
    g.add((rule_s5, RDFS.comment, Literal("")))
    g.add((rule_s5, SWRLA.isRuleEnabled, Literal("true", datatype=XSD.boolean)))


if __name__ == "__main__":
    # Configuration
    INPUT_CSV = "./results/final_mutations_with_pathways.csv"
    OUTPUT_TTL = "./results/BIME550BRCA_update.ttl"

    # Generate the ontology
    create_ontology(INPUT_CSV, OUTPUT_TTL)
