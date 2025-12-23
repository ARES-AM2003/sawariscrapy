#!/usr/bin/env python3
"""
Automatic Pipeline Configuration and Execution Script

This script automatically:
1. Updates brand name and model name in all required spider files
2. Updates URLs for CarDekho, CarWale, and AutoCarIndia
3. Configures the output path
4. Runs the complete pipeline automatically

Usage:
    1. Update the variables in the CONFIGURATION section below
    2. Run: python3 auto_update_and_run.py

The script will:
    - Update all spider files with brand/model names and URLs
    - Update link_and_path.py
    - Create the output folder structure
    - Run the complete pipeline automatically
"""

import os
import re
import subprocess
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION VARIABLES - UPDATE THESE FOR YOUR CAR MODEL
# ============================================================================

# Brand and Model Information
BRAND_NAME = "Tata"
MODEL_NAME = "Punch"

# Website URLs (main model pages)
CARDEKHO_LINK = "https://www.cardekho.com/tata/punch"
CARWALE_LINK = "https://www.carwale.com/tata-cars/punch/"
AUTOCARINDIA_LINK = "https://www.autocarindia.com/cars/tata/punch"

# ============================================================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================================================


class SpiderUpdater:
    """Handles updating all spider files and running the pipeline."""

    def __init__(self, brand, model, cardekho_url, carwale_url, autocar_url):
        """Initialize the updater with configuration."""
        self.brand_name = brand
        self.model_name = model
        self.cardekho_url = cardekho_url
        self.carwale_url = carwale_url
        self.autocar_url = autocar_url

        # Get directory paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.script_dir)
        self.spiders_dir = os.path.join(self.project_root, "sawari-expert", "spiders")
        self.link_and_path_file = os.path.join(
            self.project_root, "sawari-expert", "link_and_path.py"
        )
        self.complete_pipeline_script = os.path.join(
            self.script_dir, "run_complete_pipeline.py"
        )

        # Output folder structure
        self.output_folder = f"Output/{self.brand_name}/{self.model_name}"
        self.output_path = f"output/{self.brand_name}/{self.model_name}/"

        # Backup directory
        self.backup_dir = os.path.join(
            self.script_dir, "backups", datetime.now().strftime("%Y%m%d_%H%M%S")
        )

    def log(self, message, level="INFO"):
        """Print formatted log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def create_backup(self):
        """Create backup of all files before modification."""
        self.log("Creating backups of files...")
        os.makedirs(self.backup_dir, exist_ok=True)

        files_to_backup = {
            "link_and_path": self.link_and_path_file,
            "faq": os.path.join(self.spiders_dir, "faq.py"),
            "pros_cons_colours": os.path.join(self.spiders_dir, "pros_cons_colours.py"),
            "model_with_ratings": os.path.join(
                self.spiders_dir, "model_with_ratings.py"
            ),
        }

        for name, filepath in files_to_backup.items():
            if os.path.exists(filepath):
                backup_path = os.path.join(self.backup_dir, f"{name}_backup.py")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.log(f"✓ Backed up: {name}", "SUCCESS")
                except Exception as e:
                    self.log(f"✗ Failed to backup {name}: {e}", "ERROR")
                    return False

        self.log(f"Backups saved to: {self.backup_dir}", "SUCCESS")
        return True

    def update_link_and_path(self):
        """Update link_and_path.py with new URLs and path."""
        self.log("Updating link_and_path.py...")

        # Create new content
        content = f'''# Path
path = "{self.output_path}"
#links
car_dekho = "{self.cardekho_url}"
car_wale = "{self.carwale_url}"
auto_car = "{self.autocar_url}"
'''

        try:
            with open(self.link_and_path_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"✓ Updated link_and_path.py", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to update link_and_path.py: {e}", "ERROR")
            return False

    def update_faq_spider(self):
        """Update faq.py spider."""
        self.log("Updating faq.py spider...")

        filepath = os.path.join(self.spiders_dir, "faq.py")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Update start_urls
            content = re.sub(
                r"start_urls\s*=\s*\[.*?\]",
                f'start_urls = ["{self.cardekho_url}"]',
                content,
                flags=re.DOTALL,
            )

            # Update brand_name
            content = re.sub(
                r"brand_name\s*=\s*['\"].*?['\"]",
                f"brand_name = '{self.brand_name}'",
                content,
            )

            # Update model_name
            content = re.sub(
                r"model_name\s*=\s*['\"].*?['\"]",
                f"model_name = '{self.model_name.lower()}'",
                content,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.log(f"✓ Updated faq.py", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to update faq.py: {e}", "ERROR")
            return False

    def update_pros_cons_colours_spider(self):
        """Update pros_cons_colours.py spider."""
        self.log("Updating pros_cons_colours.py spider...")

        filepath = os.path.join(self.spiders_dir, "pros_cons_colours.py")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Update start_urls
            content = re.sub(
                r"start_urls\s*=\s*\[.*?\]",
                f'start_urls = ["{self.cardekho_url}"]',
                content,
                flags=re.DOTALL,
            )

            # Update brand_name
            content = re.sub(
                r"brand_name\s*=\s*['\"].*?['\"]",
                f"brand_name = '{self.brand_name}'",
                content,
            )

            # Update model_name
            content = re.sub(
                r"model_name\s*=\s*['\"].*?['\"]",
                f"model_name = '{self.model_name.lower()}'",
                content,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.log(f"✓ Updated pros_cons_colours.py", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to update pros_cons_colours.py: {e}", "ERROR")
            return False

    def update_model_with_ratings_spider(self):
        """Update model_with_ratings.py spider."""
        self.log("Updating model_with_ratings.py spider...")

        filepath = os.path.join(self.spiders_dir, "model_with_ratings.py")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Update start_urls
            content = re.sub(
                r"start_urls\s*=\s*\[.*?\]",
                f'start_urls = ["{self.autocar_url}"]',
                content,
                flags=re.DOTALL,
            )

            # Update brand_name
            content = re.sub(
                r"brand_name\s*=\s*['\"].*?['\"]",
                f"brand_name = '{self.brand_name}'",
                content,
            )

            # Update model_name
            content = re.sub(
                r"model_name\s*=\s*['\"].*?['\"]",
                f"model_name = '{self.model_name.lower()}'",
                content,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.log(f"✓ Updated model_with_ratings.py", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to update model_with_ratings.py: {e}", "ERROR")
            return False

    def create_output_folder(self):
        """Create the output folder structure."""
        self.log(f"Creating output folder: {self.output_folder}...")

        output_path = os.path.join(self.project_root, self.output_folder)

        try:
            os.makedirs(output_path, exist_ok=True)
            self.log(f"✓ Output folder created: {output_path}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"✗ Failed to create output folder: {e}", "ERROR")
            return False

    def run_pipeline(self):
        """Run the complete pipeline."""
        self.log("Starting complete pipeline execution...")

        pipeline_script = os.path.join(self.script_dir, "run_complete_pipeline.py")

        if not os.path.exists(pipeline_script):
            self.log(f"✗ Pipeline script not found: {pipeline_script}", "ERROR")
            return False

        try:
            # Run the pipeline
            self.log(f"Executing: python3 {pipeline_script} {self.output_folder}")
            result = subprocess.run(
                ["python3", pipeline_script, self.output_folder],
                cwd=self.project_root,
                capture_output=False,
                text=True,
            )

            if result.returncode == 0:
                self.log("✓ Pipeline completed successfully!", "SUCCESS")
                return True
            else:
                self.log(
                    f"✗ Pipeline failed with exit code {result.returncode}", "ERROR"
                )
                return False

        except Exception as e:
            self.log(f"✗ Error running pipeline: {e}", "ERROR")
            return False

    def display_config(self):
        """Display the current configuration."""
        self.print_header("CONFIGURATION")
        print(f"Brand Name:        {self.brand_name}")
        print(f"Model Name:        {self.model_name}")
        print(f"Output Folder:     {self.output_folder}")
        print(f"\nURLs:")
        print(f"  CarDekho:        {self.cardekho_url}")
        print(f"  CarWale:         {self.carwale_url}")
        print(f"  AutoCarIndia:    {self.autocar_url}")
        print()

    def run(self):
        """Execute the complete update and pipeline run process."""
        start_time = datetime.now()

        self.print_header("AUTO SPIDER UPDATER AND PIPELINE RUNNER")
        self.log(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Display configuration
        self.display_config()

        # Step 1: Create backups
        self.print_header("STEP 1: Creating Backups")
        if not self.create_backup():
            self.log("Failed to create backups. Aborting.", "ERROR")
            return False

        # Step 2: Update all files
        self.print_header("STEP 2: Updating Spider Files")

        updates = [
            ("link_and_path.py", self.update_link_and_path),
            ("faq.py", self.update_faq_spider),
            ("pros_cons_colours.py", self.update_pros_cons_colours_spider),
            ("model_with_ratings.py", self.update_model_with_ratings_spider),
        ]

        all_success = True
        for name, update_func in updates:
            if not update_func():
                all_success = False
                self.log(f"Failed to update {name}", "ERROR")

        if not all_success:
            self.log("Some updates failed. Check the logs above.", "ERROR")
            return False

        # Step 3: Create output folder
        self.print_header("STEP 3: Creating Output Folder")
        if not self.create_output_folder():
            self.log("Failed to create output folder. Aborting.", "ERROR")
            return False

        # Step 4: Run pipeline
        self.print_header("STEP 4: Running Complete Pipeline")
        self.log("This may take several minutes depending on the number of variants...")

        pipeline_success = self.run_pipeline()

        # Final summary
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        self.print_header("EXECUTION SUMMARY")
        print(f"Start Time:     {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time:       {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {elapsed:.2f} seconds ({elapsed / 60:.2f} minutes)")
        print(f"\nStatus:         {'✓ SUCCESS' if pipeline_success else '✗ FAILED'}")
        print(f"Output Folder:  {os.path.join(self.project_root, self.output_folder)}")
        print(f"Backups:        {self.backup_dir}")
        print()

        if pipeline_success:
            self.log("All operations completed successfully! 🎉", "SUCCESS")
            self.log(f"Check your output files in: {self.output_folder}", "INFO")
        else:
            self.log("Pipeline execution failed. Check logs for details.", "ERROR")

        return pipeline_success


def validate_configuration():
    """Validate the configuration before running."""
    errors = []

    if not BRAND_NAME or BRAND_NAME.strip() == "":
        errors.append("BRAND_NAME cannot be empty")

    if not MODEL_NAME or MODEL_NAME.strip() == "":
        errors.append("MODEL_NAME cannot be empty")

    if not CARDEKHO_LINK or not CARDEKHO_LINK.startswith("http"):
        errors.append("CARDEKHO_LINK must be a valid URL")

    if not CARWALE_LINK or not CARWALE_LINK.startswith("http"):
        errors.append("CARWALE_LINK must be a valid URL")

    if not AUTOCARINDIA_LINK or not AUTOCARINDIA_LINK.startswith("http"):
        errors.append("AUTOCARINDIA_LINK must be a valid URL")

    if errors:
        print("\n" + "=" * 80)
        print("  CONFIGURATION ERRORS")
        print("=" * 80 + "\n")
        for error in errors:
            print(f"✗ {error}")
        print("\nPlease update the configuration variables at the top of this script.")
        print("=" * 80 + "\n")
        return False

    return True


def main():
    """Main entry point."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║          AUTO SPIDER UPDATER AND PIPELINE RUNNER                            ║
║          Automatically configure spiders and run complete pipeline           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Validate configuration
    if not validate_configuration():
        sys.exit(1)

    # Create updater and run
    updater = SpiderUpdater(
        brand=BRAND_NAME,
        model=MODEL_NAME,
        cardekho_url=CARDEKHO_LINK,
        carwale_url=CARWALE_LINK,
        autocar_url=AUTOCARINDIA_LINK,
    )

    success = updater.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


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
