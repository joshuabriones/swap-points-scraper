# AXIORY SCRIPT - WORKING VERSION

import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# The exact order you requested
REQUIRED_ORDER = [
    "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "EURUSD", "AUDCHF", "AUDNZD", "AUDSGD", "AUDUSD",
    "AUDZAR", "CADCHF", "CADJPY", "CHFHUF", "CHFJPY", "CHFZAR", "EURAUD", "EURCAD", "EURCHF", "EURCZK",
    "EURGBP", "EURHUF", "EURMXN", "EURNOK", "EURNZD", "EURPLN", "EURRUB", "EURSEK", "EURSGD", "EURZAR",
    "GBPAUD", "GBPUSD", "USDCHF", "USDCAD", "NZDUSD", "GBPNZD", "GBPCAD", "GBPCHF", "NZDCHF", "NZDCAD",
    "AUDCAD", "ZARJPY", "SGDJPY", "TRYJPY", "USDCZK", "USDSEK", "USDNOK", "USDPLN", "USDHUF", "EURTRY",
    "USDTRY", "USDSGD", "USDZAR", "USDMXN", "USDRUB", "GBPSGD", "GBPZAR", "NOKSEK", "NZDSEK", "NZDSGD", "USDILS"
]

def save_to_google_sheets(data_list):
    """Adds the final data to your Google Sheet without changing your scraper."""
    print("\n--- Connecting to Google Sheets ---", flush=True)
    try:
        # Load your credentials
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)

        # Open the specific sheet
        sheet_name = "[DYNAMIC] AXIORY SWAP POINTS"
        sheet = client.open(sheet_name).sheet1

        # Clear and update
        sheet.clear()
        sheet.append_row(["Symbol", "Swap Short", "Swap Long"])
        
        # Prepare data rows
        rows_to_upload = [[d['Symbol'], d['Swap Short'], d['Swap Long']] for d in data_list]
        sheet.append_rows(rows_to_upload)
        
        print(f"SUCCESS: Data stored in '{sheet_name}'!", flush=True)
    except Exception as e:
        print(f"!!! Sheets Storage Error: {str(e)}", flush=True)

def scrape_axiory_ordered():
    url = "https://www.axiory.com/jp/trading-products/forex"
    options = Options()
    # options.add_argument("--headless") 
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Use a dictionary for fast lookup by symbol name
        scraped_data_map = {}
        print("\n--- Starting Scraping ---\n", flush=True)

        for page in range(1, 7):
            print(f"PAGE {page}: Waiting for table data...", flush=True)
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr"))
            )
            
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            first_symbol_check = rows[0].find_elements(By.TAG_NAME, "td")[0].text.strip()
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 9:
                    symbol = cols[0].text.strip()
                    if symbol:
                        scraped_data_map[symbol] = {
                            "Swap Short": cols[7].text.strip(),
                            "Swap Long": cols[8].text.strip()
                        }

            if page < 6:
                next_page_num = page + 1
                try:
                    pager = driver.find_element(By.CLASS_NAME, "configurable-dynamic-table-pager")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pager)
                    time.sleep(1)

                    li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.configurable-dynamic-table-pager li")
                    target_button = next((li for li in li_elements if li.text.strip() == str(next_page_num)), None)
                    
                    if target_button:
                        driver.execute_script("arguments[0].click();", target_button)
                        WebDriverWait(driver, 10).until(
                            lambda d: d.find_elements(By.CSS_SELECTOR, "tbody tr")[0].text.strip() != first_symbol_check
                        )
                        time.sleep(1)
                except Exception as e:
                    print(f"!!! Pagination Error: {str(e)}", flush=True)
                    break

        # Reconstruct the list in the REQUIRED order
        ordered_final_data = []
        for symbol in REQUIRED_ORDER:
            if symbol in scraped_data_map:
                ordered_final_data.append({
                    "Symbol": symbol,
                    "Swap Short": scraped_data_map[symbol]["Swap Short"],
                    "Swap Long": scraped_data_map[symbol]["Swap Long"]
                })
            else:
                # Fill missing symbols with your requested value
                ordered_final_data.append({
                    "Symbol": symbol,
                    "Swap Short": "Web記載なし",
                    "Swap Long": "Web記載なし"
                })

        print("\n--- FINAL ORDERED RESULTS ---\n")
        print(pd.DataFrame(ordered_final_data).to_string(index=False), flush=True)

        # TRIGGER STORAGE
        save_to_google_sheets(ordered_final_data)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_axiory_ordered()