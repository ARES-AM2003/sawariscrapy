#!/usr/bin/env python3
"""
Sequential Variant Spider Runner
This script runs the variant spider sequentially (one URL at a time) for maximum reliability.
Use this when parallel processing is causing issues or when you need guaranteed results.

- Reads URLs from variants_urls.txt
- Processes one URL at a time with proper delays
- More reliable but slower than parallel processing
- Outputs to Output/[ModelName]/Variants.csv

Usage:
    python3 run_variants_sequential.py
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def read_urls_from_file(filename):
    """
    Read URLs from a text file that can be comma-separated or newline-separated.

    Args:
        filename: Path to the file containing URLs

    Returns:
        List of cleaned URLs
    """
    if not os.path.exists(filename):
        print(f"[ERROR] File '{filename}' not found!")
        return []

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    import re

    # Split by both commas and newlines
    urls = re.split(r"[,\n]", content)

    # Clean up URLs (strip whitespace and remove empty strings)
    urls = [url.strip() for url in urls if url.strip()]

    return urls


def run_spider_for_url(spider_name, url, project_root, index, total):
    """
    Run spider for a single URL.

    Args:
        spider_name: Name of the spider to run
        url: Single URL to process
        project_root: Root directory of the scrapy project
        index: Current URL index (1-based)
        total: Total number of URLs

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 80)
    print(f"Processing URL {index}/{total}")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)

    start_time = time.time()

    try:
        # Run spider for this single URL
        result = subprocess.run(
            [
                "scrapy",
                "crawl",
                spider_name,
                "-a",
                f"url={url}",
                "-s",
                "LOG_LEVEL=INFO",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ [{index}/{total}] Success in {elapsed_time:.2f}s")
            return True
        else:
            print(f"\n❌ [{index}/{total}] Failed with exit code {result.returncode}")
            if result.stderr:
                # Print last 500 chars of error
                print(f"Error: {result.stderr[-500:]}")
            return False

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ [{index}/{total}] Error: {e}")
        return False


def main():
    """Main function to run sequential variant scraping."""

    # Get the script's directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Configuration
    INPUT_FILE = os.path.join(script_dir, "variants_urls.txt")
    SPIDER_NAME = "variants"
    DELAY_BETWEEN_URLS = 3  # Seconds to wait between URLs

    # Check if scrapy.cfg exists in project root
    scrapy_cfg = os.path.join(project_root, "scrapy.cfg")
    if not os.path.exists(scrapy_cfg):
        print(f"[ERROR] scrapy.cfg not found at {scrapy_cfg}")
        print(
            "[ERROR] Please ensure the script is in the utils folder of your scrapy project"
        )
        sys.exit(1)

    # Read URLs from file
    print(f"[INFO] Reading URLs from '{INPUT_FILE}'...")
    urls = read_urls_from_file(INPUT_FILE)

    if not urls:
        print("[ERROR] No URLs found in the input file!")
        print(f"[INFO] Please create 'variants_urls.txt' in the utils folder with URLs")
        sys.exit(1)

    print(f"[SUCCESS] Found {len(urls)} URL(s) to process")
    print()

    # Display configuration
    print("=" * 80)
    print("🐢 SEQUENTIAL VARIANT SPIDER (Slow but Reliable)")
    print("=" * 80)
    print(f"Total URLs:          {len(urls)}")
    print(f"Processing mode:     Sequential (one at a time)")
    print(f"Delay between URLs:  {DELAY_BETWEEN_URLS} seconds")
    print(f"Estimated time:      ~{len(urls) * 30 / 60:.1f} minutes")
    print(f"Output:              Output/[ModelName]/Variants.csv")
    print(f"Start time:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Confirm with user
    try:
        response = input("Continue with sequential processing? (y/n): ")
        if response.lower() != "y":
            print("[INFO] Aborted by user")
            sys.exit(0)
    except (EOFError, KeyboardInterrupt):
        print("\n[INFO] Running in non-interactive mode, proceeding...")

    print()

    # Track statistics
    success_count = 0
    failed_count = 0
    failed_urls = []
    overall_start_time = time.time()

    # Process each URL sequentially
    for index, url in enumerate(urls, 1):
        success = run_spider_for_url(SPIDER_NAME, url, project_root, index, len(urls))

        if success:
            success_count += 1
        else:
            failed_count += 1
            failed_urls.append((index, url))

        # Wait before processing next URL (except for the last one)
        if index < len(urls):
            print(f"\n⏳ Waiting {DELAY_BETWEEN_URLS} seconds before next URL...")
            time.sleep(DELAY_BETWEEN_URLS)

    # Calculate total time
    total_time = time.time() - overall_start_time

    # Display final summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total URLs:           {len(urls)}")
    print(f"Successfully scraped: {success_count}")
    print(f"Failed:               {failed_count}")
    print(f"Success rate:         {success_count / len(urls) * 100:.1f}%")
    print(f"Total execution time: {total_time:.2f}s ({total_time / 60:.2f} minutes)")
    print(f"Average per URL:      {total_time / len(urls):.2f}s")
    print(f"End time:             {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Show failed URLs if any
    if failed_urls:
        print("\n" + "=" * 80)
        print(f"⚠️  FAILED URLS ({len(failed_urls)})")
        print("=" * 80)
        for idx, url in failed_urls:
            print(f"{idx}. {url}")
        print("=" * 80)
        print()
        print("💡 TIP: You can manually retry failed URLs by running:")
        print(f"   scrapy crawl {SPIDER_NAME} -a url=<failed_url>")

    print(f"\n[INFO] All variants have been written to Output/[ModelName]/Variants.csv")

    if failed_count == 0:
        print(f"\n✅ [SUCCESS] All {success_count} URLs processed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  [PARTIAL SUCCESS] {success_count}/{len(urls)} URLs succeeded")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Script terminated by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
