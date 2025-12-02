# Quick Start Guide - Complete Pipeline

## TL;DR

Run the entire pipeline with one command:

```bash
python utils/run_complete_pipeline.py Output/Citroen/C3
```

Replace `Output/Citroen/C3` with your desired output folder.

---

## What It Does

This orchestration script runs **7 steps automatically**:

1. ✅ Initial spiders (FAQ, ratings, colors)
2. ✅ Variant spiders (parallel)
3. ✅ Feature & specification spiders (parallel)
4. ✅ Fill missing mileage data
5. ✅ Process variant names & metadata
6. ✅ Verify variant consistency
7. ✅ Create Excel sheet (only if variants match)

---

## Prerequisites

### 1. URL Files

Create these two files in `utils/` folder:

**`utils/variants_urls.txt`**
```
https://example.com/variant1
https://example.com/variant2
https://example.com/variant3
```

**`utils/feature_spec_urls.txt`**
```
https://example.com/specs1
https://example.com/specs2
```

### 2. API Key (Optional - for mileage filling)

Edit `utils/run_seedMileage.py` and add your OpenRouter API key:
```python
OPENROUTER_API_KEY = "your-api-key-here"
```

### 3. Variant Mapping (Optional)

Create `utils/variant_mapping.json` to rename variants:
```json
{
  "OLD NAME": "New Name",
  "SIGMA": "Sigma 1.2L Petrol",
  "DELTA": "Delta 1.2L Petrol"
}
```

---

## Usage

### Run Complete Pipeline

```bash
cd /home/ares-am/Projects/BNT/scrapy
python utils/run_complete_pipeline.py Output/Citroen/C3
```

### Output Structure

```
Output/Citroen/C3/
├── Variants.csv              ← All variants
├── specification-info.csv    ← Specifications
├── feature-info.csv          ← Features
├── faq-info.csv              ← FAQs
├── ratingInfo.csv            ← Ratings
├── prosConsInfo.csv          ← Pros & Cons
├── colourOptionsInfo.csv     ← Colors
├── modelInfo.csv             ← Model info
└── combined/
    └── maruti-ignis-sheet.xlsx  ← Final Excel sheet
```

---

## Individual Scripts

If you need to run scripts separately:

### 1. Check Variant Consistency Only
```bash
python utils/run_variantcheck.py Output/Citroen/C3
```

**Returns:**
- `True` - All variants match ✅
- `False` - Variants don't match ❌ (shows details)

**Success Output:**
```
✓ SUCCESS: All variants match!
Total unique variants in Variants.csv: 11
Total unique variants in specification-info.csv: 11
```

**Error Output:**
```
✗ MISMATCH DETECTED!
specification-info.csv has FEWER variants (9 vs 11)

--- Variants in Variants.csv but MISSING in specification-info.csv (2): ---
  • VARIANT A
  • VARIANT B
```

### 2. Run Individual Steps

```bash
# Step 1: Initial spiders
python utils/run_first_spiders.py

# Step 2: Variant spiders
python utils/run_variants_parallel.py

# Step 3: Feature & spec spiders
python utils/run_feature_spec_parallel.py

# Step 4: Fill mileage
python utils/run_seedMileage.py

# Step 5: Process variants
python utils/run_processVariant.py Output/Citroen/C3/Variants.csv

# Step 6: Check variants
python utils/run_variantcheck.py Output/Citroen/C3

# Step 7: Create Excel
python utils/sheet-creator.py
```

---

## Using Variant Check in Python

```python
from utils.run_variantcheck import check_variants

# With verbose output
result = check_variants('Output/Citroen/C3', verbose=True)

# Silent mode (returns True/False only)
result = check_variants('Output/Citroen/C3', verbose=False)

if result:
    print("✅ Variants match!")
else:
    print("❌ Variants don't match!")
```

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Initial Spiders                                     │
│ Outputs: FAQ, Ratings, Pros/Cons, Colors, Model Info       │
└─────────────────────────────────────────────────────────────┘
                          ↓ (Success)
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Variant Spiders (Parallel: 8 workers)              │
│ Outputs: Variants.csv                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓ (Success)
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Feature & Spec Spiders (Parallel: 4 workers)       │
│ Outputs: feature-info.csv, specification-info.csv          │
└─────────────────────────────────────────────────────────────┘
                          ↓ (Success)
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Seed Mileage (Optional - continues on failure)     │
│ Updates: Variants.csv                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓ (Continue)
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Process Variants (Optional - continues on failure) │
│ Updates: Variants.csv (names, types, popularity)           │
└─────────────────────────────────────────────────────────────┘
                          ↓ (Continue)
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Variant Check (CRITICAL)                           │
│ Compares: Variants.csv vs specification-info.csv           │
└─────────────────────────────────────────────────────────────┘
              ↓ (Match?)                    ↓ (No Match?)
        ┌─────────────┐              ┌────────────────┐
        │   SUCCESS   │              │   STOP HERE    │
        │   ↓         │              │  Show Errors   │
        │ Step 7:     │              │  Skip Excel    │
        │ Excel Sheet │              └────────────────┘
        └─────────────┘
```

---

## Troubleshooting

### Problem: Variant Check Fails

**Error:**
```
✗ MISMATCH DETECTED!
Both files have the same count (11) but different variant names
```

**Solution:**
1. Check variant names in both CSVs
2. Update `utils/variant_mapping.json` to standardize names
3. Re-run Step 5: `python utils/run_processVariant.py`
4. Re-run Step 6: `python utils/run_variantcheck.py Output/Citroen/C3`

### Problem: Mileage API Fails

**Error:**
```
401 error querying Grok
```

**Solution:**
- Check API key in `run_seedMileage.py`
- Verify API credits available
- Pipeline continues anyway (mileage is optional)

### Problem: Spider Fails

**Error:**
```
✗ Spider 'variants' failed with exit code 1
```

**Solution:**
- Check URL files exist: `variants_urls.txt`, `feature_spec_urls.txt`
- Verify URLs are accessible
- Check `scrapy.cfg` exists in project root

---

## Key Features

✅ **Automatic Path Management** - Updates all hardcoded paths automatically

✅ **Smart Failure Handling** - Stops on critical errors, continues on optional steps

✅ **Real-time Output** - See progress as it happens

✅ **Execution Tracking** - Shows time taken for each step

✅ **Variant Validation** - Ensures data consistency before Excel creation

✅ **Conditional Excel Creation** - Only creates sheet if variants match

---

## Exit Codes

- `0` = Success ✅
- `1` = Failure (variants don't match or critical error) ❌
- `130` = Interrupted by user (Ctrl+C) ⚠️

---

## Files Created by This Guide

1. **`run_complete_pipeline.py`** - Main orchestration script
2. **`run_variantcheck.py`** - Variant consistency checker
3. **`PIPELINE_README.md`** - Detailed documentation
4. **`QUICK_START.md`** - This guide

---

## Example Session

```bash
$ python utils/run_complete_pipeline.py Output/Citroen/C3

================================================================================
  COMPLETE PIPELINE ORCHESTRATION
================================================================================
[14:30:00] [INFO] Output Folder: Output/Citroen/C3
[14:30:00] [INFO] Start Time: 2024-12-01 14:30:00

--------------------------------------------------------------------------------
STEP 1: Running Initial Spiders (FAQ, Rating, Pros/Cons/Colors)
--------------------------------------------------------------------------------
[14:30:45] [SUCCESS] ✓ Initial Spiders completed successfully in 45.23s

--------------------------------------------------------------------------------
STEP 2: Running Variant Spiders in Parallel
--------------------------------------------------------------------------------
[14:32:55] [SUCCESS] ✓ Variant Spiders completed successfully in 130.45s

... (continues)

--------------------------------------------------------------------------------
STEP 6: Verifying Variant Consistency
--------------------------------------------------------------------------------

Checking variants in: Output/Citroen/C3
================================================================================

Total unique variants in Variants.csv: 11
Total unique variants in specification-info.csv: 11

✓ SUCCESS: All variants match!
================================================================================

[14:37:30] [INFO] Variant check passed! Proceeding to create Excel sheet...

--------------------------------------------------------------------------------
STEP 7: Creating Final Excel Sheet
--------------------------------------------------------------------------------
[14:37:33] [SUCCESS] ✓ Sheet Creator completed successfully in 3.45s

================================================================================
  PIPELINE EXECUTION SUMMARY
================================================================================

Total Steps: 7
Successful: 7
Failed: 0

Total Execution Time: 456.78s

✅ COMPLETE SUCCESS - Excel sheet created at: Output/Citroen/C3/combined/
```

---

## Need Help?

See `PIPELINE_README.md` for detailed documentation of each step.