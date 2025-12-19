import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_xm_metals():
    url = "https://www.xmtrading.com/jp/precious-metals"
    options = Options()
    # options.add_argument("--headless") # Uncomment to run without a visible browser
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        print(f"Opening: {url}")
        
        # 1. Handle the Cookie Modal (Green "全てを許可する" button)
        # The button has the class 'js-acceptDefaultCookie' as seen in the images
        try:
            wait = WebDriverWait(driver, 10)
            accept_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie")))
            accept_btn.click()
            print("Cookie modal dismissed.")
            time.sleep(1) # Wait for animation to finish
        except Exception:
            print("Cookie modal not found or already closed.")

        # 2. Set Table to Show 100 Entries
        # This ensures all metals are visible on a single page
        try:
            length_menu = driver.find_element(By.NAME, "DataTables_Table_0_length")
            length_menu.send_keys("100")
            time.sleep(2)
        except Exception:
            print("Note: Could not change table length, proceeding with default view.")

        # 3. Locate and Scrape the Table
        # Using the exact data-xm-qa-name attributes found in your images
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        
        print("\n--- Precious Metals Swap Points ---")
        print(f"{'Symbol':<15} {'Long Swap':<15} {'Short Swap':<15}")
        print("-" * 45)

        for row in rows:
            try:
                # Use standard data attributes from the XM Trading table structure
                symbol = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='currencyPair']").text.strip()
                long_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").text.strip()
                short_swap = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").text.strip()
                
                print(f"{symbol:<15} {long_swap:<15} {short_swap:<15}")
            except Exception:
                # Skip header rows or decorative elements that don't match the format
                continue

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_xm_metals()