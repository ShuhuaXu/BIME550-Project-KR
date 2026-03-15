# BIME550 Breast Cancer Ontology Project

## Overview

An ontology for automated breast cancer subtype classification based on mutation profiles, using property chain reasoning and explicit negative assertions to enable classification under the Open World Assumption (OWA). The ontology classifies patients into subtypes (Luminal A, Luminal B, HER2-enriched, Basal-like, Normal-like) based on their somatic mutations in key cancer genes and affected molecular pathways.

**Key Innovation:** Uses the `notHasMutation` property with explicit negative assertions to enable definitive "normal" pathway classifications in OWA, allowing the reasoner to infer absence of pathway activation when patients lack specific mutations.

## Project Structure

```
BIME550-Project-KR/
├── generate_ontology.py          # Main ontology generation script
├── add_tcga_patients.py          # Adds real TCGA patients to ontology
├── DataExplore.ipynb            # TCGA data extraction & pathway mapping
├── evaluate_reasoner_precision.ipynb  # (Optional) Precision evaluation
├── data/
│   ├── mc3.v0.2.8.PUBLIC.maf.gz              # TCGA mutation data
│   └── disease_variant_ewas_mapping.tsv      # Reactome pathway annotations
├── results/
│   ├── final_mutations_with_pathways.csv     # Curated mutation-pathway mappings
│   ├── BIME550BRCA_presentation.ttl          # Hand-curated reference ontology
│   ├── BIME550BRCA_update.ttl                # Generated ontology (latest)
│   ├── BIME550BRCA_with_TCGA_patients.ttl    # Ontology with 50 TCGA patients
│   ├── TCGA_BRCA.csv                          # Filtered TCGA BRCA mutations
│   └── TCGA_patient_summary.csv               # Patient mutation profiles
├── TCGA_Validation_Writeup.md    # Validation results writeup
└── README_TCGA_TESTING.md        # Detailed TCGA testing guide
```

## Quick Start

### 1. Generate Base Ontology

```bash
python generate_ontology.py
```

**Generates:** `results/BIME550BRCA_update.ttl`

This script creates the complete ontology from mutation-pathway mappings, including:
- 37 mutation individuals (PIK3CA, ERBB2, TP53, BRCA1/2, PTEN, RB1, SMAD4, AKT1)
- 9 pathway classes (ER-related, HER2-related, Ki-67-related, DNA repair)
- 5 breast cancer subtype classes with equivalent class axioms
- 3 "Normal" pathway classes (ER-Normal, HER2-Normal, Ki-67-Normal)
- 4 property chain axioms for mutation effect inference
- 5 demo patient instances with explicit negative assertions

**Key Features:**
- `notHasMutation` property (disjoint with `hasMutation`)
- `affectsPathway` parent property (subsumes `upregulatesPathway`, `downregulatesPathway`)
- Normal classes defined using `hasValue` restrictions on `notHasMutation`
- Property chains: `hasMutation ∘ upregulatesPathway → hasUpregulatedPathway`

### 2. Add Real TCGA Patients

```bash
python add_tcga_patients.py
```

**Generates:** `results/BIME550BRCA_with_TCGA_patients.ttl`

Adds 50 representative TCGA BRCA patients to the ontology with:
- Comprehensive mutation profiles (1-3 mutations per patient)
- Explicit `notHasMutation` assertions for all non-present mutations
- ~2,000 total triples (92.5% are negative assertions)

### 3. Run Reasoning in Protégé

1. **Start HermiT reasoner:** Reasoner → HermiT → Start Reasoner
2. **View inferred types:** Select any `TCGA_Patient_*` individual → Types tab
3. **Reasoning time:** under 1 minute for 50 patients

**Expected Results:**
- All patients classified into 1+ subtypes
- Property chains infer `hasUpregulatedPathway`, `hasLoF`, `hasGoF`
- Normal classes inferred from negative assertions

## Ontology Design

### Class Hierarchy

```
owl:Thing
├── Patient
│   ├── Basal
│   ├── Her2
│   ├── LumA
│   ├── LumB
│   ├── Normal
│   ├── ER-Normal
│   ├── HER2-Normal
│   └── Ki-67-Normal
├── Gene
│   ├── BRCA1, BRCA2, TP53
│   ├── PIK3CA, AKT1, PTEN
│   ├── ERBB2 (HER2)
│   └── RB1, SMAD4
├── Mutation
│   └── Mutation_Effect (GoF, LoF, Partial_LoF)
└── Pathway
    ├── PathwayCategory
    │   ├── ER-related_pathway
    │   ├── HER2-related_pathway
    │   ├── Ki-67-related_pathway
    │   └── PR-related_pathway
    └── DNA_Repair_Pathway
```

### Object Properties

**Core Properties:**
- `hasMutation` / `notHasMutation` (disjoint)
- `hasLoFMutation` / `hasGoFMutation` (subproperties of `hasMutation`)
- `isLoFMutationOf` / `isGoFMutationOf` (inverse of above)

**Mutation-Pathway:**
- `affectsPathway` (parent)
  - `upregulatesPathway` (GoF mutations)
  - `downregulatesPathway` (LoF mutations)

**Patient-Pathway (inferred via property chains):**
- `hasUpregulatedPathway`
- `hasDownregulatedPathway`
- `hasLoF` / `hasGoF`

### Property Chain Axioms

```turtle
# Patient mutation → pathway activation
hasMutation ∘ upregulatesPathway → hasUpregulatedPathway
hasMutation ∘ downregulatesPathway → hasDownregulatedPathway

# Patient mutation → gene effect
hasMutation ∘ isGoFMutationOf → hasGoF
hasMutation ∘ isLoFMutationOf → hasLoF
```

### Subtype Definitions (Equivalent Classes)

**Luminal A:**
```
Patient ∧ hasUpregulatedPathway(ER-related)
        ∧ HER2-Normal ∧ Ki-67-Normal
```

**Luminal B:**
```
Patient ∧ hasUpregulatedPathway(ER-related)
        ∧ (hasUpregulatedPathway(HER2-related) ∨ hasUpregulatedPathway(Ki-67-related))
```

**HER2-enriched:**
```
Patient ∧ ER-Normal ∧ hasUpregulatedPathway(HER2-related)
```

**Basal-like:**
```
Patient ∧ ER-Normal ∧ HER2-Normal
        ∧ (hasLoF(BRCA1) ∨ hasLoF(BRCA2) ∨ hasLoF(TP53) ∨ hasUpregulatedPathway(Ki-67))
```

**Normal-like:**
```
Patient ∧ ER-Normal ∧ HER2-Normal ∧ Ki-67-Normal
        ∧ notHasMutation(BRCA1_p.C61G) ∧ notHasMutation(BRCA2_p.Y3308Ter)
```


## Key Ideas

### 1. Explicit Negative Assertions for Open World Assumption (OWA)

**Problem:** Under OWA, absence of `hasMutation(X)` ≠ `NOT hasMutation(X)`

**Solution:** Explicit `notHasMutation` property:
```turtle
:Patient_1 hasMutation :PIK3CA_p.H1047R .
:Patient_1 notHasMutation :ERBB2_p.V777L .
:Patient_1 notHasMutation :BRCA1_p.C61G .
# ... (35 more negative assertions)
```

**Enables:**
- Definitive classification into "Normal" pathway classes
- Reasoning about pathway non-activation
- Closed-world assumption pattern within OWA framework

### 2. Property Chain Reasoning

Automatic inference of patient-level phenotypes from mutations:

```
Patient → hasMutation → Mutation → upregulatesPathway → Pathway
  ↓                                                           ↓
  └────────────── hasUpregulatedPathway ──────────────────────┘
```

## Requirements

### Software
- Python 3.10+
- Protégé 5.6.4+ (with HermiT reasoner)

### Python Dependencies
```bash
pip install pandas rdflib requests
```

## License

This project is for educational purposes as part of BIME 550 coursework.

---

**Course:** BIME 550 - Knowledge Representation in Biomedical Informatics
**Institution:** University of Washington
