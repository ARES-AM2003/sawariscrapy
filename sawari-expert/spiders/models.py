import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ModelsSpider(scrapy.Spider):
    name = "models"
    allowed_domains = ["autocarindia.com"]
    start_urls = ["https://www.autocarindia.com/cars/hyundai/ioniq-5"]

    custom_settings = {
    'ITEM_PIPELINES': {
        'sawari-expert.pipelines.ModelInfoJsonPipeline': 300,
        'sawari-expert.pipelines.ModelInfoCsvPipeline': 400,
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

        print(f"[LOG] WebDriver found in response.meta: {driver}")
        print(f"[LOG] WebDriver session ID: {driver.session_id}")  # Log session ID

        # Extract brand and model name dynamically from h1
        try:
            car_name_elem = driver.find_element(By.XPATH, "//h1[contains(@class, 'text-display-sm')]")
            car_name_full = car_name_elem.text.strip()  # e.g. "MG Cyberster"
            parts = car_name_full.split()
            brand_name = parts[0] if len(parts) > 0 else ""
            model_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        except Exception as e:
            brand_name = model_name = ""
            print(f"[ERROR] Could not extract car name info: {e}")

        # Scroll to the Body Style section and extract body type
        try:
            body_style_elem = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'flex items-center justify-between py-2 border-border border-b text-sm')]"
                "[.//div[contains(., 'Body Style')]]"
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", body_style_elem)
            body_type = body_style_elem.find_element(
                By.XPATH, ".//div[contains(@class, 'text-button-sm')]"
            ).text.strip()
        except Exception as e:
            body_type = ""
            print(f"[ERROR] Could not extract body type: {e}")

        yield {
            "brandName": brand_name,
            "modelName": model_name,
            "modelTagline": " ",
            "modelIsHiglighted": " ",
            "bodyType": body_type, 
        }