"""
Generate BIME550 BRCA Ontology TTL file from Mutation Data
This script creates an RDF ontology in Turtle format matching the BIME550BRCA structure,
using pure OWL2 property chains (no SWRL) and equivalent class axioms for
breast cancer subtype classification via Protege reasoning (HermiT-compatible).
"""

import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, BNode
from rdflib.namespace import XSD
from rdflib.collection import Collection
import re


# ── Namespaces ──────────────────────────────────────────────────────────────
BASE = Namespace("http://www.semanticweb.org/kevinlee/ontologies/2026/1/untitled-ontology-5/")
GENE_NS = Namespace("http://www.semanticweb.org/kevinlee/ontologies/2026/1/untitled-ontology-5#")


def clean_uri_string(s):
    """Clean string to make it suitable for URI"""
    if pd.isna(s):
        return "Unknown"
    s = str(s).strip()
    s = s.replace('/', '_')
    s = re.sub(r'[^\w\-\.]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s


# ── OWL Helper Functions ───────────────────────────────────────────────────

def owl_some(g, prop, filler):
    """Create owl:Restriction with owl:someValuesFrom (existential restriction)"""
    r = BNode()
    g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, prop))
    g.add((r, OWL.someValuesFrom, filler))
    return r


def owl_complement(g, cls):
    """Create owl:complementOf (negation)"""
    c = BNode()
    g.add((c, RDF.type, OWL.Class))
    g.add((c, OWL.complementOf, cls))
    return c


def owl_union(g, classes):
    """Create owl:unionOf"""
    u = BNode()
    g.add((u, RDF.type, OWL.Class))
    list_node = BNode()
    Collection(g, list_node, classes)
    g.add((u, OWL.unionOf, list_node))
    return u


def owl_intersection(g, classes):
    """Create owl:intersectionOf"""
    i = BNode()
    g.add((i, RDF.type, OWL.Class))
    list_node = BNode()
    Collection(g, list_node, classes)
    g.add((i, OWL.intersectionOf, list_node))
    return i


# ── Main Ontology Builder ─────────────────────────────────────────────────

def create_ontology(input_csv, output_ttl):
    """
    Create BIME550 BRCA ontology from mutation data with full reasoning support.
    """
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} records")

    g = Graph()

    # Bind namespaces
    g.bind("", BASE)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    # Ontology declaration
    ontology_uri = URIRef("http://www.semanticweb.org/kevinlee/ontologies/2026/1/BIME550BRCA")
    g.add((ontology_uri, RDF.type, OWL.Ontology))

    # ── Object Properties (with domain/range restrictions from original ontology) ──
    print("Defining object properties...")

    # We define classes early so we can reference them in domain/range
    gene_class = GENE_NS.Gene
    mutation_class = GENE_NS.Mutation
    pathway_class = GENE_NS.Pathway
    patient_class = BASE.Patient
    mutation_effect_class = BASE.Mutation_Effect

    downregulates_pathway = BASE.downregulatesPathway
    g.add((downregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((downregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((downregulates_pathway, RDFS.domain, mutation_class))
    g.add((downregulates_pathway, RDFS.range, pathway_class))

    upregulates_pathway = BASE.upregulatesPathway
    g.add((upregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((upregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((upregulates_pathway, RDFS.domain, mutation_class))
    g.add((upregulates_pathway, RDFS.range, pathway_class))

    normally_regulates_pathway = BASE.normallyRegulatesPathway
    g.add((normally_regulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((normally_regulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((normally_regulates_pathway, RDFS.domain, mutation_class))
    g.add((normally_regulates_pathway, RDFS.range, pathway_class))

    has_downregulated_pathway = BASE.hasDownregulatedPathway
    g.add((has_downregulated_pathway, RDF.type, OWL.ObjectProperty))
    g.add((has_downregulated_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_downregulated_pathway, RDFS.domain, patient_class))
    g.add((has_downregulated_pathway, RDFS.range, pathway_class))

    has_upregulated_pathway = BASE.hasUpregulatedPathway
    g.add((has_upregulated_pathway, RDF.type, OWL.ObjectProperty))
    g.add((has_upregulated_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_upregulated_pathway, RDFS.domain, patient_class))
    # Range will be set to PathwayCategory after it's defined (enables negation reasoning)

    has_normally_regulated_pathway = BASE.hasNormallyRegulatedPathway
    g.add((has_normally_regulated_pathway, RDF.type, OWL.ObjectProperty))
    g.add((has_normally_regulated_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_normally_regulated_pathway, RDFS.domain, patient_class))
    g.add((has_normally_regulated_pathway, RDFS.range, pathway_class))

    has_effect = BASE.hasEffect
    g.add((has_effect, RDF.type, OWL.ObjectProperty))
    g.add((has_effect, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_effect, RDFS.domain, mutation_class))
    g.add((has_effect, RDFS.range, mutation_effect_class))

    has_mutation = BASE.hasMutation
    g.add((has_mutation, RDF.type, OWL.ObjectProperty))
    g.add((has_mutation, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_mutation, RDFS.domain, patient_class))

    has_gof = BASE.hasGoF
    g.add((has_gof, RDF.type, OWL.ObjectProperty))
    # NOT a subproperty - inferred via property chain to avoid cycle
    g.add((has_gof, RDFS.domain, patient_class))
    g.add((has_gof, RDFS.range, gene_class))

    has_lof = BASE.hasLoF
    g.add((has_lof, RDF.type, OWL.ObjectProperty))
    # NOT a subproperty - inferred via property chain to avoid cycle
    g.add((has_lof, RDFS.domain, patient_class))
    g.add((has_lof, RDFS.range, gene_class))

    # Gene-to-Mutation links differentiated by effect type
    has_gof_mutation = BASE.hasGoFMutation
    g.add((has_gof_mutation, RDF.type, OWL.ObjectProperty))
    g.add((has_gof_mutation, RDFS.subPropertyOf, has_mutation))

    has_lof_mutation = BASE.hasLoFMutation
    g.add((has_lof_mutation, RDF.type, OWL.ObjectProperty))
    g.add((has_lof_mutation, RDFS.subPropertyOf, has_mutation))

    # Inverse properties: Mutation → Gene
    is_gof_mutation_of = BASE.isGoFMutationOf
    g.add((is_gof_mutation_of, RDF.type, OWL.ObjectProperty))
    g.add((is_gof_mutation_of, OWL.inverseOf, has_gof_mutation))

    is_lof_mutation_of = BASE.isLoFMutationOf
    g.add((is_lof_mutation_of, RDF.type, OWL.ObjectProperty))
    g.add((is_lof_mutation_of, OWL.inverseOf, has_lof_mutation))

    # ── Property Chains (all HermiT-compatible, no SWRL needed) ───────────
    print("Adding property chains for inference...")

    # S1: hasMutation o upregulatesPathway → hasUpregulatedPathway
    chain1 = BNode()
    Collection(g, chain1, [has_mutation, upregulates_pathway])
    g.add((has_upregulated_pathway, OWL.propertyChainAxiom, chain1))

    # S2: hasMutation o downregulatesPathway → hasDownregulatedPathway
    chain2 = BNode()
    Collection(g, chain2, [has_mutation, downregulates_pathway])
    g.add((has_downregulated_pathway, OWL.propertyChainAxiom, chain2))

    # S2b: hasMutation o normallyRegulatesPathway → hasNormallyRegulatedPathway
    chain2b = BNode()
    Collection(g, chain2b, [has_mutation, normally_regulates_pathway])
    g.add((has_normally_regulated_pathway, OWL.propertyChainAxiom, chain2b))

    # S3/S4: hasMutation o isGoFMutationOf → hasGoF
    # Patient -hasMutation-> Mutation -isGoFMutationOf-> Gene = Patient hasGoF Gene
    chain3 = BNode()
    Collection(g, chain3, [has_mutation, is_gof_mutation_of])
    g.add((has_gof, OWL.propertyChainAxiom, chain3))

    # S3/S5: hasMutation o isLoFMutationOf → hasLoF
    # Patient -hasMutation-> Mutation -isLoFMutationOf-> Gene = Patient hasLoF Gene
    chain4 = BNode()
    Collection(g, chain4, [has_mutation, is_lof_mutation_of])
    g.add((has_lof, OWL.propertyChainAxiom, chain4))

    # ── Classes ────────────────────────────────────────────────────────────
    # (gene_class, mutation_class, pathway_class, patient_class, mutation_effect_class
    #  were already created above for domain/range references)
    print("Defining classes...")

    g.add((gene_class, RDF.type, OWL.Class))
    g.add((mutation_class, RDF.type, OWL.Class))
    g.add((pathway_class, RDF.type, OWL.Class))
    g.add((patient_class, RDF.type, OWL.Class))
    g.add((mutation_effect_class, RDF.type, OWL.Class))
    g.add((mutation_effect_class, RDFS.subClassOf, mutation_class))

    breast_cancer_subtype = GENE_NS.BreastCancerSubType
    g.add((breast_cancer_subtype, RDF.type, OWL.Class))

    # ── Gene Classes + Punning (OWL2: each gene is both a class and an individual) ──
    print("Defining gene classes with OWL2 punning...")
    core_genes = ['BRCA1', 'BRCA2', 'ER', 'PR', 'Ki-67', 'TP53']

    all_gene_names = list(core_genes)

    for gene_name in core_genes:
        gene_uri = BASE[gene_name]
        g.add((gene_uri, RDF.type, OWL.Class))
        g.add((gene_uri, RDFS.subClassOf, gene_class))
        # OWL2 punning: also declare as individual
        g.add((gene_uri, RDF.type, OWL.NamedIndividual))
        g.add((gene_uri, RDF.type, gene_class))    # individual is-a Gene
        g.add((gene_uri, RDF.type, gene_uri))       # individual is-a itself (for someValuesFrom matching)

    # ERBB2 (HER2) — single class for both names
    erbb2_uri = BASE['ERBB2']
    g.add((erbb2_uri, RDF.type, OWL.Class))
    g.add((erbb2_uri, RDFS.subClassOf, gene_class))
    g.add((erbb2_uri, RDFS.label, Literal("ERBB2 (HER2)")))
    g.add((erbb2_uri, RDF.type, OWL.NamedIndividual))
    g.add((erbb2_uri, RDF.type, gene_class))
    g.add((erbb2_uri, RDF.type, erbb2_uri))
    all_gene_names.append('ERBB2')

    # Genes from CSV data
    unique_genes = df['Gene'].unique()
    for gene_symbol in unique_genes:
        if gene_symbol not in all_gene_names:
            gene_uri = BASE[gene_symbol]
            g.add((gene_uri, RDF.type, OWL.Class))
            g.add((gene_uri, RDFS.subClassOf, gene_class))
            g.add((gene_uri, RDF.type, OWL.NamedIndividual))
            g.add((gene_uri, RDF.type, gene_class))
            g.add((gene_uri, RDF.type, gene_uri))
            all_gene_names.append(gene_symbol)

    # ── Pathway Classes ────────────────────────────────────────────────────
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

    # Close the pathway universe for negation reasoning (OWA → CWA)
    pathway_category = BASE['PathwayCategory']
    g.add((pathway_category, RDF.type, OWL.Class))
    g.add((pathway_category, RDFS.subClassOf, pathway_class))

    # PathwayCategory ≡ (ER-related OR PR-related OR HER2-related OR Ki-67-related)
    pathway_union = owl_union(g, [er_related, pr_related, her2_related, ki67_related])
    g.add((pathway_category, OWL.equivalentClass, pathway_union))

    # Set range of hasUpregulatedPathway to close the pathway universe
    # This enables HermiT to reason about negation (e.g., NOT Ki-67 upregulated)
    g.add((has_upregulated_pathway, RDFS.range, pathway_category))

    # Add closure axiom: Patient can ONLY have upregulated pathways from PathwayCategory
    # This universal restriction enables negation-as-failure reasoning
    print("Adding Patient closure axiom for negation reasoning...")
    patient_closure = BNode()
    g.add((patient_closure, RDF.type, OWL.Restriction))
    g.add((patient_closure, OWL.onProperty, has_upregulated_pathway))
    g.add((patient_closure, OWL.allValuesFrom, pathway_category))
    g.add((patient_class, RDFS.subClassOf, patient_closure))

    # DNA repair pathway (for BRCA1/BRCA2 mutations)
    dna_repair_pathway = BASE['DNA_Repair_Pathway']
    g.add((dna_repair_pathway, RDF.type, OWL.Class))
    g.add((dna_repair_pathway, RDFS.subClassOf, pathway_class))

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
        # Make it an INDIVIDUAL, not a class
        g.add((pathway_uri, RDF.type, OWL.NamedIndividual))
        # Type it as a Pathway instance
        g.add((pathway_uri, RDF.type, pathway_class))
        # Type it into the parent pathway category class (ER/HER2/PR/Ki67/etc.)
        g.add((pathway_uri, RDF.type, parent_class))
        g.add((pathway_uri, RDFS.label, Literal(pathway_name)))

    # Additional pathways for reasoning demo
    # TP53 LoF → uncontrolled proliferation (Ki-67 high) — biologically accurate
    tp53_proliferation = BASE['Cell_Proliferation_due_to_TP53_Loss']
    g.add((tp53_proliferation, RDF.type, OWL.NamedIndividual))
    g.add((tp53_proliferation, RDF.type, pathway_class))
    g.add((tp53_proliferation, RDF.type, ki67_related))  # <- critical typing
    g.add((tp53_proliferation, RDFS.label, Literal("Cell Proliferation due to TP53 Loss")))

    # BRCA1/BRCA2 LoF → defective homologous recombination
    brca_hr_pathway = BASE['Defective_Homologous_Recombination_Repair']
    g.add((brca_hr_pathway, RDF.type, OWL.NamedIndividual))
    g.add((brca_hr_pathway, RDF.type, pathway_class))
    g.add((brca_hr_pathway, RDF.type, dna_repair_pathway))
    g.add((brca_hr_pathway, RDFS.label, Literal("Defective Homologous Recombination Repair")))

    # ── Breast Cancer Subtypes ─────────────────────────────────────────────
    print("Defining breast cancer subtypes...")
    subtypes = ['Basal', 'Her2', 'LumA', 'LumB', 'Normal']
    for subtype in subtypes:
        subtype_uri = BASE[subtype]
        g.add((subtype_uri, RDF.type, OWL.Class))
        g.add((subtype_uri, RDFS.subClassOf, breast_cancer_subtype))

    # ── Mutation Effect Individuals ────────────────────────────────────────
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

    # ── Mutation Instances from CSV ────────────────────────────────────────
    print("Creating mutation instances from CSV data...")
    for idx, row in df.iterrows():
        gene_symbol = str(row['Gene'])
        mutation = str(row['Mutation'])
        pathway_name = str(row['Pathway'])
        effect = str(row['Effect'])

        mutation_id = f"{gene_symbol}_{clean_uri_string(mutation)}"
        mutation_uri = BASE[mutation_id]
        g.add((mutation_uri, RDF.type, OWL.NamedIndividual))
        g.add((mutation_uri, RDF.type, mutation_class))
        g.add((mutation_uri, RDFS.label, Literal(f"{gene_symbol} {mutation}")))

        gene_uri = BASE[gene_symbol]
        pathway_uri = BASE[clean_uri_string(pathway_name)]

        if 'gain_of_function' in effect.lower():
            # Gene -hasGoFMutation-> Mutation (HermiT infers inverse: Mutation -isGoFMutationOf-> Gene)
            g.add((gene_uri, has_gof_mutation, mutation_uri))
            g.add((mutation_uri, upregulates_pathway, pathway_uri))
            g.add((mutation_uri, has_effect, gof))
        if 'loss_of_function' in effect.lower():
            # Gene -hasLoFMutation-> Mutation (HermiT infers inverse: Mutation -isLoFMutationOf-> Gene)
            g.add((gene_uri, has_lof_mutation, mutation_uri))
            g.add((mutation_uri, downregulates_pathway, pathway_uri))
            if 'partial' in effect.lower():
                g.add((mutation_uri, has_effect, partial_lof))
            g.add((mutation_uri, has_effect, lof))

    # ── Additional Mutations for Reasoning Demo ────────────────────────────
    print("Adding additional mutations for reasoning demo...")

    # TP53 LoF also drives proliferation (Ki-67 upregulation)
    # Biologically: TP53 loss removes cell cycle checkpoints → increased proliferation
    tp53_mut = BASE['TP53_p.R342P']
    g.add((tp53_mut, upregulates_pathway, tp53_proliferation))

    # BRCA1 p.C61G — well-known pathogenic BRCA1 germline variant (LoF)
    brca1_mut = BASE['BRCA1_p.C61G']
    g.add((brca1_mut, RDF.type, OWL.NamedIndividual))
    g.add((brca1_mut, RDF.type, mutation_class))
    g.add((brca1_mut, RDFS.label, Literal("BRCA1 p.C61G")))
    g.add((brca1_mut, has_effect, lof))
    g.add((brca1_mut, downregulates_pathway, brca_hr_pathway))
    g.add((BASE['BRCA1'], has_lof_mutation, brca1_mut))

    # BRCA2 p.Y3308* — known pathogenic BRCA2 truncating variant (LoF)
    brca2_mut = BASE['BRCA2_p.Y3308Ter']
    g.add((brca2_mut, RDF.type, OWL.NamedIndividual))
    g.add((brca2_mut, RDF.type, mutation_class))
    g.add((brca2_mut, RDFS.label, Literal("BRCA2 p.Y3308*")))
    g.add((brca2_mut, has_effect, lof))
    g.add((brca2_mut, downregulates_pathway, brca_hr_pathway))
    g.add((BASE['BRCA2'], has_lof_mutation, brca2_mut))

    # ── Normal Regulation Assertions (Closed World Assumption) ─────────────
    print("Adding normal regulation assertions for unaffected pathways...")

    # Collect all pathway individuals (typed as instances of pathway_class)
    all_pathways = set()
    for pathway_name in pathway_to_parent.keys():
        all_pathways.add(BASE[clean_uri_string(pathway_name)])
    all_pathways.add(tp53_proliferation)
    all_pathways.add(brca_hr_pathway)

    # For each mutation, find which pathways it affects and assert normal regulation for others
    for mutation_uri in g.subjects(RDF.type, mutation_class):
        if isinstance(mutation_uri, BNode):
            continue  # Skip blank nodes

        # Find pathways this mutation affects (upregulates or downregulates)
        affected_pathways = set()
        for pathway in g.objects(mutation_uri, upregulates_pathway):
            affected_pathways.add(pathway)
        for pathway in g.objects(mutation_uri, downregulates_pathway):
            affected_pathways.add(pathway)

        # Assert normallyRegulates for all unaffected pathways
        for pathway_uri in all_pathways:
            if pathway_uri not in affected_pathways:
                g.add((mutation_uri, normally_regulates_pathway, pathway_uri))

    # ── Equivalent Class Axioms for Breast Cancer Subtypes ─────────────────
    print("Adding equivalent class axioms for subtype classification...")
    add_subtype_definitions(g, patient_class,
                            has_lof, has_gof, has_upregulated_pathway, has_normally_regulated_pathway,
                            er_related, her2_related, pr_related, ki67_related)

    # ── AllDisjointClasses for Subtypes ────────────────────────────────────
    # REMOVED: Disjoint classes declaration causes unsatisfiability with positive-only
    # definitions that have overlapping criteria (e.g., ER+/HER2+ satisfies both Her2 and LumB).
    # Patients may now satisfy multiple subtype definitions based on their mutation profile.
    print("Skipping AllDisjointClasses axiom (using overlapping positive definitions)...")

    # ── Sample Patient Individuals for Demo ────────────────────────────────
    print("Adding sample patient individuals...")
    add_sample_patients(g, patient_class, mutation_class,
                        has_mutation, has_effect, lof, gof)

    # ── Serialize ──────────────────────────────────────────────────────────
    print(f"\nSerializing ontology to {output_ttl}...")
    g.serialize(destination=output_ttl, format='turtle')

    print(f"\nOntology Statistics:")
    print(f"  Total triples: {len(g)}")
    print(f"  Unique genes from CSV: {len(df['Gene'].unique())}")
    print(f"  Unique pathways from CSV: {len(df['Pathway'].unique())}")
    print(f"\nOntology file created successfully: {output_ttl}")


def add_subtype_definitions(g, patient_class,
                            has_lof, has_gof, has_upregulated_pathway, has_normally_regulated_pathway,
                            er_related, her2_related, pr_related, ki67_related):
    """
    Add OWL equivalent class axioms for breast cancer subtypes.
    Uses positive-only criteria by combining upregulation and normal regulation assertions.
    Implements Closed World Assumption pattern - negation expressed as explicit normal regulation.

    Subtype definitions (based on PAM50 molecular classification):

    Basal-like: Patient AND hasLoF(BRCA1) AND hasLoF(TP53) AND Ki-67↑ AND ER-normal AND HER2-normal AND PR-normal
    HER2-enriched: Patient AND HER2↑ AND ((ER-normal AND PR-normal AND Ki-67↑) OR (Ki-67-normal AND ER↑))
    Luminal A: Patient AND ER↑ AND PR↑ AND Ki-67-normal
    Luminal B: Patient AND ER↑ AND ((HER2-normal AND PR-normal AND Ki-67↑) OR HER2↑)
    """

    # ── Basal ──────────────────────────────────────────────────────────────
    # Patient AND (hasLoF some BRCA1)
    #        AND (hasLoF some TP53)
    #        AND (hasUpregulatedPathway some Ki-67)
    #        AND (hasNormallyRegulatedPathway some ER)
    #        AND (hasNormallyRegulatedPathway some HER2)
    #        AND (hasNormallyRegulatedPathway some PR)
    basal_def = owl_intersection(g, [
        patient_class,
        owl_some(g, has_lof, BASE['BRCA1']),
        owl_some(g, has_lof, BASE['TP53']),
        owl_some(g, has_upregulated_pathway, ki67_related),
        owl_some(g, has_normally_regulated_pathway, er_related),
        owl_some(g, has_normally_regulated_pathway, her2_related),
        owl_some(g, has_normally_regulated_pathway, pr_related),
    ])
    g.add((BASE['Basal'], OWL.equivalentClass, basal_def))

    # ── Her2 ───────────────────────────────────────────────────────────────
    # Patient AND HER2↑
    #        AND ((ER-normal AND PR-normal AND Ki-67↑)      ← classic HER2-enriched
    #             OR (Ki-67-normal AND ER↑))                ← HER2+/luminal crossover
    her2_def = owl_intersection(g, [
        patient_class,
        owl_some(g, has_upregulated_pathway, her2_related),
        owl_union(g, [
            # Branch 1: ER-normal, PR-normal, Ki-67↑ (classic HER2-enriched)
            owl_intersection(g, [
                owl_some(g, has_normally_regulated_pathway, er_related),
                owl_some(g, has_normally_regulated_pathway, pr_related),
                owl_some(g, has_upregulated_pathway, ki67_related),
            ]),
            # Branch 2: Ki-67-normal, ER↑ (HER2+/luminal crossover)
            owl_intersection(g, [
                owl_some(g, has_normally_regulated_pathway, ki67_related),
                owl_some(g, has_upregulated_pathway, er_related),
            ]),
        ]),
    ])
    g.add((BASE['Her2'], OWL.equivalentClass, her2_def))

    # ── LumA ───────────────────────────────────────────────────────────────
    # Patient AND ER↑ AND PR↑ AND Ki-67-normal
    # (ER+, PR+, Ki-67 low — good prognosis luminal)
    luma_def = owl_intersection(g, [
        patient_class,
        owl_some(g, has_upregulated_pathway, er_related),
        owl_some(g, has_upregulated_pathway, pr_related),
        owl_some(g, has_normally_regulated_pathway, ki67_related),
    ])
    g.add((BASE['LumA'], OWL.equivalentClass, luma_def))

    # ── LumB ───────────────────────────────────────────────────────────────
    # Patient AND ER↑
    #        AND ((HER2-normal AND PR-normal AND Ki-67↑)   ← LumB HER2-negative
    #             OR HER2↑)                                ← LumB HER2-positive
    lumb_def = owl_intersection(g, [
        patient_class,
        owl_some(g, has_upregulated_pathway, er_related),
        owl_union(g, [
            # Branch 1: HER2-normal, PR-normal, Ki-67↑ (LumB HER2-negative)
            owl_intersection(g, [
                owl_some(g, has_normally_regulated_pathway, her2_related),
                owl_some(g, has_normally_regulated_pathway, pr_related),
                owl_some(g, has_upregulated_pathway, ki67_related),
            ]),
            # Branch 2: HER2↑ (LumB HER2-positive)
            owl_some(g, has_upregulated_pathway, her2_related),
        ]),
    ])
    g.add((BASE['LumB'], OWL.equivalentClass, lumb_def))

    # ── Normal ─────────────────────────────────────────────────────────────
    # Patient AND NOT(Basal OR Her2 OR LumA OR LumB) — catch-all for patients
    # who don't match the molecular subtype criteria
    normal_def = owl_intersection(g, [
        patient_class,
        owl_complement(g, owl_union(g, [
            BASE['Basal'], BASE['Her2'], BASE['LumA'], BASE['LumB'],
        ])),
    ])
    g.add((BASE['Normal'], OWL.equivalentClass, normal_def))


def add_sample_patients(g, patient_class, mutation_class,
                        has_mutation, has_effect, lof, gof):
    """
    Add sample patient individuals for testing the reasoning chain.
    Each patient has specific mutations; HermiT should infer:
      1. hasUpregulatedPathway / hasDownregulatedPathway (via property chains)
      2. hasLoF / hasGoF (via property chains with inverse properties)
      3. Breast cancer subtype classification (via equivalent class axioms)
    """

    # ── Patient_Basal_Demo ─────────────────────────────────────────────────
    # Expected classification: Basal-like
    # Mutations: BRCA1 p.C61G (LoF) + TP53 p.R342P (LoF → also upregulates Ki-67)
    # Pathway result: Ki-67 upregulated, no ER/HER2/PR upregulation
    pt_basal = BASE['Patient_Basal_Demo']
    g.add((pt_basal, RDF.type, OWL.NamedIndividual))
    g.add((pt_basal, RDF.type, patient_class))
    g.add((pt_basal, RDFS.label, Literal("Demo Patient - Expected Basal")))
    g.add((pt_basal, has_mutation, BASE['BRCA1_p.C61G']))
    g.add((pt_basal, has_mutation, BASE['TP53_p.R342P']))

    # ── Patient_Her2_Demo ──────────────────────────────────────────────────
    # Expected classification: HER2-enriched
    # Mutations: ERBB2 p.V777L (GoF → upregulates HER2-related pathway)
    pt_her2 = BASE['Patient_Her2_Demo']
    g.add((pt_her2, RDF.type, OWL.NamedIndividual))
    g.add((pt_her2, RDF.type, patient_class))
    g.add((pt_her2, RDFS.label, Literal("Demo Patient - Expected Her2")))
    g.add((pt_her2, has_mutation, BASE['ERBB2_p.V777L']))

    # ── Patient_LumA_Demo ──────────────────────────────────────────────────
    # Expected classification: Luminal A
    # Mutations: PIK3CA p.H1047R (GoF → upregulates ER-related pathway)
    pt_luma = BASE['Patient_LumA_Demo']
    g.add((pt_luma, RDF.type, OWL.NamedIndividual))
    g.add((pt_luma, RDF.type, patient_class))
    g.add((pt_luma, RDFS.label, Literal("Demo Patient - Expected LumA")))
    g.add((pt_luma, has_mutation, BASE['PIK3CA_p.H1047R']))

    # ── Patient_LumB_Demo ──────────────────────────────────────────────────
    # Expected classification: Luminal B
    # Mutations: PIK3CA p.E545K (GoF → ER pathway) + ERBB2 p.S310F (GoF → HER2 pathway)
    pt_lumb = BASE['Patient_LumB_Demo']
    g.add((pt_lumb, RDF.type, OWL.NamedIndividual))
    g.add((pt_lumb, RDF.type, patient_class))
    g.add((pt_lumb, RDFS.label, Literal("Demo Patient - Expected LumB")))
    g.add((pt_lumb, has_mutation, BASE['PIK3CA_p.E545K']))
    g.add((pt_lumb, has_mutation, BASE['ERBB2_p.S310F']))

    # ── Patient_Normal_Demo ────────────────────────────────────────────────
    # Expected classification: Normal-like
    # Mutations: PTEN p.R130Q (LoF → downregulates ER pathway, but does NOT upregulate any)
    pt_normal = BASE['Patient_Normal_Demo']
    g.add((pt_normal, RDF.type, OWL.NamedIndividual))
    g.add((pt_normal, RDF.type, patient_class))
    g.add((pt_normal, RDFS.label, Literal("Demo Patient - Expected Normal")))
    g.add((pt_normal, has_mutation, BASE['PTEN_p.R130Q']))


if __name__ == "__main__":
    INPUT_CSV = "./results/final_mutations_with_pathways.csv"
    OUTPUT_TTL = "./results/BIME550BRCA_update.ttl"

    create_ontology(INPUT_CSV, OUTPUT_TTL)
