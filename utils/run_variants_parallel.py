#!/usr/bin/env python3
"""
Parallel Variant Spider Runner (6 Concurrent Browsers)
This script runs the variant spider with 6 separate browser instances in parallel.
Each browser processes one URL at a time for maximum reliability.

- Reads URLs from variants_urls.txt
- Spawns 6 browser processes that work in parallel
- Each browser handles 1 URL at a time (single tab, no multi-tab issues)
- More reliable than multi-tab approach
- Outputs to Output/[ModelName]/Variants.csv

Usage:
    python3 run_variants_parallel.py
"""

import math
import os
import subprocess
import sys
import time
from datetime import datetime
from multiprocessing import Process, Queue


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


def run_spider_for_url(spider_name, url, project_root, index, total, queue):
    """
    Run spider for a single URL (runs in separate process).

    Args:
        spider_name: Name of the spider to run
        url: Single URL to process
        project_root: Root directory of the scrapy project
        index: Current URL index (1-based)
        total: Total number of URLs
        queue: Queue to store results

    Returns:
        True if successful, False otherwise
    """
    start_time = time.time()

    print(
        f"[Browser {index % 6 + 1}] [{index}/{total}] Starting: {url.split('/')[-1][:40]}..."
    )

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
                "LOG_LEVEL=ERROR",  # Reduce output noise
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            print(
                f"[Browser {index % 6 + 1}] ✅ [{index}/{total}] Success in {elapsed_time:.2f}s"
            )
            queue.put(("success", index, url, elapsed_time))
            return True
        else:
            print(
                f"[Browser {index % 6 + 1}] ❌ [{index}/{total}] Failed (code {result.returncode})"
            )
            queue.put(("failed", index, url, elapsed_time))
            return False

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[Browser {index % 6 + 1}] ❌ [{index}/{total}] Error: {e}")
        queue.put(("error", index, url, elapsed_time))
        return False


def run_parallel_batch(
    spider_name, urls_batch, project_root, start_index, total_urls, queue
):
    """
    Run a batch of URLs sequentially in one browser process.

    Args:
        spider_name: Name of the spider
        urls_batch: List of URLs for this browser to process
        project_root: Project root directory
        start_index: Starting index for this batch
        total_urls: Total number of URLs across all batches
        queue: Queue to store results
    """
    for i, url in enumerate(urls_batch):
        current_index = start_index + i
        run_spider_for_url(
            spider_name, url, project_root, current_index, total_urls, queue
        )

        # Small delay between URLs in same browser
        if i < len(urls_batch) - 1:
            time.sleep(1)


def main():
    """Main function to run parallel variant scraping with 6 browsers."""

    # Get the script's directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Configuration
    INPUT_FILE = os.path.join(script_dir, "variants_urls.txt")
    SPIDER_NAME = "variants"
    NUM_BROWSERS = 6  # Number of parallel browser instances

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
    print("🚀 PARALLEL VARIANT SPIDER (6 Concurrent Browsers)")
    print("=" * 80)
    print(f"Total URLs:              {len(urls)}")
    print(f"Number of browsers:      {NUM_BROWSERS}")
    print(f"Mode:                    Parallel (6 browsers, 1 URL each at a time)")
    print(f"Estimated memory:        ~2.7GB (450MB per browser)")
    print(f"Estimated time:          ~{len(urls) * 25 / NUM_BROWSERS / 60:.1f} minutes")
    print(f"Speedup vs sequential:   ~{NUM_BROWSERS}x")
    print(f"Output:                  Output/[ModelName]/Variants.csv")
    print(f"Start time:              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Split URLs into batches for each browser
    urls_per_browser = math.ceil(len(urls) / NUM_BROWSERS)
    url_batches = []

    for i in range(NUM_BROWSERS):
        start_idx = i * urls_per_browser
        end_idx = min((i + 1) * urls_per_browser, len(urls))
        batch = urls[start_idx:end_idx]
        if batch:
            url_batches.append((batch, start_idx + 1))  # +1 for 1-based indexing

    print(f"[INFO] Split {len(urls)} URLs into {len(url_batches)} browser batches:")
    for i, (batch, start_idx) in enumerate(url_batches, 1):
        print(f"  Browser {i}: {len(batch)} URLs (starting from URL #{start_idx})")
    print()

    # Create queue for results
    result_queue = Queue()

    # Track statistics
    overall_start_time = time.time()

    # Start all browser processes
    processes = []
    for i, (batch, start_idx) in enumerate(url_batches):
        process = Process(
            target=run_parallel_batch,
            args=(SPIDER_NAME, batch, project_root, start_idx, len(urls), result_queue),
        )
        process.start()
        processes.append(process)
        time.sleep(0.5)  # Small delay between browser starts

    print(
        f"[INFO] All {len(url_batches)} browsers started. Processing URLs in parallel...\n"
    )

    # Wait for all processes to complete
    for process in processes:
        process.join()

    # Calculate total time
    total_time = time.time() - overall_start_time

    # Collect results from queue
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    # Analyze results
    success_count = sum(1 for r in results if r[0] == "success")
    failed_count = sum(1 for r in results if r[0] in ["failed", "error"])
    failed_urls = [(r[1], r[2]) for r in results if r[0] in ["failed", "error"]]

    # Display final summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total URLs:              {len(urls)}")
    print(f"Successfully scraped:    {success_count}")
    print(f"Failed:                  {failed_count}")
    print(f"Success rate:            {success_count / len(urls) * 100:.1f}%")
    print(f"Total execution time:    {total_time:.2f}s ({total_time / 60:.2f} minutes)")
    print(f"Average per URL:         {total_time / len(urls):.2f}s")
    print(f"Speedup achieved:        ~{len(urls) * 25 / total_time:.1f}x vs sequential")
    print(f"End time:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Show failed URLs if any
    if failed_urls:
        print("\n" + "=" * 80)
        print(f"⚠️  FAILED URLS ({len(failed_urls)})")
        print("=" * 80)
        for idx, url in sorted(failed_urls):
            print(f"{idx}. {url}")
        print("=" * 80)
        print()
        print("💡 TIP: You can manually retry failed URLs by running:")
        print(f"   scrapy crawl {SPIDER_NAME} -a url=<failed_url>")

    print(f"\n[INFO] All variants have been written to Output/[ModelName]/Variants.csv")

    if failed_count == 0:
        print(f"\n✅ [SUCCESS] All {success_count} URLs processed successfully!")
        print(
            f"💡 Processed {NUM_BROWSERS} URLs at a time using {NUM_BROWSERS} parallel browsers"
        )
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
