import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def handle_blocking_modal(driver):
    """Wait for and click the 'Accept All' green button on the cookie modal."""
    print("Checking for blocking modal...")
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie"))
        )
        accept_button.click()
        print("Modal dismissed successfully.")
        time.sleep(1) 
    except TimeoutException:
        print("No blocking modal appeared within timeout period.")

def scrape_xm_forex_render():
    url = "https://www.xmtrading.com/jp/forex-trading"
    options = Options()
    # options.add_argument("--headless") 
    
    driver = webdriver.Chrome(options=options)
    all_extracted_data = []

    try:
        driver.get(url)
        print(f"Opening XM Forex: {url}...")

        handle_blocking_modal(driver)

        # Wait for the table to load
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))

        # Set 'Show entries' to 100 to capture all pairs on one page
        try:
            length_menu = driver.find_element(By.NAME, "DataTables_Table_0_length")
            length_menu.send_keys("100")
            time.sleep(2) 
        except:
            print("Note: Could not change table length, proceeding with default view.")

        # Find all rows in the table body
        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        print(f"Scanning all {len(rows)} rows found in the table...\n")

        for row in rows:
            try:
                # Dynamically fetch values from specific QA attributes for every row
                symbol_text = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='currencyPair']").text.strip()
                long_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").text.strip()
                short_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").text.strip()
                
                if symbol_text: # Ensure the symbol name is not empty
                    all_extracted_data.append({
                        "Symbol": symbol_text,
                        "ロング (Long)": long_swap,
                        "ショート (Short)": short_swap
                    })
            except:
                continue

        # Render all results to console
        df = pd.DataFrame(all_extracted_data)
        print("--- EXTRACTED ALL XM FOREX DATA ---")
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal symbols found and extracted: {len(all_extracted_data)}")
        else:
            print("No data extracted. Verify table structure.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_xm_forex_render()