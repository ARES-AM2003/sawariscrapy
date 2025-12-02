import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import re
import time


class SpecificationsSpider(scrapy.Spider):
    name = "specifications"
    allowed_domains = ["carwale.com"]
    start_urls = ["https://www.carwale.com/hyundai-cars/venue/e-12-petrol/"]
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'sawari-expert.pipelines.SpecificationInfoJsonPipeline': 300,
            'sawari-expert.pipelines.SpecificationInfoCsvPipeline': 400,
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=10,
                screenshot=True,
                dont_filter=True
            )

    def parse(self, response):
        driver = response.meta.get("driver")
        if not driver:
            self.logger.error("WebDriver not found in response")
            return
            
        try:
            # Get car name
            car_name_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'o-j6')]"))
            )
            car_name = car_name_elem.text.strip()
            model_name = car_name.split()[1] if len(car_name.split()) > 1 else ""
            variant_name = car_name.split()[2] if len(car_name.split()) > 2 else ""
            
            self.logger.info(f"Car: {car_name}")
            
            # Click on Specs & Features tab
            try:
                specs_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//ul[contains(@class, 'o-f')]/li//div/span[div[text()='Specs & Features']]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", specs_tab)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", specs_tab)
                time.sleep(3)  # Increased wait time
                
                # Take a screenshot for debugging
                driver.save_screenshot("specs_tab_clicked.png")
            except Exception as e:
                self.logger.error(f"Error clicking Specs tab: {e}")
        
            # Find the main specifications container
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
                
                all_specs = []
                
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
                            content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'la6Zqh')]")
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
                                    content_div = section.find_element(By.XPATH, ".//div[contains(@class, 'la6Zqh')]")
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
                            
                            # Get all immediate div children which can be of different types
                            row_containers = inner_ul.find_elements(By.XPATH, "./div")
                            self.logger.info(f"Found {len(row_containers)} potential rows in '{category}'")
                            
                            # Process each row container
                            for row_index, row_container in enumerate(row_containers):
                                try:
                                    # Check if this is a row or just a container
                                    if "o-cE" in row_container.get_attribute("class"):
                                        # This is the "Report incorrect specifications" div, skip it
                                        continue
                                    
                                    # Find the actual row div - handle both direct and nested cases
                                    row_div = None
                                    try:
                                        # Try direct data-itemid case
                                        if row_container.get_attribute("data-itemid"):
                                            row_div = row_container.find_element(By.XPATH, "./div")
                                        else:
                                            # Try class o-C case (nested)
                                            inner_div = row_container.find_element(By.XPATH, "./div")
                                            row_div = inner_div.find_element(By.XPATH, "./div")
                                    except:
                                        # Try finding any div with o-aE class
                                        try:
                                            row_div = row_container.find_element(By.XPATH, ".//div[contains(@class, 'o-aE')]")
                                        except:
                                            continue
                                    
                                    if row_div:
                                        # Extract title and value
                                        try:
                                            title_div = row_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]")
                                            title = title_div.text.strip()
                                            
                                            value_div = row_div.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]")
                                            value = value_div.text.strip()
                                            
                                            if title and value:
                                                all_specs.append({
                                                    "category": category,
                                                    "title": title, 
                                                    "value": value
                                                })
                                                self.logger.info(f"Extracted: {category} - {title}: {value}")
                                        except Exception as e:
                                            self.logger.error(f"Error extracting data from row {row_index}: {e}")
                                except Exception as e:
                                    self.logger.error(f"Error processing row container {row_index}: {e}")
                        
                        except Exception as e:
                            self.logger.error(f"Error with content div in '{category}': {e}")
                
                    except Exception as e:
                        self.logger.error(f"Error processing section {section_index}: {e}")
                
                self.logger.info(f"Total specifications extracted: {len(all_specs)}")
                
                # Yield the extracted data
                for spec in all_specs:
                    yield {
                        "modelName": model_name,
                        "makeYear": " ",
                        "variantName": variant_name,
                        "specificationCategoryName": spec["category"],
                        "specificationName": spec["title"],
                        "specificationValue": spec["value"],
                    }
                    
            except Exception as e:
                self.logger.error(f"Error finding main container: {e}")
    
        except Exception as e:
            self.logger.error(f"[ERROR] Could not extract specifications: {e}")

