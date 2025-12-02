#!/usr/bin/env python3
"""
Variant Check Script
This script compares variants between Variants.csv and Specifications.csv
to ensure data consistency.

Usage as script:
    python run_variantcheck.py <folder_path>

Usage as module:
    from utils.run_variantcheck import check_variants

    result = check_variants('/path/to/folder')
    if result:
        print("Variants match!")
    else:
        print("Variants don't match!")

Returns:
    True if all variants match
    False if variants don't match (with details about missing variants)
"""

import os
import sys
import csv
from typing import Set, Tuple, Dict


def read_variants_from_variants_csv(file_path: str) -> Set[str]:
    """
    Read unique variant names from Variants.csv

    Args:
        file_path: Path to Variants.csv file

    Returns:
        Set of unique variant names (normalized to uppercase for comparison)
    """
    variants = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                variant_name = row.get('variantName', '').strip()
                if variant_name:
                    # Normalize variant name for comparison
                    variants.add(variant_name.upper())
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return set()
    except Exception as e:
        print(f"Error reading Variants.csv: {e}")
        return set()

    return variants


def read_variants_from_specification_csv(file_path: str) -> Set[str]:
    """
    Read unique variant names from Specifications.csv

    Args:
        file_path: Path to Specifications.csv file

    Returns:
        Set of unique variant names (normalized to uppercase for comparison)
    """
    variants = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                variant_name = row.get('variantName', '').strip()
                if variant_name:
                    # Normalize variant name for comparison
                    variants.add(variant_name.upper())
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return set()
    except Exception as e:
        print(f"Error reading Specifications.csv: {e}")
        return set()

    return variants


def check_variants(folder_path: str, verbose: bool = True) -> bool:
    """
    Compare variants between Variants.csv and Specifications.csv
    This is the main function to use when importing as a module.

    Args:
        folder_path: Path to folder containing both CSV files
        verbose: If True, print detailed output. If False, only return result.

    Returns:
        True if variants match, False otherwise

    Example:
        >>> from utils.run_variantcheck import check_variants
        >>> result = check_variants('Output/Citroen/C3')
        >>> print(result)
        False
    """
    return compare_variants(folder_path, verbose)


def compare_variants(folder_path: str, verbose: bool = True) -> bool:
    """
    Internal function to compare variants between Variants.csv and Specifications.csv

    Args:
        folder_path: Path to folder containing both CSV files
        verbose: If True, print detailed output. If False, suppress output.

    Returns:
        True if variants match, False otherwise
    """
    # Construct file paths
    variants_csv_path = os.path.join(folder_path, 'Variants.csv')
    spec_csv_path = os.path.join(folder_path, 'Specifications.csv')

    # Check if both files exist
    if not os.path.exists(variants_csv_path):
        if verbose:
            print(f"Error: Variants.csv not found in {folder_path}")
        return False

    if not os.path.exists(spec_csv_path):
        if verbose:
            print(f"Error: Specifications.csv not found in {folder_path}")
        return False

    # Read variants from both files
    if verbose:
        print(f"\nChecking variants in: {folder_path}")
        print("=" * 80)

    variants_from_variants_csv = read_variants_from_variants_csv(variants_csv_path)
    variants_from_spec_csv = read_variants_from_specification_csv(spec_csv_path)

    # Get counts
    variants_count = len(variants_from_variants_csv)
    spec_count = len(variants_from_spec_csv)

    if verbose:
        print(f"\nTotal unique variants in Variants.csv: {variants_count}")
        print(f"Total unique variants in Specifications.csv: {spec_count}")

    # Check if counts match
    if variants_count == spec_count and variants_from_variants_csv == variants_from_spec_csv:
        if verbose:
            print("\n✓ SUCCESS: All variants match!")
            print("=" * 80)
        return True
    else:
        if verbose:
            print("\n✗ MISMATCH DETECTED!")
            print("=" * 80)

            # Determine which file has fewer variants
            if variants_count < spec_count:
                print(f"\nVariants.csv has FEWER variants ({variants_count} vs {spec_count})")
                print(f"Difference: {spec_count - variants_count} variants")
            elif variants_count > spec_count:
                print(f"\nSpecifications.csv has FEWER variants ({spec_count} vs {variants_count})")
                print(f"Difference: {variants_count - spec_count} variants")
            else:
                print(f"\nBoth files have the same count ({variants_count}) but different variant names")

            # Find missing variants in each file
            missing_in_spec = variants_from_variants_csv - variants_from_spec_csv
            missing_in_variants = variants_from_spec_csv - variants_from_variants_csv

            if missing_in_spec:
                print(f"\n--- Variants in Variants.csv but MISSING in Specifications.csv ({len(missing_in_spec)}): ---")
                for variant in sorted(missing_in_spec):
                    print(f"  • {variant}")

            if missing_in_variants:
                print(f"\n--- Variants in Specifications.csv but MISSING in Variants.csv ({len(missing_in_variants)}): ---")
                for variant in sorted(missing_in_variants):
                    print(f"  • {variant}")

            print("\n" + "=" * 80)
        return False


def main():
    """Main function to run the variant check"""
    if len(sys.argv) != 2:
        print("Usage: python run_variantcheck.py <folder_path>")
        print("\nExample:")
        print("  python run_variantcheck.py Output/Citroen/C3")
        sys.exit(1)

    folder_path = sys.argv[1]

    # Check if folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found - {folder_path}")
        sys.exit(1)

    # Run the comparison
    result = compare_variants(folder_path)

    # Exit with appropriate code
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
