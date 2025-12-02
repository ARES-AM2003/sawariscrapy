import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import re
import time


class FeatureSpecificationSpider(scrapy.Spider):
    name = "feature-specification"
    allowed_domains = ["carwale.com"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'sawari-expert.pipelines.SpecificationInfoJsonPipeline': 300,
            'sawari-expert.pipelines.SpecificationInfoCsvPipeline': 400,
            'sawari-expert.pipelines.FeatureInfoJsonPipeline': 500,
            'sawari-expert.pipelines.FeatureInfoCsvPipeline': 600,
        },
        'CONCURRENT_REQUESTS': 1,  # Process one URL at a time
        'DOWNLOAD_DELAY': 3,  # Add delay between requests
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super(FeatureSpecificationSpider, self).__init__(*args, **kwargs)
        # Use provided URL or default to a sample URL
        if start_url:
            self.start_urls = [start_url]
        else:
            self.start_urls = ["https://www.carwale.com/mahindra-cars/xuv-3xo/"]

    def start_requests(self):
        for index, url in enumerate(self.start_urls, 1):
            self.logger.info(f"Processing URL {index}/{len(self.start_urls)}: {url}")
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=20,
                screenshot=True,
                dont_filter=True,
                meta={
                    'dont_cache': True,
                    'url_index': index,
                    'total_urls': len(self.start_urls)
                }
            )

    def parse(self, response):
        url_index = response.meta.get('url_index', 0)
        total_urls = response.meta.get('total_urls', 0)
        current_url = response.url

        self.logger.info(f"=" * 80)
        self.logger.info(f"PARSING URL {url_index}/{total_urls}: {current_url}")
        self.logger.info(f"=" * 80)

        driver = response.meta.get("driver")
        if not driver:
            self.logger.error(f"WebDriver not found in response for URL: {current_url}")
            return

        try:
            # Get car name
            car_name_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'o-j6')]"))
            )
            car_name = car_name_elem.text.strip()
            car_parts = car_name.split()

            # Extract brand name (first word)
            brand_name = car_parts[0] if len(car_parts) > 0 else ""

            # Extract model name (second word)
            model_name = car_parts[1] if len(car_parts) > 1 else ""

            # Extract variant name (all remaining words after the model name)
            variant_name = " ".join(car_parts[2:]) if len(car_parts) > 2 else ""

            self.logger.info(f"Car: {car_name}")
            self.logger.info(f"Brand: {brand_name}, Model: {model_name}, Variant: {variant_name}")

            # Click on Specs & Features tab
            try:
                specs_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//ul[contains(@class, 'o-f')]/li//div/span[div[text()='Specs & Features']]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", specs_tab)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", specs_tab)
                time.sleep(3)  # Wait for tab to load

            except Exception as e:
                self.logger.error(f"Error clicking Specs tab: {e}")

            # Extract specifications
            spec_items = self.extract_specifications(driver, model_name, variant_name)
            for item in spec_items:
                yield item

            # Extract features
            feature_items = self.extract_features(driver, model_name, variant_name)
            for item in feature_items:
                yield item

            self.logger.info(f"Completed processing URL {url_index}/{total_urls}: {current_url}")
            self.logger.info(f"Extracted {len(spec_items)} specifications and {len(feature_items)} features")

        except Exception as e:
            self.logger.error(f"[ERROR] Error in main parse for URL {current_url}: {e}")

    def extract_specifications(self, driver, model_name, variant_name):
        """Extract specifications data from the page"""
        all_specs = []

        try:
            # First try to find the main container directly
            main_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'o-mO o-m3')]"))
            )

            # Find all section li elements
            section_elements = WebDriverWait(main_container, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, ".//li[contains(@class, 'o-kY')]"))
            )

            self.logger.info(f"Found {len(section_elements)} specification sections")

            # Process each section
            for section_index, section in enumerate(section_elements):
                try:
                    # Scroll section into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)
                    time.sleep(1)

                    # Extract category name
                    try:
                        category_elem = section.find_element(By.XPATH, ".//p[contains(@class, 'o-jq')]")
                        category = category_elem.text.strip()
                        self.logger.info(f"Processing section {section_index+1}/{len(section_elements)}: {category}")
                    except Exception as e:
                        self.logger.error(f"Error getting category name: {e}")
                        category = f"Section {section_index+1}"

                    # Find content div - the one with class la6Zqh
                    try:
                        content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'kgwwPb')]")
                        aria_hidden = content_div.get_attribute("aria-hidden")
                        self.logger.info(f"Section '{category}' aria-hidden: {aria_hidden}")

                        # If collapsed, expand it
                        if aria_hidden == "true":
                            try:
                                # Find and click toggle button
                                toggle_btn = section.find_element(By.XPATH, ".//div[contains(@class, 'o-f7')]")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle_btn)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", toggle_btn)
                                time.sleep(2)

                                # Re-fetch content div after expansion
                                content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'kgwwPb')]")
                            except Exception as e:
                                self.logger.error(f"Error expanding section '{category}': {e}")

                        # CRITICAL FIX: Force content div to be visible via JavaScript
                        driver.execute_script("""
                            arguments[0].style.height = 'auto';
                            arguments[0].style.overflow = 'visible';
                            arguments[0].setAttribute('aria-hidden', 'false');
                        """, content_div)

                        # CRITICAL FIX: Find all rows using direct descendant XPaths
                        # First, ensure we have the inner div and ul elements
                        inner_div = content_div.find_element(By.XPATH, "./div")
                        inner_ul = inner_div.find_element(By.XPATH, "./ul")

                        # Get all li elements (each represents a specification row)
                        row_items = inner_ul.find_elements(By.XPATH, "./li")
                        self.logger.info(f"Found {len(row_items)} rows in '{category}'")

                        # Process each row
                        for row_index, row_item in enumerate(row_items):
                            try:
                                # Try to find title and value directly in the row
                                title = None
                                value = None

                                # Try multiple methods to extract data
                                try:
                                    # Method 1: Try with data-itemid structure (original)
                                    item_div = row_item.find_element(By.XPATH, "./div[@data-itemid]")
                                    data_div = item_div.find_element(By.XPATH, "./div")
                                    title_div = data_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]")
                                    title = title_div.text.strip()
                                    value_div = data_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]")
                                    value = value_div.text.strip()
                                except:
                                    # Method 2: Try direct search for title and value in row
                                    try:
                                        title_div = row_item.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]")
                                        title = title_div.text.strip()
                                        value_div = row_item.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]")
                                        value = value_div.text.strip()
                                    except:
                                        # Method 3: Try alternative class patterns
                                        try:
                                            # Some items might have different structure
                                            all_divs = row_item.find_elements(By.XPATH, ".//div")
                                            if len(all_divs) >= 2:
                                                # Try to find title and value from text content
                                                texts = [div.text.strip() for div in all_divs if div.text.strip()]
                                                if len(texts) >= 2:
                                                    title = texts[0]
                                                    value = texts[1]
                                        except:
                                            continue

                                if title and value:
                                    all_specs.append({
                                        "modelName": model_name,
                                        "makeYear": 2025,
                                        "variantName": variant_name,
                                        "specificationCategoryName": category,
                                        "specificationName": title,
                                        "specificationValue": value,
                                    })
                                    self.logger.info(f"Extracted: {category} - {title}: {value}")
                            except Exception as e:
                                # Skip rows that can't be parsed
                                continue

                    except Exception as e:
                        self.logger.error(f"Error finding content div in '{category}': {e}")
                        continue  # Skip to the next section if we can't find the content div

                except Exception as e:
                    self.logger.error(f"Error with content div in '{category}': {e}")

            self.logger.info(f"Total specifications extracted: {len(all_specs)}")

        except Exception as e:
            self.logger.error(f"[ERROR] Could not extract specifications: {e}")

        return all_specs

    def extract_features(self, driver, model_name, variant_name):
        """Extract features data from the page"""
        all_features = []

        try:
            # Find Features heading
            features_heading = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Features')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", features_heading)
            time.sleep(2)

            # Find the main features container
            features_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Features')]/parent::div/following-sibling::ul"))
            )

            # Find all feature sections
            section_elements = WebDriverWait(features_container, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "./div/li"))
            )

            self.logger.info(f"Found {len(section_elements)} feature sections")

            # Process each feature section
            for section_index, section in enumerate(section_elements):
                try:
                    # Scroll section into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)
                    time.sleep(1)

                    # Get category name
                    try:
                        category_elem = section.find_element(By.XPATH, ".//p[contains(@class, 'o-jq')]")
                        category = category_elem.text.strip()
                        self.logger.info(f"Processing feature section {section_index+1}/{len(section_elements)}: {category}")
                    except Exception as e:
                        self.logger.error(f"Error getting feature category name: {e}")
                        category = f"Feature Section {section_index+1}"

                    # Find content div
                    try:
                        content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'kgwwPb')]")
                        aria_hidden = content_div.get_attribute("aria-hidden")
                        self.logger.info(f"Feature section '{category}' aria-hidden: {aria_hidden}")

                        # If collapsed, expand it
                        if aria_hidden == "true":
                            try:
                                toggle_btn = section.find_element(By.XPATH, ".//div[contains(@class, 'o-f7')]")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle_btn)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", toggle_btn)
                                time.sleep(2)

                                # Re-fetch content div
                                content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'kgwwPb')]")
                            except Exception as e:
                                self.logger.error(f"Error expanding feature section '{category}': {e}")

                        # Force visibility
                        driver.execute_script("""
                            arguments[0].style.height = 'auto';
                            arguments[0].style.overflow = 'visible';
                            arguments[0].setAttribute('aria-hidden', 'false');
                        """, content_div)

                        # Find feature rows - using li elements
                        try:
                            inner_div = content_div.find_element(By.XPATH, "./div")
                            inner_ul = inner_div.find_element(By.XPATH, "./ul")

                            row_items = inner_ul.find_elements(By.XPATH, "./li")
                            self.logger.info(f"Found {len(row_items)} feature rows in '{category}'")

                            for row_item in row_items:
                                try:
                                    # Try to find title and value directly in the row
                                    title = None
                                    value = None

                                    # Try multiple methods to extract data
                                    try:
                                        # Method 1: Try with data-itemid structure (original)
                                        item_div = row_item.find_element(By.XPATH, "./div[@data-itemid]")
                                        data_div = item_div.find_element(By.XPATH, "./div")
                                        title_div = data_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]")
                                        title = title_div.text.strip()

                                        # For features, the value is often Yes/No or present/absent
                                        try:
                                            value_div = data_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]")
                                            value = value_div.text.strip()
                                        except:
                                            # If no specific value, feature is present (Yes)
                                            value = "Yes"
                                    except:
                                        # Method 2: Try direct search for title and value in row
                                        try:
                                            title_div = row_item.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]")
                                            title = title_div.text.strip()
                                            try:
                                                value_div = row_item.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]")
                                                value = value_div.text.strip()
                                            except:
                                                value = "Yes"
                                        except:
                                            # Method 3: Try alternative class patterns
                                            try:
                                                # Some items might have different structure
                                                all_divs = row_item.find_elements(By.XPATH, ".//div")
                                                if len(all_divs) >= 2:
                                                    # Try to find title and value from text content
                                                    texts = [div.text.strip() for div in all_divs if div.text.strip()]
                                                    if len(texts) >= 1:
                                                        title = texts[0]
                                                        value = texts[1] if len(texts) >= 2 else "Yes"
                                            except:
                                                continue

                                    if title:
                                        all_features.append({
                                            "modelName": model_name,
                                            "makeYear": 2025,
                                            "variantName": variant_name,
                                            "featureCategoryName": category,
                                            "featureName": title,
                                            "featureValue": value,
                                            "featureIsHighlighted": "",
                                        })
                                        self.logger.info(f"Extracted feature: {category} - {title}: {value}")
                                except Exception as e:
                                    # Skip rows that can't be parsed
                                    continue
                        except Exception as e:
                            self.logger.error(f"Error finding feature rows: {e}")
                    except Exception as e:
                        self.logger.error(f"Error with feature content div: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing feature section {section_index}: {e}")

            self.logger.info(f"Total features extracted: {len(all_features)}")

        except Exception as e:
            self.logger.error(f"[ERROR] Could not extract features: {e}")

        return all_features
