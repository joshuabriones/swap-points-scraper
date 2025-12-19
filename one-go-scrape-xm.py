import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def handle_blocking_modal(driver):
    """Dismisses the green XM cookie modal if it appears."""
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie"))
        )
        accept_button.click()
        time.sleep(1) 
    except TimeoutException:
        pass

def scrape_standard_format(driver, category, url, name_attr):
    """Extraction method for Forex, Indices, Metals, and Energies."""
    print(f"Scraping {category}...")
    driver.get(url)
    handle_blocking_modal(driver)
    
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))

    # Ensure 100 entries are shown
    try:
        length_menu = driver.find_element(By.NAME, "DataTables_Table_0_length")
        length_menu.send_keys("100")
        time.sleep(2) 
    except: pass

    data = []
    rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
    for row in rows:
        try:
            # Dynamically target symbol/currencyPair based on the page
            symbol = row.find_element(By.CSS_SELECTOR, f"td[data-xm-qa-name='{name_attr}']").text.strip()
            long_v = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").text.strip()
            short_v = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").text.strip()
            if symbol:
                data.append({"Category": category, "Symbol": symbol, "Long": long_v, "Short": short_v})
        except: continue
    return data

def scrape_crypto_format(driver):
    """Specific extraction method for the dynamic Crypto page."""
    url = "https://xem.fxsignup.com/trade/crypto-cfds.html"
    print("Scraping Crypto...")
    driver.get(url)
    
    # Expand table if 'More' button exists
    try:
        expand_btn = driver.find_element(By.CSS_SELECTOR, "div.toggleBtnTable")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_btn)
        time.sleep(1)
        expand_btn.click()
        time.sleep(3)
    except: pass

    # Wait specifically for numbers to populate in the span
    wait = WebDriverWait(driver, 30)
    wait.until(lambda d: "." in d.find_element(By.CSS_SELECTOR, "span[data-id^='1INCHUSD-data']").get_attribute("textContent"))

    data = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table.tableCommon03 tbody tr")
    for row in rows:
        try:
            symbol = row.find_element(By.CSS_SELECTOR, "td.tc").get_attribute("textContent").strip()
            if not symbol or "商品/銘柄" in symbol: continue
            
            # Target data-id spans specific to this HTML
            long_v = row.find_element(By.CSS_SELECTOR, "span[data-id$='data01']").get_attribute("textContent").strip()
            short_v = row.find_element(By.CSS_SELECTOR, "span[data-id$='data02']").get_attribute("textContent").strip()
            data.append({"Category": "Crypto", "Symbol": symbol, "Long": long_v, "Short": short_v})
        except: continue
    return data

def run_master_scraper():
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    # The 'One big storage'
    master_data_list = []

    try:
        # Define categories that use the standard table structure
        standard_tasks = [
            ("Forex", "https://www.xmtrading.com/jp/forex-trading", "currencyPair"),
            ("Indices", "https://www.xmtrading.com/jp/equity-indices", "symbol"),
            ("Metals", "https://www.xmtrading.com/jp/precious-metals", "currencyPair"),
            ("Energies", "https://www.xmtrading.com/jp/energies", "symbol")
        ]

        # 1. Run standard structured pages
        for cat, url, attr in standard_tasks:
            master_data_list.extend(scrape_standard_format(driver, cat, url, attr))

        # 2. Run the uniquely structured Crypto page
        master_data_list.extend(scrape_crypto_format(driver))

        # 3. CONSOLIDATED PRINT
        df = pd.DataFrame(master_data_list)
        print("\n" + "="*60)
        print("CONSOLIDATED XM DATA RENDER")
        print("="*60)
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal Records: {len(df)}")
        else:
            print("No data captured. Verify connection.")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_master_scraper()