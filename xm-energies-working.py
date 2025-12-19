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
        # Wait for the green button often used for cookie consent
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie"))
        )
        accept_button.click()
        print("Modal dismissed successfully.")
        time.sleep(1) # Wait for animation
    except TimeoutException:
        print("No blocking modal appeared.")

def scrape_xm_energies():
    url = "https://www.xmtrading.com/jp/energies"
    options = Options()
    # options.add_argument("--headless") # Run without GUI for efficiency
    
    driver = webdriver.Chrome(options=options)
    all_extracted_data = []

    try:
        driver.get(url)
        print(f"Opening XM Energies: {url}...")

        # Clear modal as it can intercept clicks
        handle_blocking_modal(driver)

        # Wait for the main table element
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))

        # Expand entries to 100 to capture all available energy products
        try:
            length_menu = driver.find_element(By.NAME, "DataTables_Table_0_length")
            length_menu.send_keys("100")
            time.sleep(2) 
        except Exception as e:
            print(f"Note: Could not change table length ({e}), proceeding with default view.")

        # Find all rows in the table body
        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        print(f"Scanning all {len(rows)} rows found in the table...\n")

        for row in rows:
            try:
                # Target symbols like BRENTCash, NGASCash, and OILCash
                symbol_text = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='symbol']").text.strip()
                
                # Extract Long and Short values using the specific QA attributes
                long_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").text.strip()
                short_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").text.strip()
                
                if symbol_text: 
                    all_extracted_data.append({
                        "Symbol": symbol_text,
                        "ロング (Long)": long_swap,
                        "ショート (Short)": short_swap
                    })
            except Exception:
                # Skip header or empty rows
                continue

        # Render results to console
        df = pd.DataFrame(all_extracted_data)
        print("--- EXTRACTED XM ENERGIES DATA ---")
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal energy products found: {len(all_extracted_data)}")
        else:
            print("No data extracted. Verify table structure.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_xm_energies()