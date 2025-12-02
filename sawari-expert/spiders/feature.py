import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time


class FeaturesSpider(scrapy.Spider):
    name = "features"
    allowed_domains = ["carwale.com"]
    start_urls = ["https://www.carwale.com/hyundai-cars/creta/sx-15-petrol/"]
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'sawari-expert.pipelines.FeatureInfoJsonPipeline': 300,
            'sawari-expert.pipelines.FeatureInfoCsvPipeline': 400,
        }
    }

    # instead of start_requests, we use SeleniumRequest to handle JavaScript
    def start_requests(self):
        yield SeleniumRequest(
            url=self.start_urls[0],
            callback=self.parse,
            wait_time=20,
            screenshot=True,
            dont_filter=True,
            meta={'dont_cache': True}
        )

    def parse(self, response):
        driver = response.meta.get("driver")

        # Log to check if driver is initialized
        if driver:
            self.logger.info("[LOG] WebDriver initialized: %s", driver.session_id)
        else:
            self.logger.error("[ERROR] WebDriver not found in response.meta")

        # If driver is not initialized, stop the process
        if not driver:
            return
        
        # Find the <h1> with the car name
        try:
            car_name_elem = driver.find_element(By.XPATH, "//h1[contains(@class, 'o-j6') and contains(@data-lang-id, 'car_overview_heading')]")
            car_name = car_name_elem.text.strip()
            model_name = car_name.split()[1] if car_name else ""
            variant_name = car_name.split()[2] if len(car_name.split()) > 2 else ""

        except Exception as e:
            car_name = ""
            self.logger.error(f"[ERROR] Could not extract car name: {e}")

        # Find the <div> with text 'Specs & Features' and click it
        try:
            specs_tab = driver.find_element(
                By.XPATH,
                "//ul[contains(@class, 'o-f')]/li//div/span[div[text()='Specs & Features']]"
            )
            time.sleep(2)  # Wait for the element to be clickable
            specs_tab.click()
            print("Clicked 'Specs & Features' tab.")
        except Exception as e:
            self.logger.error(f"[ERROR] Could not click 'Specs & Features' tab: {e}")

        # Try to remove ALL obstructing elements before processing sections
        try:
            # List of common obstructing element classes
            obstructing_elements = [
                "//button[contains(@class, 'ticker-cta-container-1')]",
                "//div[contains(@class, 'model-ticker__wrapper')]",
                "//div[contains(@class, 'ticker')]",
                "//div[contains(@class, 'popup')]",
                "//div[contains(@class, 'banner')]",
                "//div[contains(@class, 'sticky')]"
            ]
            
            for xpath in obstructing_elements:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        driver.execute_script("arguments[0].remove();", element)
                    if elements:
                        print(f"Removed {len(elements)} obstructing elements matching: {xpath}")
                except Exception:
                    continue
        except Exception as e:
            print(f"Error while removing obstructing elements: {e}")

        try:
            # Find the Features heading first
            features_heading = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[text()='Features']"))
            )
            
            # Scroll to the Features section
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", features_heading)
            time.sleep(1)
            
            # Find the <div> containing <h3>Features</h3>
            features_div = driver.find_element(By.XPATH, "//div[h3[text()='Features']]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", features_div)
            # The <ul> is the next sibling of this <div>
            feature_ul = features_div.find_element(By.XPATH, "following-sibling::ul[1]")
            num_sections = len(feature_ul.find_elements(By.XPATH, "./div/li"))
            all_features = []

            print(f"Found {num_sections} feature categories")
            
            for i in range(num_sections):
                # Always re-fetch the list and the current li
                feature_lis = feature_ul.find_elements(By.XPATH, "./div/li")
                li = feature_lis[i]

                # Get the category name
                try:
                    category = li.find_element(By.XPATH, ".//p").text.strip()
                except Exception:
                    category = ""

                # Find the content container for this category
                try:
                    content_div = li.find_element(By.XPATH, ".//div[contains(@class, 'la6Zqh')]")
                    aria_hidden = content_div.get_attribute("aria-hidden")
                    if aria_hidden == "true":
                        # Section is collapsed, click the arrow to expand
                        try:
                            toggle_btn = li.find_element(By.XPATH, ".//div[contains(@class, 'o-f7')]")
                            # Scroll the element into center view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle_btn)
                            time.sleep(1)
                            # Use JavaScript click instead of regular click
                            driver.execute_script("arguments[0].click();", toggle_btn)
                            print(f"Expanded section: {category}")
                            time.sleep(2)
                            # After expanding, re-fetch everything for this index
                            feature_lis = feature_ul.find_elements(By.XPATH, "./div/li")
                            li = feature_lis[i]
                            content_div = li.find_element(By.XPATH, ".//div[contains(@class, 'la6Zqh')]")
                        except Exception as e:
                            self.logger.error(f"[ERROR] Could not expand section '{category}': {e}")
                            continue
                except Exception as e:
                    self.logger.error(f"[ERROR] Could not find content div for '{category}': {e}")
                    continue

                # Now extract rows only if visible
                try:
                    rows = content_div.find_elements(By.XPATH, ".//div[contains(@class, 'o-aE')]")
                    for row in rows:
                        try:
                            title = row.find_element(By.XPATH, ".//div[contains(@class, 'o-jK')]").text.strip()
                            value = row.find_element(By.XPATH, ".//div[contains(@class, 'o-jJ')]").text.strip()
                            all_features.append({
                                "category": category,
                                "title": title,
                                "value": value
                            })
                        except Exception:
                            continue
                except Exception:
                    continue

            # Debug print
            print(f"Extracted {len(all_features)} features")

        except Exception as e:
            self.logger.error(f"[ERROR] Could not extract features: {e}")

        for feature in all_features:
            yield {
                "modelName": model_name,
                "makeYear": " ",
                "variantName": variant_name,
                "featureCategoryName": feature["category"],
                "featureName": feature["title"],
                "featureValue": feature["value"],
            }

