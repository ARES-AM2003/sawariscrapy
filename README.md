
# Scrapy-Selenium Starter Kit 🕷️💻

Welcome to the **Scrapy-Selenium Starter Kit**! This project combines the power of **Scrapy** for web scraping with **Selenium** for dynamic content rendering. Whether you're scraping static pages or handling JavaScript-heavy websites, this kit has you covered.

## 📦 Features
- **Scrapy** for efficient web scraping
- **Selenium** integration to handle JavaScript-heavy websites
- Pre-configured **Firefox** and **Chrome** WebDriver setup
- Easily customizable spider templates
- Caching and HTTP handling

## 🚀 Setup Guide

### 1. Clone the repository

Clone the repository to your local machine:

```bash
git clone git@github.com:ARES-AM2003/Scrapy-selenium-kit.git
```

### 2. Rename the project folder

Rename the folder to your desired project name:

```bash
mv  Project_name newProjectName
```

### 3. Create a virtual environment

Create a virtual environment to isolate dependencies:

For **Linux/MacOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

For **Windows**:
```bash
python -m venv venv
venv\Scriptsctivate
```

### 4. Install dependencies

Install the required dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This will install **Scrapy**, **Selenium**, **webdriver-manager**, and other necessary packages.

### 5. Update project settings

After renaming the project folder, update the respective fields in the following files:

- **scrapy.cfg**:
```ini
[settings]
default = Project_name.settings
to
default = newProjectName.settings
```

- **settings.py**:

```python
# Scrapy settings for Project_name project

BOT_NAME = "Project_name" ->BOT_NAME = "newProjectName"


SPIDER_MODULES = ["Project_name.spiders"]  -> SPIDER_MODULES = ["newProjectName.spiders"]
NEWSPIDER_MODULE = "Project_name.spiders"  -> NEWSPIDER_MODULE = "newProjectName.spiders" 

ADDONS = {}

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0"

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

FEED_EXPORT_ENCODING = "utf-8"

DOWNLOADER_MIDDLEWARES = {
    'newProjectName.middlewares.SeleniumMiddleware': 543,
}

# Retry Mechanism
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 30
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408]

FEEDS = {
    'output/cars.json': {'format': 'json'},  --->    'output/fileName.json': {'format': 'json'},

    'output/cars.csv': {'format': 'csv'},  ---->        'output/fileName.csv': {'format': 'csv'},

}
```

### 6. Update or create a new spider 🕷️

- Customize the spider logic in `Project_name/spiders/cars.py` or create a new spider for your scraping needs.
- Update the `start_urls` and parsing methods to match the structure of the website you're scraping.

Example of customizing the spider:

```python
import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
import time

class CarsSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ["cars24.com"]
    start_urls = ['https://www.cars24.com/buy-used-cars/']

    def start_requests(self):
        yield SeleniumRequest(
            url=self.start_urls[0],
            callback=self.parse,
            wait_time=10,
            wait_until=lambda driver: driver.find_element(By.TAG_NAME, "body"),
        )

    def parse(self, response):
        self.logger.info("Parsing car list page")
        driver = response.meta['driver']

        # Scroll to bottom
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Get car links
        cars = driver.find_elements(By.CSS_SELECTOR, "a[href*='/buy-used-car']")
        self.logger.info(f"Found {len(cars)} cars")

        for car in cars:
            link = car.get_attribute("href")
            if link:
                yield SeleniumRequest(
                    url=link,
                    callback=self.parse_car_detail,
                    wait_time=10,
                    wait_until=lambda d: d.find_element(By.TAG_NAME, "body"),
                )

    def parse_car_detail(self, response):
        driver = response.meta['driver']
        self.logger.info(f"Parsing car detail: {response.url}")

        def safe_text(by, value):
            try:
                return driver.find_element(by, value).text
            except:
                return None

        yield {
            "brand": safe_text(By.CSS_SELECTOR, ".brand-name"),
            "model": safe_text(By.CSS_SELECTOR, ".model-name"),
            "year": safe_text(By.XPATH, "//span[contains(text(),'Year')]/following-sibling::span"),
            "fuel_type": safe_text(By.XPATH, "//span[contains(text(),'Fuel')]/following-sibling::span"),
            "mileage": safe_text(By.XPATH, "//span[contains(text(),'Mileage')]/following-sibling::span"),
            "engine": safe_text(By.XPATH, "//span[contains(text(),'Engine')]/following-sibling::span"),
            "features": [el.text for el in driver.find_elements(By.CSS_SELECTOR, ".feature-item")],
            "price": safe_text(By.CSS_SELECTOR, ".price"),
            "url": response.url,
        }
```

### 7. Run the spider 🏃‍♂️

Once your spider is set up, run it with the following command:

```bash
scrapy crawl cars
```

This will start the scraping process, and the results will be saved in the format specified in your settings (typically JSON or CSV).

---

## 💡 Tips

- Ensure that **WebDriver** (Firefox or Chrome) is correctly installed before running the scraper.
- Check for **page load times** and increase `wait_time` in the `SeleniumRequest` if necessary to avoid incomplete page loads.
- Use **headless mode** for faster scraping by using the `--headless` flag.

## ⚙️ Tools & Technologies

- [Scrapy](https://scrapy.org/) 🐍
- [Selenium](https://www.selenium.dev/) 🔧
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager) ⚙️
- [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) & [GeckoDriver](https://github.com/mozilla/geckodriver) 🏎️

## 🔗 Links

- [Scrapy Documentation](https://docs.scrapy.org/en/latest/)
- [Selenium Documentation](https://www.selenium.dev/documentation/en/)
- [WebDriver Manager GitHub](https://github.com/SergeyPirogov/webdriver_manager)



Happy scraping! 🎉 If you have any questions or suggestions, feel free to [open an issue](https://github.com/ARES-AM2003/Scrapy-selenium-kit/issues).
# scrapy
# sawari-Scrape
# sawariscrapy
