import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def scrape_xm_crypto_direct():
    url = "https://xem.fxsignup.com/trade/crypto-cfds.html"
    options = Options()
    # Note: If it still fails, try commenting out headless mode to debug
    options.add_argument("--headless") 
    
    driver = webdriver.Chrome(options=options)
    scraped_data = []

    try:
        driver.get(url)
        print(f"Opening: {url}")
        wait = WebDriverWait(driver, 30)

        # 1. Expand the 'Show More' button immediately if found
        try:
            expand_btn = driver.find_element(By.CSS_SELECTOR, "div.toggleBtnTable")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_btn)
            time.sleep(1)
            expand_btn.click()
            print("Table expanded.")
            time.sleep(3) # Give extra time for expanded rows to render
        except:
            print("Expand button not found or already open.")

        # 2. WAIT FOR DATA: We wait for any span in the table to contain a decimal point
        print("Waiting for dynamic swap values to load...")
        try:
            # We target a specific common span to check for numerical load
            wait.until(lambda d: "." in d.find_element(By.CSS_SELECTOR, "span[data-id^='1INCHUSD-data']").get_attribute("textContent"))
            print("Values detected!")
        except TimeoutException:
            print("Timeout waiting for values. Attempting to scrape current state...")

        # 3. Locate all rows across all swap tables
        rows = driver.find_elements(By.CSS_SELECTOR, "table.tableCommon03 tbody tr")
        print(f"Processing {len(rows)} rows...")

        for row in rows:
            try:
                # Extract using the data-id spans you provided in your source
                # We use get_attribute('textContent') to bypass empty .text issues
                symbol = row.find_element(By.CSS_SELECTOR, "td.tc").get_attribute("textContent").strip()
                
                # Check if this is a header row or empty
                if not symbol or "商品/銘柄" in symbol:
                    continue

                # Targeting data-id ends with data01 (Long) and data02 (Short)
                long_val = row.find_element(By.CSS_SELECTOR, "span[data-id$='data01']").get_attribute("textContent").strip()
                short_val = row.find_element(By.CSS_SELECTOR, "span[data-id$='data02']").get_attribute("textContent").strip()

                if long_val or short_val:
                    scraped_data.append({
                        "Symbol": symbol,
                        "ロング (Long)": long_val,
                        "ショート (Short)": short_val
                    })
            except:
                continue

        # Render
        df = pd.DataFrame(scraped_data)
        print("\n--- CRYPTO DATA RENDER ---")
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("No data captured. Ensure JavaScript is enabled and not blocked.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_xm_crypto_direct()