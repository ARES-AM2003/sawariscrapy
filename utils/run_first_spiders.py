#!/usr/bin/env python3
"""
Script to run multiple Scrapy spiders in parallel.
Runs: faq, model-rating, and pros_cons_colours spiders simultaneously.
Outputs to Output/[ModelName]/ directory structure.
"""

import subprocess
import sys
import time
import os
import csv
from multiprocessing import Process, Queue
from datetime import datetime


def extract_model_name_from_output(output_dir):
    """
    Extract model name from any CSV file in the output directory.
    
    Args:
        output_dir: Directory to search for CSV files
        
    Returns:
        Model name string or None
    """
    try:
        # Find any CSV file in the output directory
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.csv'):
                    csv_path = os.path.join(root, file)
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        first_row = next(reader, None)
                        if first_row and 'modelName' in first_row:
                            return first_row['modelName']
    except Exception as e:
        print(f"[WARNING] Could not extract model name: {e}")
    
    return None


def move_files_to_final_output(temp_output_dir, final_output_dir):
    """
    Move all output files to the final Output/ModelName directory.
    
    Args:
        temp_output_dir: Temporary output directory
        final_output_dir: Final output directory
    """
    os.makedirs(final_output_dir, exist_ok=True)
    
    files_moved = 0
    for root, dirs, files in os.walk(temp_output_dir):
        for file in files:
            if file.endswith(('.csv', '.json')):
                source_path = os.path.join(root, file)
                dest_path = os.path.join(final_output_dir, file)
                
                try:
                    # Move the file
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    
                    os.rename(source_path, dest_path)
                    print(f"  ✓ Moved: {file}")
                    files_moved += 1
                except Exception as e:
                    print(f"  ✗ Failed to move {file}: {e}")
    
    return files_moved


def run_spider(spider_name, output_dir, project_root, queue):
    """
    Run a single spider and capture its exit code.
    
    Args:
        spider_name: Name of the spider to run
        output_dir: Output directory for spider results
        project_root: Root directory of the scrapy project
        queue: Queue to store the result
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting spider: {spider_name}")
    start_time = time.time()
    
    try:
        # Set environment variable for output directory
        env = os.environ.copy()
        env['SCRAPY_OUTPUT_DIR'] = output_dir
        
        # Run the spider with output directory parameter
        result = subprocess.run(
            ['scrapy', 'crawl', spider_name, '-s', 'LOG_LEVEL=INFO'],
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Spider '{spider_name}' completed successfully in {elapsed_time:.2f}s")
            queue.put((spider_name, 'success', elapsed_time))
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Spider '{spider_name}' failed with exit code {result.returncode}")
            if result.stderr:
                print(f"[ERROR] {result.stderr[:300]}")
            queue.put((spider_name, 'failed', elapsed_time))
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Spider '{spider_name}' error: {e}")
        queue.put((spider_name, 'error', elapsed_time))


def main():
    """Main function to run all spiders in parallel."""
    
    # Get the script's directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Use hardcoded output directory
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Define the spiders to run in two phases
    first_phase_spiders = [
        'faq',
        'pros_cons_colours'
    ]
    
    second_phase_spiders = [
        'model-rating'
    ]
    
    all_spiders = first_phase_spiders + second_phase_spiders
    
    print("=" * 70)
    print("RUNNING MULTIPLE SPIDERS IN PHASES")
    print("=" * 70)
    print(f"Phase 1 spiders: {', '.join(first_phase_spiders)}")
    print(f"Phase 2 spiders: {', '.join(second_phase_spiders)}")
    print(f"Output directory: {output_dir}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Check if scrapy.cfg exists
    scrapy_cfg = os.path.join(project_root, 'scrapy.cfg')
    if not os.path.exists(scrapy_cfg):
        print(f"[ERROR] scrapy.cfg not found at {scrapy_cfg}")
        print("[ERROR] Please ensure the script is in the utils folder of your scrapy project")
        sys.exit(1)
    
    # Create a queue to collect results
    result_queue = Queue()
    overall_start_time = time.time()
    
    # Phase 1: Run first set of spiders
    print("[PHASE 1] Starting first phase spiders...")
    print()
    processes = []
    
    for spider_name in first_phase_spiders:
        process = Process(target=run_spider, args=(spider_name, output_dir, project_root, result_queue))
        process.start()
        processes.append(process)
        time.sleep(1)  # Small delay between starting spiders to avoid resource conflicts
    
    # Wait for phase 1 to complete
    for process in processes:
        process.join()
    
    print()
    print("[PHASE 1] Completed. Waiting 2 seconds before starting phase 2...")
    time.sleep(2)
    
    # Phase 2: Run model-rating spider
    print("[PHASE 2] Starting model-rating spider...")
    print()
    processes = []
    
    for spider_name in second_phase_spiders:
        process = Process(target=run_spider, args=(spider_name, output_dir, project_root, result_queue))
        process.start()
        processes.append(process)
    
    # Wait for phase 2 to complete
    for process in processes:
        process.join()
    
    # Calculate total time
    total_time = time.time() - overall_start_time
    
    # Collect and display results
    print()
    print("=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # Sort results by spider name for consistent display
    results.sort(key=lambda x: x[0])
    
    success_count = 0
    failed_count = 0
    
    for spider_name, status, elapsed in results:
        status_icon = "✓" if status == "success" else "✗"
        status_text = status.upper()
        print(f"{status_icon} {spider_name:20s} - {status_text:10s} ({elapsed:.2f}s)")
        
        if status == "success":
            success_count += 1
        else:
            failed_count += 1
    
    print("=" * 70)
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Successful: {success_count}/{len(all_spiders)}")
    print(f"Failed: {failed_count}/{len(all_spiders)}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Display output location
    if success_count > 0:
        print(f"\n[SUCCESS] All output files saved to: {output_dir}")
        print("[INFO] Files created:")
        for file in sorted(os.listdir(output_dir)):
            if file.endswith(('.csv', '.json')):
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
    
    # Exit with appropriate code
    if failed_count > 0:
        print(f"\n[WARNING] {failed_count} spider(s) failed. Check the logs above for details.")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] All spiders completed successfully!")
        sys.exit(0)


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