#!/usr/bin/env python3
"""
Test script to inspect CarWale HTML structure for specifications and features
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time

def test_carwale_structure():
    # Setup Firefox options
    firefox_options = Options()
    # firefox_options.add_argument('--headless')  # Comment out to see browser
    
    # Initialize driver
    driver = webdriver.Firefox(options=firefox_options)
    
    try:
        # Navigate to test URL
        url = "https://www.carwale.com/honda-cars/elevate/v-mt/"
        print(f"Loading URL: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get car name
        print("\n=== Checking Car Name ===")
        try:
            car_name = driver.find_element(By.XPATH, "//h1")
            print(f"Car name found: {car_name.text}")
        except Exception as e:
            print(f"Error finding car name: {e}")
        
        # Check for Specs & Features tab
        print("\n=== Checking Specs & Features Tab ===")
        try:
            # Try multiple patterns for the tab
            patterns = [
                "//ul[contains(@class, 'o-f')]/li//div/span[div[text()='Specs & Features']]",
                "//div[contains(text(), 'Specs & Features')]",
                "//span[contains(text(), 'Specs & Features')]",
                "//button[contains(text(), 'Specs & Features')]",
                "//*[contains(text(), 'Specs & Features')]"
            ]
            
            for pattern in patterns:
                try:
                    elements = driver.find_elements(By.XPATH, pattern)
                    if elements:
                        print(f"Found {len(elements)} elements with pattern: {pattern}")
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            print(f"  Element {i+1}: tag={elem.tag_name}, classes={elem.get_attribute('class')}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Error finding Specs tab: {e}")
        
        # Look for specifications sections
        print("\n=== Checking Specifications Structure ===")
        try:
            # Try to find specification sections by text
            spec_headers = driver.find_elements(By.XPATH, "//*[contains(text(), 'Specifications')]")
            print(f"Found {len(spec_headers)} 'Specifications' headers")
            
            # Look for common section patterns
            spec_sections = driver.find_elements(By.XPATH, "//h3 | //h4 | //div[@role='heading']")
            print(f"Found {len(spec_sections)} potential section headers")
            for i, section in enumerate(spec_sections[:10]):
                text = section.text.strip()
                if text:
                    print(f"  Section {i+1}: {text[:50]}")
        except Exception as e:
            print(f"Error finding specification sections: {e}")
        
        # Check for specification items (key-value pairs)
        print("\n=== Checking Specification Items ===")
        try:
            # Try to find spec items by looking for common patterns
            patterns = [
                "//li[contains(@class, 'o-kY')]",
                "//div[contains(@class, 'spec-item')]",
                "//div[contains(@class, 'specification')]",
                "//li[@data-itemid]",
            ]
            
            for pattern in patterns:
                try:
                    items = driver.find_elements(By.XPATH, pattern)
                    if items:
                        print(f"Found {len(items)} items with pattern: {pattern}")
                        if items:
                            # Show structure of first item
                            first_item = items[0]
                            print(f"  First item HTML preview: {first_item.get_attribute('outerHTML')[:200]}")
                except:
                    continue
        except Exception as e:
            print(f"Error finding spec items: {e}")
        
        # Check for features section
        print("\n=== Checking Features Structure ===")
        try:
            feature_headers = driver.find_elements(By.XPATH, "//*[contains(text(), 'Features')]")
            print(f"Found {len(feature_headers)} 'Features' headers")
            
            for i, header in enumerate(feature_headers[:3]):
                print(f"  Header {i+1}: tag={header.tag_name}, text={header.text[:50]}, classes={header.get_attribute('class')}")
        except Exception as e:
            print(f"Error finding features: {e}")
        
        # Dump part of page source for analysis
        print("\n=== Page Source Sample (first 2000 chars) ===")
        page_source = driver.page_source
        print(page_source[:2000])
        
        # Save full HTML for offline analysis
        with open('/tmp/carwale_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("\nFull page HTML saved to: /tmp/carwale_page.html")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_carwale_structure()