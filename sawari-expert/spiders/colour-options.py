import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ColourOptionsSpider(scrapy.Spider):
    name = "colour-options"
    allowed_domains = ["cardekho.com"]
    start_urls = ["https://www.cardekho.com/honda/elevate"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'sawari-expert.pipelines.ColourOptionsInfoJsonPipeline': 300,
            'sawari-expert.pipelines.ColourOptionsInfoCsvPipeline': 400,
        }
    }

    # Custom settings for output files
    # This will save the output in JSON and CSV formats in the specified directory
#     custom_settings = {
#         'FEEDS': {
#             'output/model-sheet/modelInfo.json': {
#                 'format': 'json',
#                 'indent': 4,  # This makes the JSON pretty!
#                 'overwrite': True,  # Overwrite existing file
#             },
#             'output/model-sheet/modelInfo.csv': {'format': 'csv'},
#         }
# }

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
            model_name_elem = driver.find_element(By.XPATH, "//a[ contains(@title, 'Overview')]")
            model_name = model_name_elem.text.strip()

        except Exception as e:
            brand_name = model_name = ""
            print(f"[ERROR] Could not extract car name info: {e}")

        # Scroll to the colour section
        try:
           # Select all color option <li> elements
            color_option_elements = driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'gscr_dot')]"
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", color_option_elements[0])

        except Exception as e:
            body_type = ""
            print(f"[ERROR] Could not extract body type: {e}")

        # Extract color options: name and hex code
        colors = []
        try:
            color_option_elements = driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'gscr_dot')]"
            )
            for li in color_option_elements:
                # Extract color name from <a> title
                try:
                    color_name = li.find_element(By.XPATH, ".//a").get_attribute("title")
                except Exception:
                    color_name = ""
                # Extract style from <i> (coloredIcon)
                try:
                    icon_elem = li.find_element(By.XPATH, ".//i[contains(@class, 'coloredIcon')]")
                    style = icon_elem.get_attribute("style")
                    import re
                    match = re.search(r"(rgb[a]?\([^)]+\)|#[0-9a-fA-F]{3,6})", style)
                    color_hex = match.group(1) if match else style
                except Exception:
                    color_hex = ""
                # Yield one item per color!
                yield {
                    "modelName": model_name,
                    "colourName": color_name,
                    "hexCode": color_hex
                }
        except Exception as e:
            print(f"[ERROR] Could not extract color options: {e}")
