# Complete Pipeline Orchestration

This document describes the complete pipeline orchestration system for running all scraping and processing scripts in sequence.

## Overview

The `run_complete_pipeline.py` script orchestrates the entire data scraping and processing workflow, running 7 steps in sequence:

1. **Initial Spiders** - FAQ, Rating, Pros/Cons/Colors
2. **Variant Spiders** - Run in parallel
3. **Feature & Specification Spiders** - Run in parallel
4. **Seed Mileage** - Fill missing mileage data
5. **Process Variants** - Update variant names and metadata
6. **Variant Check** - Verify consistency between Variants.csv and specification-info.csv
7. **Sheet Creator** - Create final Excel sheet (only if variants match)

## Usage

### Basic Usage

```bash
python utils/run_complete_pipeline.py <output_folder>
```

### Example

```bash
python utils/run_complete_pipeline.py Output/Citroen/C3
```

## Pipeline Steps

### Step 1: Initial Spiders (`run_first_spiders.py`)

Runs three spiders in parallel:
- **faq** - Extracts FAQ information
- **model-rating** - Extracts rating information
- **pros_cons_colours** - Extracts pros/cons and color options

**Output Files:**
- `faq-info.csv`
- `ratingInfo.csv`
- `prosConsInfo.csv`
- `colourOptionsInfo.csv`
- `modelInfo.csv`

**Exit Behavior:** Pipeline stops if this step fails.

---

### Step 2: Variant Spiders (`run_variants_parallel.py`)

Runs variant spiders in parallel (8 workers) using URLs from `variants_urls.txt`.

**Input:** `utils/variants_urls.txt` (comma or newline separated URLs)

**Output Files:**
- `Variants.csv` - Contains all variant information

**Exit Behavior:** Pipeline stops if this step fails.

---

### Step 3: Feature & Specification Spiders (`run_feature_spec_parallel.py`)

Runs feature and specification spiders in parallel (4 workers) using URLs from `feature_spec_urls.txt`.

**Input:** `utils/feature_spec_urls.txt` (comma or newline separated URLs)

**Output Files:**
- `feature-info.csv` - Features data
- `specification-info.csv` - Specifications data

**Exit Behavior:** Pipeline stops if this step fails.

---

### Step 4: Seed Mileage (`run_seedMileage.py`)

Fills missing mileage values in `Variants.csv` using Grok AI via OpenRouter API.

**Requirements:**
- OpenRouter API key must be configured in the script
- Handles different fuel types with correct units:
  - Petrol/Diesel: kmpl
  - CNG: km/kg
  - Electric: km/charge or km/kWh

**Modifies:** `Variants.csv`

**Exit Behavior:** Pipeline continues even if this step fails (with warning).

---

### Step 5: Process Variants (`run_processVariant.py`)

Updates variant information:
- Replaces variant names using JSON mapping (if available)
- Sets `variantType` to 'Top' for highest priced variant, 'Base' for others
- Randomly assigns `variantIsPopular` (True/False)

**Input (Optional):** `utils/variant_mapping.json`

**Modifies:** `Variants.csv`

**Exit Behavior:** Pipeline continues even if this step fails (with warning).

---

### Step 6: Variant Check (`run_variantcheck.py`)

**Critical Step:** Verifies consistency between `Variants.csv` and `specification-info.csv`.

Checks:
- Total number of unique variants match
- All variant names are present in both files

**Output:** Detailed report showing:
- Total variants in each file
- Which file has fewer variants (if mismatch)
- Missing variants in each file

**Exit Behavior:** 
- If variants match → Continues to Step 7
- If variants don't match → Skips Step 7 and shows detailed error report

---

### Step 7: Sheet Creator (`sheet-creator.py`)

**Conditional Step:** Only runs if Step 6 (Variant Check) passes.

Creates final Excel workbook with multiple sheets:
- **Categories** - Feature/specification categories
- **ModelYears** - Model year information
- **Individual CSV sheets** - All CSV files as separate sheets

**Output:** `combined/[model-name]-sheet.xlsx`

---

## Pipeline Behavior

### Success Flow

```
Step 1 ✓ → Step 2 ✓ → Step 3 ✓ → Step 4 ✓ → Step 5 ✓ → Step 6 ✓ → Step 7 ✓
```

### Failure Handling

- **Steps 1-3:** Pipeline stops immediately on failure
- **Steps 4-5:** Pipeline continues with warning
- **Step 6:** If fails, Step 7 is skipped
- **Step 7:** Only runs if Step 6 succeeds

### Example Output

```
================================================================================
  COMPLETE PIPELINE ORCHESTRATION
================================================================================
[12:30:00] [INFO] Output Folder: Output/Citroen/C3
[12:30:00] [INFO] Start Time: 2024-01-15 12:30:00

--------------------------------------------------------------------------------
STEP 1: Running Initial Spiders (FAQ, Rating, Pros/Cons/Colors)
--------------------------------------------------------------------------------
[12:30:05] [SUCCESS] ✓ Initial Spiders completed successfully in 45.23s

--------------------------------------------------------------------------------
STEP 2: Running Variant Spiders in Parallel
--------------------------------------------------------------------------------
[12:32:15] [SUCCESS] ✓ Variant Spiders completed successfully in 130.45s

... (continues for all steps)

================================================================================
  PIPELINE EXECUTION SUMMARY
================================================================================

Total Steps: 7
Successful: 7
Failed: 0

Total Execution Time: 456.78s

--------------------------------------------------------------------------------
Step Execution Times:
--------------------------------------------------------------------------------
  Initial Spiders               :    45.23s
  Variant Spiders               :   130.45s
  Feature & Spec Spiders        :   180.67s
  Seed Mileage                  :    45.12s
  Process Variants              :     2.34s
  Variant Check                 :     0.89s
  Sheet Creator                 :     3.45s

================================================================================
Pipeline ended at: 2024-01-15 12:37:36
================================================================================
```

## Configuration

### Folder Structure

The output folder should follow this structure:

```
Output/
└── [Brand]/
    └── [Model]/
        ├── Variants.csv
        ├── specification-info.csv
        ├── feature-info.csv
        ├── faq-info.csv
        ├── ratingInfo.csv
        ├── prosConsInfo.csv
        ├── colourOptionsInfo.csv
        ├── modelInfo.csv
        └── combined/
            └── [model]-sheet.xlsx
```

### Required Input Files

1. **utils/variants_urls.txt** - URLs for variant pages
2. **utils/feature_spec_urls.txt** - URLs for feature/spec pages
3. **utils/variant_mapping.json** (optional) - Variant name mapping

### Path Updates

The orchestration script automatically updates hardcoded paths in:
- `run_seedMileage.py` - Updates INPUT_CSV_PATH and OUTPUT_CSV_PATH
- `run_processVariant.py` - Updates CSV_BASE_PATH
- `sheet-creator.py` - Updates csv_folder

## Individual Script Usage

If you need to run scripts individually:

### 1. Initial Spiders
```bash
python utils/run_first_spiders.py
```

### 2. Variant Spiders
```bash
python utils/run_variants_parallel.py
```

### 3. Feature & Spec Spiders
```bash
python utils/run_feature_spec_parallel.py
```

### 4. Seed Mileage
```bash
python utils/run_seedMileage.py
```

### 5. Process Variants
```bash
python utils/run_processVariant.py [json_mapping] [csv_file]
# Or with defaults:
python utils/run_processVariant.py
```

### 6. Variant Check
```bash
python utils/run_variantcheck.py Output/Citroen/C3
```

### 7. Sheet Creator
```bash
python utils/sheet-creator.py
```

## Troubleshooting

### Issue: Variant Check Fails

**Symptoms:**
```
✗ MISMATCH DETECTED!
Variants in Variants.csv but MISSING in specification-info.csv:
  • VARIANT_NAME_1
  • VARIANT_NAME_2
```

**Solution:**
1. Review the mismatch report
2. Check variant name formatting consistency
3. Verify all variants were scraped correctly
4. Update variant mapping in `variant_mapping.json` if needed
5. Re-run Step 5 (Process Variants) with updated mapping

### Issue: Mileage Filling Fails

**Symptoms:**
```
[ERROR] 401 error querying Grok
```

**Solution:**
1. Check OpenRouter API key is valid
2. Verify API credits are available
3. Check internet connectivity
4. Review rate limits

### Issue: Spider Fails

**Symptoms:**
```
✗ Spider 'spider-name' failed with exit code 1
```

**Solution:**
1. Check the URL list files (variants_urls.txt, feature_spec_urls.txt)
2. Verify URLs are valid and accessible
3. Check scrapy.cfg exists in project root
4. Review spider logs for specific errors

## Exit Codes

- `0` - Success (all steps completed, variants match)
- `1` - Failure (one or more steps failed, or variants don't match)
- `130` - Interrupted by user (Ctrl+C)

## Notes

- The pipeline automatically stops on critical failures (Steps 1-3)
- Non-critical failures (Steps 4-5) allow pipeline to continue
- Sheet creation only occurs if variant check passes
- All output is shown in real-time for transparency
- Execution times are tracked for each step
- The script updates hardcoded paths automatically

## Dependencies

- Python 3.7+
- Scrapy
- pandas
- xlsxwriter
- OpenAI (for mileage filling)
- All spider dependencies

## Support

For issues or questions:
1. Check the individual script documentation
2. Review error messages and logs
3. Verify all input files are properly formatted
4. Ensure all dependencies are installed