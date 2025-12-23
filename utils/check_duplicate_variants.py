#!/usr/bin/env python3
"""
Diagnostic script to check for duplicate variants in URLs.
This script analyzes the variants_urls.txt file and checks if multiple URLs
might be pointing to the same variant (either through redirects or duplicate entries).
"""

import os
import sys
from collections import defaultdict
from urllib.parse import urlparse


def extract_variant_name_from_url(url):
    """
    Extract the variant name from the URL.
    Example: https://www.cardekho.com/overview/Tata_Punch/Tata_Punch_Adventure_Plus.htm
    Returns: Tata_Punch_Adventure_Plus
    """
    parts = url.rstrip("/").split("/")
    if len(parts) > 0:
        last_part = parts[-1]
        # Remove .htm extension
        variant = last_part.replace(".htm", "")
        return variant
    return url


def normalize_variant_name(variant):
    """
    Normalize variant name for comparison.
    Removes underscores and converts to lowercase.
    """
    # Extract just the variant part after the model name
    parts = variant.split(
        "_", 2
    )  # Split on first 2 underscores to get Tata_Punch_VariantName
    if len(parts) >= 3:
        variant_only = parts[2]
    else:
        variant_only = variant

    return variant_only.lower().replace("_", " ")


def main():
    """Main function to analyze variants URLs."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    urls_file = os.path.join(script_dir, "variants_urls.txt")

    if not os.path.exists(urls_file):
        print(f"[ERROR] File not found: {urls_file}")
        sys.exit(1)

    # Read URLs
    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print("=" * 80)
    print("VARIANT URLs ANALYSIS")
    print("=" * 80)
    print(f"Total URLs: {len(urls)}")
    print()

    # Track variants
    variant_to_urls = defaultdict(list)
    url_to_variant_name = {}

    for url in urls:
        variant_full = extract_variant_name_from_url(url)
        variant_normalized = normalize_variant_name(variant_full)

        variant_to_urls[variant_normalized].append(url)
        url_to_variant_name[url] = (variant_full, variant_normalized)

    # Find duplicates
    duplicates = {k: v for k, v in variant_to_urls.items() if len(v) > 1}

    if duplicates:
        print(f"⚠️  WARNING: Found {len(duplicates)} potential duplicate variants!")
        print("=" * 80)
        print()

        for variant_name, urls_list in sorted(duplicates.items()):
            print(f"Variant: {variant_name}")
            print(f"  Appears {len(urls_list)} times:")
            for url in urls_list:
                full_name = url_to_variant_name[url][0]
                print(f"    - {full_name}")
                print(f"      {url}")
            print()
    else:
        print("✓ No duplicate variants found!")
        print()

    # Show unique variants
    unique_variants = [k for k, v in variant_to_urls.items() if len(v) == 1]
    print(f"✓ Unique variants: {len(unique_variants)}")
    print(f"✗ Duplicate variants: {len(duplicates)}")
    print()

    # Calculate expected vs actual
    total_unique = len(variant_to_urls)
    print(f"Expected unique variants to scrape: {total_unique}")
    print(f"Total URLs provided: {len(urls)}")
    print(f"Wasted URLs (duplicates): {len(urls) - total_unique}")
    print()

    # Show all variants in order
    print("=" * 80)
    print("ALL VARIANTS (in order of appearance)")
    print("=" * 80)

    seen = set()
    for i, url in enumerate(urls, 1):
        full_name, normalized = url_to_variant_name[url]
        is_duplicate = normalized in seen
        status = "DUPLICATE" if is_duplicate else "NEW"
        seen.add(normalized)

        print(f"{i:2d}. [{status:9s}] {normalized}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total URLs in file:        {len(urls)}")
    print(f"Unique variants:           {total_unique}")
    print(f"Duplicate entries:         {len(urls) - total_unique}")
    print(f"Expected CSV rows:         {total_unique} (excluding header)")
    print("=" * 80)

    if duplicates:
        print()
        print("💡 RECOMMENDATION:")
        print(
            "   Remove duplicate URLs from variants_urls.txt to avoid wasted scraping."
        )
        print("   The spider's duplicate filter is working correctly, but it's still")
        print("   processing duplicate pages unnecessarily.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
