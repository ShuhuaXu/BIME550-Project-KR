# TCGA Patient Testing Workflow

This guide explains how to test the ontology reasoner with real TCGA BRCA patients.

## Overview

The workflow:
1. **Extract** real patient mutation profiles from TCGA BRCA cohort
2. **Add** patients to the ontology with explicit `hasMutation` and `notHasMutation` assertions
3. **Reason** using HermiT in Protégé to infer breast cancer subtypes
4. **Evaluate** precision by comparing inferred subtypes with expected biological patterns

## Files Created

### Scripts
- **`add_tcga_patients.py`** - Extracts TCGA patients and adds them to ontology
- **`evaluate_reasoner_precision.ipynb`** - Jupyter notebook for comprehensive analysis

### Generated Files
- **`results/BIME550BRCA_with_TCGA_patients.ttl`** - Ontology with TCGA patients added
- **`results/TCGA_patient_summary.csv`** - Summary of all patients and their mutations
- **`results/mutation_subtype_analysis.csv`** - Mutation-subtype association analysis
- **`results/TCGA_patient_final_summary.csv`** - Final results with inferred subtypes

## Step-by-Step Instructions

### Step 1: Generate Base Ontology (if not done already)

```bash
python generate_ontology.py
```

This creates `results/BIME550BRCA_update.ttl` from the mutation CSV data.

### Step 2: Add TCGA Patients

```bash
python add_tcga_patients.py
```

**What it does:**
- Loads TCGA BRCA mutation data (299 exact matches from `DataExplore.ipynb`)
- Selects ~50 representative patients covering diverse mutation profiles
- Adds each patient to the ontology with:
  - `hasMutation` assertions for their mutations
  - `notHasMutation` assertions for ALL other mutations (enables OWA reasoning)
- Saves to `results/BIME550BRCA_with_TCGA_patients.ttl`

**Configuration:**
Edit `add_tcga_patients.py` to adjust:
- `n_per_mutation=2` - Number of patients per unique mutation
- `max_total=50` - Maximum total patients

### Step 3: Run Reasoner in Protégé

1. **Open Protégé**
   ```bash
   open -a Protégé results/BIME550BRCA_with_TCGA_patients.ttl
   ```

2. **Start HermiT Reasoner**
   - Menu: `Reasoner` → `HermiT`
   - Wait for reasoning to complete (may take 1-2 minutes)

3. **Inspect Inferred Types**
   - Select any `TCGA_Patient_*` individual in the class hierarchy
   - View the "Types" section in the individual description
   - You should see inferred subtype classes (Basal, Her2, LumA, LumB, Normal)

4. **Export Inferred Axioms** (for evaluation notebook)
   - Menu: `File` → `Export inferred axioms as ontology...`
   - Save as: `results/BIME550BRCA_with_TCGA_patients_inferred.ttl`

### Step 4: Evaluate Reasoner Precision

```bash
jupyter notebook evaluate_reasoner_precision.ipynb
```

**What the notebook does:**
1. Loads the inferred ontology
2. Extracts reasoner-inferred subtypes for each patient
3. Validates against expected biological patterns:
   - BRCA1/2 mutations → Basal subtype
   - ERBB2 mutations → Her2 or LumB subtype
   - PIK3CA mutations → LumA or LumB subtype
   - TP53 mutations → Basal or Her2 subtype
4. Generates visualizations and statistics
5. Calculates pattern match rate as a precision metric

### Step 5: Review Results

#### Key Metrics to Check:

1. **Subtype Distribution**
   - How many patients fall into each subtype?
   - Are the proportions biologically reasonable?
   - Expected TCGA BRCA distribution: ~15% Basal, ~15% Her2, ~50% LumA, ~20% LumB

2. **Pattern Match Rate**
   - What percentage of patients match expected mutation-subtype patterns?
   - High match rate (>80%) indicates good precision
   - Lower rate may indicate:
     - Patients with mixed characteristics
     - Need for more refined ontology definitions
     - Presence of rare/atypical cases

3. **Multi-Subtype Patients**
   - How many patients are inferred to belong to multiple subtypes?
   - This can indicate:
     - Overlapping molecular features (biologically valid)
     - Need for more specific subtype definitions

## Expected Biological Patterns

Based on well-established breast cancer biology:

| Mutation Pattern | Expected Subtype | Biological Rationale |
|-----------------|------------------|---------------------|
| BRCA1/2 loss | Basal | DNA repair deficiency, triple-negative |
| ERBB2 gain | Her2 or LumB | HER2 amplification/activation |
| PIK3CA gain + ER-normal | LumA | PI3K/AKT pathway activation, ER+ |
| PIK3CA + ERBB2 | LumB | ER+/HER2+ |
| TP53 loss + BRCA loss | Basal | High-grade, triple-negative |
| TP53 loss + ERBB2 gain | Her2 | High-grade, HER2+ |
| No pathway mutations | Normal | Normal-like or insufficient data |

## Troubleshooting

### Issue: "No mutations found in ontology"
**Solution:** Make sure `generate_ontology.py` was run first and includes all mutations from the CSV.

### Issue: "Reasoner takes too long"
**Solution:**
- Reduce number of patients in `add_tcga_patients.py` (set `max_total=20`)
- Use a faster reasoner like ELK (but it may not support all OWL features)

### Issue: "All patients inferred as 'Unknown'"
**Solution:**
- Check that notHasMutation assertions were added correctly
- Verify Normal class definitions in the ontology
- Ensure reasoner completed successfully

### Issue: "Pattern match rate is low"
**Possible causes:**
1. Patients have incomplete mutation data (only mutations mapped to Reactome pathways)
2. Mixed/atypical tumor subtypes (biologically valid)
3. Ontology definitions need refinement

## Advanced: Clinical Validation

For a more rigorous evaluation, compare inferred subtypes with clinical PAM50 subtypes:

1. **Download TCGA Clinical Data:**
   - GDC Data Portal: https://portal.gdc.cancer.gov/
   - UCSC Xena: https://xenabrowser.net/
   - Look for PAM50 or RNA-seq-based subtype annotations

2. **Add to evaluation notebook:**
   ```python
   clinical_data = pd.read_csv('path/to/clinical_data.tsv', sep='\t')
   # Merge with patient_summary on patient_id
   # Calculate accuracy, precision, recall for each subtype
   ```

3. **Generate confusion matrix:**
   ```python
   from sklearn.metrics import confusion_matrix, classification_report
   cm = confusion_matrix(y_true=clinical_subtypes, y_pred=inferred_subtypes)
   ```

## Interpreting Results

### Good Precision Indicators:
- ✅ Pattern match rate > 80%
- ✅ Subtype distribution similar to TCGA expected
- ✅ Few "Unknown" classifications
- ✅ Multi-subtype patients have biologically plausible mutation combinations

### Areas for Improvement:
- ⚠️ High "Unknown" rate → Need more pathway coverage or better Normal class definition
- ⚠️ Low pattern match rate → Refine subtype equivalent class axioms
- ⚠️ Unexpected subtype distribution → Check mutation-pathway mappings

## Next Steps

1. **Refine ontology based on results:**
   - Add more pathway rules
   - Refine subtype definitions
   - Add intermediate classes (e.g., ER-positive, HER2-positive)

2. **Expand testing:**
   - Include more patients
   - Test with other cancer types
   - Validate against multi-omic data (CNV, methylation)

3. **Publication:**
   - Document precision metrics
   - Compare with machine learning approaches
   - Highlight advantages of explainable reasoning

## References

- TCGA BRCA: https://www.cancer.gov/tcga
- PAM50 Classification: Parker et al. (2009) JCO
- Reactome Pathways: https://reactome.org/
- HermiT Reasoner: http://www.hermit-reasoner.com/
