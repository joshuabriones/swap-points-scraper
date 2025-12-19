import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def get_fresh_driver():
    """Initializes a new Chrome driver instance."""
    options = Options()
    # options.add_argument("--headless") # Uncomment if you don't want to see the window
    driver = webdriver.Chrome(options=options)
    return driver

def handle_blocking_modal(driver):
    """Dismisses the green XM cookie modal."""
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie"))
        )
        accept_button.click()
        time.sleep(1) 
    except TimeoutException:
        pass

def scrape_standard_category(category, url, name_attr):
    """Scrapes Forex, Indices, Metals, and Energies by opening a fresh browser."""
    print(f"--- Processing {category} ---")
    driver = get_fresh_driver()
    data = []
    try:
        driver.get(url)
        handle_blocking_modal(driver)
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))

        # Expand entries
        try:
            length_menu = driver.find_element(By.NAME, "DataTables_Table_0_length")
            length_menu.send_keys("100")
            time.sleep(1.5) 
        except: pass

        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        for row in rows:
            try:
                symbol = row.find_element(By.CSS_SELECTOR, f"td[data-xm-qa-name='{name_attr}']").text.strip()
                long_v = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").text.strip()
                short_v = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").text.strip()
                if symbol:
                    data.append({"Category": category, "Symbol": symbol, "Long": long_v, "Short": short_v})
            except: continue
        print(f"Captured {len(data)} items from {category}.")
    finally:
        driver.quit()
    return data

def scrape_crypto_category():
    """Scrapes the specialized Crypto table by opening a fresh browser."""
    print("--- Processing Crypto ---")
    url = "https://xem.fxsignup.com/trade/crypto-cfds.html"
    driver = get_fresh_driver()
    data = []
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 25)
        
        # Expand table
        try:
            expand_btn = driver.find_element(By.CSS_SELECTOR, "div.toggleBtnTable")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_btn)
            time.sleep(1)
            expand_btn.click()
            time.sleep(2)
        except: pass

        # Wait for numerical data
        wait.until(lambda d: "." in d.find_element(By.CSS_SELECTOR, "span[data-id^='1INCHUSD-data']").get_attribute("textContent"))

        rows = driver.find_elements(By.CSS_SELECTOR, "table.tableCommon03 tbody tr")
        for row in rows:
            try:
                symbol = row.find_element(By.CSS_SELECTOR, "td.tc").get_attribute("textContent").strip()
                if not symbol or "商品/銘柄" in symbol: continue
                
                long_v = row.find_element(By.CSS_SELECTOR, "span[data-id$='data01']").get_attribute("textContent").strip()
                short_v = row.find_element(By.CSS_SELECTOR, "span[data-id$='data02']").get_attribute("textContent").strip()
                data.append({"Category": "Crypto", "Symbol": symbol, "Long": long_v, "Short": short_v})
            except: continue
        print(f"Captured {len(data)} items from Crypto.")
    finally:
        driver.quit()
    return data

def run_consolidated_scraper():
    # Final storage for all values collected
    master_data = []

    # Standard URLs and their specific name attributes
    standard_tasks = [
        ("Forex", "https://www.xmtrading.com/jp/forex-trading", "currencyPair"),
        ("Indices", "https://www.xmtrading.com/jp/equity-indices", "symbol"),
        ("Metals", "https://www.xmtrading.com/jp/precious-metals", "currencyPair"),
        ("Energies", "https://www.xmtrading.com/jp/energies", "symbol")
    ]

    # Collect from standard pages
    for cat, url, attr in standard_tasks:
        master_data.extend(scrape_standard_category(cat, url, attr))

    # Collect from crypto page
    master_data.extend(scrape_crypto_category())

    # --- FINAL RENDER ---
    df = pd.DataFrame(master_data)
    print("\n" + "="*60)
    print("CONSOLIDATED XM DATA RENDER (FRESH BROWSER METHOD)")
    print("="*60)
    if not df.empty:
        print(df.to_string(index=False))
        print(f"\nTotal Records: {len(df)}")
    else:
        print("No data collected.")

if __name__ == "__main__":
    run_consolidated_scraper()