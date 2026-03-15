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


def owl_has_value(g, prop, value):
    """Create owl:Restriction with owl:hasValue"""
    r = BNode()
    g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, prop))
    g.add((r, OWL.hasValue, value))
    return r


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

    affects_pathway = BASE.affectsPathway
    g.add((affects_pathway, RDF.type, OWL.ObjectProperty))
    g.add((affects_pathway, RDFS.domain, mutation_class))
    g.add((affects_pathway, RDFS.range, pathway_class))

    downregulates_pathway = BASE.downregulatesPathway
    g.add((downregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((downregulates_pathway, RDFS.subPropertyOf, affects_pathway))
    g.add((downregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((downregulates_pathway, RDFS.domain, mutation_class))
    g.add((downregulates_pathway, RDFS.range, pathway_class))

    upregulates_pathway = BASE.upregulatesPathway
    g.add((upregulates_pathway, RDF.type, OWL.ObjectProperty))
    g.add((upregulates_pathway, RDFS.subPropertyOf, affects_pathway))
    g.add((upregulates_pathway, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((upregulates_pathway, RDFS.domain, mutation_class))
    g.add((upregulates_pathway, RDFS.range, pathway_class))

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

    has_effect = BASE.hasEffect
    g.add((has_effect, RDF.type, OWL.ObjectProperty))
    g.add((has_effect, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_effect, RDFS.domain, mutation_class))
    g.add((has_effect, RDFS.range, mutation_effect_class))

    has_mutation = BASE.hasMutation
    g.add((has_mutation, RDF.type, OWL.ObjectProperty))
    g.add((has_mutation, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((has_mutation, RDFS.domain, patient_class))

    not_has_mutation = BASE.notHasMutation
    g.add((not_has_mutation, RDF.type, OWL.ObjectProperty))
    g.add((not_has_mutation, RDFS.domain, patient_class))
    g.add((not_has_mutation, RDFS.range, mutation_class))
    g.add((has_mutation, OWL.propertyDisjointWith, not_has_mutation))

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

    # ── Normal Classes (for negation reasoning) ────────────────────────────
    print("Creating Normal classes (ER-Normal, HER2-Normal, Ki-67-Normal)...")
    create_normal_classes(g, patient_class, not_has_mutation, df)

    # ── Equivalent Class Axioms for Breast Cancer Subtypes ─────────────────
    print("Adding equivalent class axioms for subtype classification...")
    add_subtype_definitions(g, patient_class, not_has_mutation,
                            has_lof, has_gof, has_upregulated_pathway,
                            er_related, her2_related, ki67_related)

    # ── AllDisjointClasses for Subtypes ────────────────────────────────────
    # REMOVED: Disjoint classes declaration causes unsatisfiability with positive-only
    # definitions that have overlapping criteria (e.g., ER+/HER2+ satisfies both Her2 and LumB).
    # Patients may now satisfy multiple subtype definitions based on their mutation profile.
    print("Skipping AllDisjointClasses axiom (using overlapping positive definitions)...")

    # ── Sample Patient Individuals for Demo ────────────────────────────────
    print("Adding sample patient individuals...")
    add_sample_patients(g, patient_class, mutation_class,
                        has_mutation, not_has_mutation)

    # ── Serialize ──────────────────────────────────────────────────────────
    print(f"\nSerializing ontology to {output_ttl}...")
    g.serialize(destination=output_ttl, format='turtle')

    print(f"\nOntology Statistics:")
    print(f"  Total triples: {len(g)}")
    print(f"  Unique genes from CSV: {len(df['Gene'].unique())}")
    print(f"  Unique pathways from CSV: {len(df['Pathway'].unique())}")
    print(f"\nOntology file created successfully: {output_ttl}")


def create_normal_classes(g, patient_class, not_has_mutation, df):
    """
    Create ER-Normal, HER2-Normal, and Ki-67-Normal classes.
    These are defined as Patient AND (notHasMutation for all relevant pathway mutations).
    """
    # Collect mutations by pathway category
    er_mutations = set()
    her2_mutations = set()
    ki67_mutations = set()

    for _, row in df.iterrows():
        gene_symbol = str(row['Gene'])
        mutation = str(row['Mutation'])
        pathway_name = str(row['Pathway'])

        mutation_id = f"{gene_symbol}_{clean_uri_string(mutation)}"
        mutation_uri = BASE[mutation_id]

        # Categorize mutations by pathway
        if 'AKT1' in pathway_name or 'PI3K' in pathway_name or 'PTEN' in pathway_name or 'RB1' in pathway_name or 'SMAD4' in pathway_name:
            er_mutations.add(mutation_uri)
        if 'ERBB2' in pathway_name or 'HER2' in pathway_name:
            her2_mutations.add(mutation_uri)
        if 'TP53' in gene_symbol:
            ki67_mutations.add(mutation_uri)

    # Add known mutations
    er_mutations.update([
        BASE['AKT1_p.E17K'],
        BASE['PIK3CA_p.E542K'], BASE['PIK3CA_p.E545A'], BASE['PIK3CA_p.E545G'],
        BASE['PIK3CA_p.E545K'], BASE['PIK3CA_p.H1047L'], BASE['PIK3CA_p.H1047R'],
        BASE['PIK3CA_p.H1047Y'], BASE['PIK3CA_p.M1043I'], BASE['PIK3CA_p.Q546K'],
        BASE['PIK3CA_p.Q546R'],
        BASE['PTEN_p.Q149_'], BASE['PTEN_p.R130P'], BASE['PTEN_p.R130Q'],
        BASE['PTEN_p.S287_'], BASE['PTEN_p.S59_'], BASE['PTEN_p.Y88_'],
        BASE['RB1_p.A74Efs_4'], BASE['RB1_p.R455_'], BASE['RB1_p.R552_'],
        BASE['RB1_p.S215_'], BASE['RB1_p.S829_'],
        BASE['SMAD4_p.E526_'], BASE['SMAD4_p.Q245_'], BASE['SMAD4_p.Q334_'],
    ])

    her2_mutations.update([
        BASE['ERBB2_p.D769H'], BASE['ERBB2_p.D769Y'], BASE['ERBB2_p.G309A'],
        BASE['ERBB2_p.I767M'], BASE['ERBB2_p.L755M'], BASE['ERBB2_p.L755S'],
        BASE['ERBB2_p.L755W'], BASE['ERBB2_p.R678Q'], BASE['ERBB2_p.S310F'],
        BASE['ERBB2_p.V777L'], BASE['ERBB2_p.V842I'],
    ])

    ki67_mutations.add(BASE['TP53_p.R342P'])

    # ER-Normal: Patient with notHasMutation for all ER-related mutations
    er_normal_restrictions = [patient_class]
    for mut in er_mutations:
        er_normal_restrictions.append(owl_has_value(g, not_has_mutation, mut))
    er_normal_def = owl_intersection(g, er_normal_restrictions)
    g.add((BASE['ER-Normal'], RDF.type, OWL.Class))
    g.add((BASE['ER-Normal'], OWL.equivalentClass, er_normal_def))
    g.add((BASE['ER-Normal'], RDFS.subClassOf, patient_class))

    # HER2-Normal: Patient with notHasMutation for all HER2-related mutations
    her2_normal_restrictions = [patient_class]
    for mut in her2_mutations:
        her2_normal_restrictions.append(owl_has_value(g, not_has_mutation, mut))
    her2_normal_def = owl_intersection(g, her2_normal_restrictions)
    g.add((BASE['HER2-Normal'], RDF.type, OWL.Class))
    g.add((BASE['HER2-Normal'], OWL.equivalentClass, her2_normal_def))
    g.add((BASE['HER2-Normal'], RDFS.subClassOf, patient_class))

    # Ki-67-Normal: Patient with notHasMutation for all Ki-67-related mutations
    ki67_normal_restrictions = [patient_class]
    for mut in ki67_mutations:
        ki67_normal_restrictions.append(owl_has_value(g, not_has_mutation, mut))
    ki67_normal_def = owl_intersection(g, ki67_normal_restrictions)
    g.add((BASE['Ki-67-Normal'], RDF.type, OWL.Class))
    g.add((BASE['Ki-67-Normal'], OWL.equivalentClass, ki67_normal_def))
    g.add((BASE['Ki-67-Normal'], RDFS.subClassOf, patient_class))


def add_subtype_definitions(g, patient_class, not_has_mutation,
                            has_lof, has_gof, has_upregulated_pathway,
                            er_related, her2_related, ki67_related):
    """
    Add OWL equivalent class axioms for breast cancer subtypes.
    Uses the Normal classes (ER-Normal, HER2-Normal, Ki-67-Normal) for negation reasoning.

    Subtype definitions matching the presentation version:

    Basal: ER-Normal AND HER2-Normal AND Patient AND (hasLoF BRCA1 OR hasLoF BRCA2 OR hasLoF TP53 OR hasUpregulatedPathway Ki-67)
    Her2: ER-Normal AND Patient AND hasUpregulatedPathway HER2-related_pathway
    LumA: HER2-Normal AND Ki-67-Normal AND Patient AND hasUpregulatedPathway ER-related_pathway
    LumB: Patient AND hasUpregulatedPathway ER-related_pathway AND (hasUpregulatedPathway HER2-related_pathway OR hasUpregulatedPathway Ki-67-related_pathway)
    Normal: ER-Normal AND HER2-Normal AND Ki-67-Normal AND Patient AND notHasMutation BRCA1_p.C61G AND notHasMutation BRCA2_p.Y3308Ter
    """

    # ── Basal ──────────────────────────────────────────────────────────────
    # ER-Normal AND HER2-Normal AND Patient AND (hasLoF BRCA1 OR hasLoF BRCA2 OR hasLoF TP53 OR hasUpregulatedPathway Ki-67)
    basal_def = owl_intersection(g, [
        BASE['ER-Normal'],
        BASE['HER2-Normal'],
        patient_class,
        owl_union(g, [
            owl_some(g, has_lof, BASE['BRCA1']),
            owl_some(g, has_lof, BASE['BRCA2']),
            owl_some(g, has_lof, BASE['TP53']),
            owl_some(g, has_upregulated_pathway, ki67_related),
        ])
    ])
    g.add((BASE['Basal'], OWL.equivalentClass, basal_def))

    # ── Her2 ───────────────────────────────────────────────────────────────
    # ER-Normal AND Patient AND hasUpregulatedPathway HER2-related_pathway
    her2_def = owl_intersection(g, [
        BASE['ER-Normal'],
        patient_class,
        owl_some(g, has_upregulated_pathway, her2_related),
    ])
    g.add((BASE['Her2'], OWL.equivalentClass, her2_def))

    # ── LumA ───────────────────────────────────────────────────────────────
    # HER2-Normal AND Ki-67-Normal AND Patient AND hasUpregulatedPathway ER-related_pathway
    luma_def = owl_intersection(g, [
        BASE['HER2-Normal'],
        BASE['Ki-67-Normal'],
        patient_class,
        owl_some(g, has_upregulated_pathway, er_related),
    ])
    g.add((BASE['LumA'], OWL.equivalentClass, luma_def))

    # ── LumB ───────────────────────────────────────────────────────────────
    # Patient AND hasUpregulatedPathway ER-related_pathway AND (hasUpregulatedPathway HER2-related_pathway OR hasUpregulatedPathway Ki-67-related_pathway)
    lumb_def = owl_intersection(g, [
        patient_class,
        owl_some(g, has_upregulated_pathway, er_related),
        owl_union(g, [
            owl_some(g, has_upregulated_pathway, her2_related),
            owl_some(g, has_upregulated_pathway, ki67_related),
        ])
    ])
    g.add((BASE['LumB'], OWL.equivalentClass, lumb_def))

    # ── Normal ─────────────────────────────────────────────────────────────
    # ER-Normal AND HER2-Normal AND Ki-67-Normal AND Patient AND notHasMutation BRCA1_p.C61G AND notHasMutation BRCA2_p.Y3308Ter
    normal_def = owl_intersection(g, [
        BASE['ER-Normal'],
        BASE['HER2-Normal'],
        BASE['Ki-67-Normal'],
        patient_class,
        owl_has_value(g, not_has_mutation, BASE['BRCA1_p.C61G']),
        owl_has_value(g, not_has_mutation, BASE['BRCA2_p.Y3308Ter']),
    ])
    g.add((BASE['Normal'], OWL.equivalentClass, normal_def))


def add_sample_patients(g, patient_class, mutation_class,
                        has_mutation, not_has_mutation):
    """
    Add sample patient individuals for testing the reasoning chain.
    Each patient has specific mutations and explicit notHasMutation assertions for all others.
    This enables closed-world reasoning under OWA.
    HermiT should infer:
      1. hasUpregulatedPathway / hasDownregulatedPathway (via property chains)
      2. hasLoF / hasGoF (via property chains with inverse properties)
      3. Breast cancer subtype classification (via equivalent class axioms)
    """

    # Collect all mutation individuals
    all_mutations = set()
    for mutation_uri in g.subjects(RDF.type, mutation_class):
        if isinstance(mutation_uri, BNode):
            continue  # Skip blank nodes
        # Only include named individuals
        if (mutation_uri, RDF.type, OWL.NamedIndividual) in g:
            all_mutations.add(mutation_uri)

    # Add the Others individual
    all_mutations.add(BASE['Others'])

    # Helper function to add patient with explicit negative assertions
    def add_patient_with_negations(patient_uri, label, mutations_list):
        g.add((patient_uri, RDF.type, OWL.NamedIndividual))
        g.add((patient_uri, RDF.type, patient_class))
        g.add((patient_uri, RDFS.label, Literal(label)))

        # Add hasMutation for the patient's mutations
        mutations_set = set(mutations_list)
        for mut in mutations_set:
            g.add((patient_uri, has_mutation, mut))

        # Add notHasMutation for all other mutations
        for mut in all_mutations:
            if mut not in mutations_set:
                g.add((patient_uri, not_has_mutation, mut))

    # ── Patient_Basal_Demo ─────────────────────────────────────────────────
    # Expected classification: Basal-like
    # Mutations: BRCA1 p.C61G (LoF) + TP53 p.R342P (LoF → also upregulates Ki-67)
    add_patient_with_negations(
        BASE['Patient_Basal_Demo'],
        "Demo Patient - Expected Basal",
        [BASE['BRCA1_p.C61G'], BASE['TP53_p.R342P']]
    )

    # ── Patient_Her2_Demo ──────────────────────────────────────────────────
    # Expected classification: HER2-enriched
    # Mutations: ERBB2 p.V777L (GoF → upregulates HER2-related pathway)
    add_patient_with_negations(
        BASE['Patient_Her2_Demo'],
        "Demo Patient - Expected Her2",
        [BASE['ERBB2_p.V777L']]
    )

    # ── Patient_LumA_Demo ──────────────────────────────────────────────────
    # Expected classification: Luminal A
    # Mutations: PIK3CA p.H1047R (GoF → upregulates ER-related pathway)
    add_patient_with_negations(
        BASE['Patient_LumA_Demo'],
        "Demo Patient - Expected LumA",
        [BASE['PIK3CA_p.H1047R']]
    )

    # ── Patient_LumB_Demo ──────────────────────────────────────────────────
    # Expected classification: Luminal B
    # Mutations: PIK3CA p.E545K (GoF → ER pathway) + ERBB2 p.S310F (GoF → HER2 pathway)
    add_patient_with_negations(
        BASE['Patient_LumB_Demo'],
        "Demo Patient - Expected LumB",
        [BASE['PIK3CA_p.E545K'], BASE['ERBB2_p.S310F']]
    )

    # ── Patient_Normal_Demo ────────────────────────────────────────────────
    # Expected classification: Normal-like
    # No mutations - all pathways normal
    add_patient_with_negations(
        BASE['Patient_Normal_Demo'],
        "Demo Patient - Expected Normal",
        []
    )


if __name__ == "__main__":
    INPUT_CSV = "./results/final_mutations_with_pathways.csv"
    OUTPUT_TTL = "./results/BIME550BRCA_update.ttl"

    create_ontology(INPUT_CSV, OUTPUT_TTL)
