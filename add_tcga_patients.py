"""
Add TCGA BRCA Real Patient Examples to Ontology
This script extracts real patient mutation profiles from TCGA BRCA cohort
and adds them to the ontology for precision testing of the reasoner.
"""

import pandas as pd
import re
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from collections import defaultdict

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


def load_tcga_patient_data(reactome_path, tcga_brca_path):
    """
    Load and merge TCGA BRCA mutation data with Reactome pathways.
    Returns a DataFrame with patient mutations mapped to pathways.
    """
    print("Loading Reactome pathway mapping...")
    map_df = pd.read_csv(reactome_path, sep="\t", dtype=str)

    # Filter for breast cancer
    map_df = map_df[map_df["disease"].str.contains("breast cancer", case=False, na=False)]

    # Extract protein mutation from displayName
    def extract_protein_change_short(display_name: str) -> str:
        if pd.isna(display_name):
            return None
        s = str(display_name)
        m = re.search(r"^[A-Za-z0-9_-]+\s+([^\s\[]+)", s)
        if not m:
            return None
        mut = m.group(1).strip()
        return f"p.{mut}"

    map_df["HGVSp_Short_like"] = map_df["displayName"].apply(extract_protein_change_short)
    map_df = map_df.dropna(subset=["Genename", "HGVSp_Short_like"])
    map_df = map_df.drop_duplicates(subset=["Genename", "HGVSp_Short_like"])

    print("Loading TCGA BRCA mutation data...")
    maf = pd.read_csv(tcga_brca_path, comment="#", low_memory=False, dtype=str)

    # Merge with pathway mapping
    merged = maf.merge(
        map_df,
        right_on=["Genename", "HGVSp_Short_like"],
        left_on=["Hugo_Symbol", "HGVSp_Short"],
        how="inner",
    )

    print(f"Found {merged.shape[0]} exact mutation-pathway matches")
    return merged


def select_representative_patients(merged_df, n_per_mutation=1, max_total=50):
    """
    Select representative patients that cover diverse mutation profiles.

    Strategy:
    - For each unique mutation, select n_per_mutation patients
    - Prioritize patients with multiple mutations (more informative)
    - Cap at max_total patients to keep ontology manageable
    """
    # Count mutations per patient
    patient_mutation_counts = merged_df.groupby('Tumor_Sample_Barcode').size()

    # Get unique mutations
    unique_mutations = merged_df[['Genename', 'HGVSp_Short']].drop_duplicates()

    selected_patients = set()

    # First pass: select patients with multiple mutations
    multi_mutation_patients = patient_mutation_counts[patient_mutation_counts >= 2].index.tolist()
    for patient in multi_mutation_patients[:max_total // 2]:
        selected_patients.add(patient)

    # Second pass: ensure coverage of all mutations
    for _, row in unique_mutations.iterrows():
        gene = row['Genename']
        mutation = row['HGVSp_Short']

        # Find patients with this mutation
        patients_with_mutation = merged_df[
            (merged_df['Genename'] == gene) &
            (merged_df['HGVSp_Short'] == mutation)
        ]['Tumor_Sample_Barcode'].unique()

        # Add up to n_per_mutation patients
        for patient in patients_with_mutation[:n_per_mutation]:
            if len(selected_patients) < max_total:
                selected_patients.add(patient)

    print(f"Selected {len(selected_patients)} representative patients")
    return list(selected_patients)


def extract_patient_profiles(merged_df, selected_patients):
    """
    Extract mutation profiles for selected patients.
    Returns dict: {patient_id: [(gene, mutation, pathway, effect), ...]}
    """
    profiles = defaultdict(list)

    for patient in selected_patients:
        patient_data = merged_df[merged_df['Tumor_Sample_Barcode'] == patient]

        for _, row in patient_data.iterrows():
            gene = row['Genename']
            mutation = row['HGVSp_Short']
            pathway = row['entityWithAccessionedSequence_pathway_displayName']
            effect = row['entityWithAccessionedSequence_reactionLikeEvent_entityFunctionalStatus_functionalStatus_functionalStatusType_displayName']

            profiles[patient].append((gene, mutation, pathway, effect))

    return profiles


def add_patients_to_ontology(base_ontology_path, patient_profiles, output_path):
    """
    Load base ontology and add TCGA patient instances.
    """
    print(f"Loading base ontology from {base_ontology_path}...")
    g = Graph()
    g.parse(base_ontology_path, format='turtle')

    # Get key properties and classes
    has_mutation = BASE.hasMutation
    not_has_mutation = BASE.notHasMutation
    mutation_class = BASE.Mutation  # Fixed: was GENE_NS.Mutation
    patient_class = BASE.Patient

    # Collect all mutation individuals from the ontology
    all_mutations = set()
    for mutation_uri in g.subjects(RDF.type, mutation_class):
        if (mutation_uri, RDF.type, OWL.NamedIndividual) in g:
            all_mutations.add(mutation_uri)

    # Add the Others individual
    all_mutations.add(BASE['Others'])

    print(f"Found {len(all_mutations)} mutations in base ontology")

    # Add each TCGA patient
    print(f"Adding {len(patient_profiles)} TCGA patients to ontology...")
    for patient_id, mutations in patient_profiles.items():
        # Create safe patient URI (remove special characters)
        safe_patient_id = clean_uri_string(patient_id)
        patient_uri = BASE[f'TCGA_Patient_{safe_patient_id}']

        # Add patient as individual
        g.add((patient_uri, RDF.type, OWL.NamedIndividual))
        g.add((patient_uri, RDF.type, patient_class))
        g.add((patient_uri, RDFS.label, Literal(f"TCGA Patient {patient_id}")))

        # Collect patient's mutations
        patient_mutations = set()
        for gene, mutation, pathway, effect in mutations:
            # Create mutation URI (matches generate_ontology.py pattern)
            mutation_id = f"{gene}_{clean_uri_string(mutation)}"
            mutation_uri = BASE[mutation_id]

            # Check if mutation exists in ontology
            if mutation_uri in all_mutations:
                patient_mutations.add(mutation_uri)
                g.add((patient_uri, has_mutation, mutation_uri))

        # Add explicit notHasMutation for all other mutations
        for mutation_uri in all_mutations:
            if mutation_uri not in patient_mutations:
                g.add((patient_uri, not_has_mutation, mutation_uri))

        print(f"  Added patient {safe_patient_id} with {len(patient_mutations)} mutations")

    # Serialize updated ontology
    print(f"Saving ontology with TCGA patients to {output_path}...")
    g.serialize(destination=output_path, format='turtle')

    print(f"\nOntology Statistics:")
    print(f"  Total triples: {len(g)}")
    print(f"  TCGA patients added: {len(patient_profiles)}")


def generate_patient_summary_report(patient_profiles, output_csv):
    """
    Generate a summary CSV of all patients for easy reference.
    """
    rows = []
    for patient_id, mutations in patient_profiles.items():
        mutation_list = "; ".join([f"{gene} {mut}" for gene, mut, _, _ in mutations])
        pathway_list = "; ".join(set([pathway for _, _, pathway, _ in mutations]))

        rows.append({
            'Patient_ID': patient_id,
            'Mutation_Count': len(mutations),
            'Mutations': mutation_list,
            'Pathways': pathway_list
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"Saved patient summary to {output_csv}")
    return df


def main():
    # Configuration
    REACTOME_PATH = "./data/disease_variant_ewas_mapping.tsv"
    TCGA_BRCA_PATH = "./results/TCGA_BRCA.csv"
    BASE_ONTOLOGY_PATH = "./results/BIME550BRCA_presentation.ttl"
    OUTPUT_ONTOLOGY_PATH = "./results/BIME550BRCA_with_TCGA_patients.ttl"
    PATIENT_SUMMARY_PATH = "./results/TCGA_patient_summary.csv"

    # Load data
    merged_df = load_tcga_patient_data(REACTOME_PATH, TCGA_BRCA_PATH)

    # Select representative patients
    # Adjust n_per_mutation and max_total to control number of patients
    selected_patients = select_representative_patients(
        merged_df,
        n_per_mutation=2,  # 2 patients per unique mutation
        max_total=50       # Cap at 50 patients total
    )

    # Extract patient mutation profiles
    patient_profiles = extract_patient_profiles(merged_df, selected_patients)

    # Generate summary report
    summary_df = generate_patient_summary_report(patient_profiles, PATIENT_SUMMARY_PATH)

    print("\nPatient Summary Statistics:")
    print(f"  Total patients: {len(patient_profiles)}")
    print(f"  Average mutations per patient: {summary_df['Mutation_Count'].mean():.2f}")
    print(f"  Median mutations per patient: {summary_df['Mutation_Count'].median():.0f}")
    print(f"  Max mutations in a patient: {summary_df['Mutation_Count'].max():.0f}")
    print(f"  Min mutations in a patient: {summary_df['Mutation_Count'].min():.0f}")

    print("\nMutation distribution:")
    print(summary_df['Mutation_Count'].value_counts().sort_index())

    # Add patients to ontology
    add_patients_to_ontology(BASE_ONTOLOGY_PATH, patient_profiles, OUTPUT_ONTOLOGY_PATH)

    print("\n" + "="*70)
    print("SUCCESS! TCGA patients added to ontology.")
    print("="*70)
    print(f"\nNext steps:")
    print(f"1. Load {OUTPUT_ONTOLOGY_PATH} in Protégé")
    print(f"2. Run HermiT reasoner")
    print(f"3. Check inferred types for TCGA_Patient_* individuals")
    print(f"4. Compare with expected subtypes from clinical data")
    print(f"5. Review {PATIENT_SUMMARY_PATH} for patient details")


if __name__ == "__main__":
    main()
