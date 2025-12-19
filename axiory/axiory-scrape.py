import time
import pandas as pd
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from gspread_formatting import set_frozen, format_cell_range, CellFormat, TextFormat, Color

# ANSI Escape Sequences for console highlighting
RED_BOLD = "\033[1;91m"
RESET = "\033[0m"

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
    """Saves data to a new tab and applies #333333 Noto Sans JP formatting."""
    print("\n--- Connecting to Google Sheets ---", flush=True)
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('axiory/service_account.json', scope)
        client = gspread.authorize(creds)

        spreadsheet = client.open("[DYNAMIC] AXIORY SWAP POINTS")
        sheet_title = datetime.now().strftime('%m/%d/%Y')
        
        try:
            worksheet = spreadsheet.worksheet(sheet_title)
            print(f"Sheet for {sheet_title} already exists. Updating...", flush=True)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_title, rows="150", cols="5")
            print(f"Created new sheet for: {sheet_title}", flush=True)

        worksheet.clear()
        worksheet.append_row(["Symbol", "Swap Short", "Swap Long"])
        rows_to_upload = [[d['Symbol'], d['Swap Short'], d['Swap Long']] for d in data_list]
        worksheet.append_rows(rows_to_upload)

        # Apply custom color #333333 (RGB: 0.2, 0.2, 0.2)
        fmt = CellFormat(
            textFormat=TextFormat(fontFamily="Noto Sans JP", fontSize=9, foregroundColor=Color(0.2, 0.2, 0.2))
        )
        format_cell_range(worksheet, f"A1:C{len(rows_to_upload) + 1}", fmt)
        set_frozen(worksheet, rows=1)
        print(f"SUCCESS: Data saved in tab '{sheet_title}'!", flush=True)
    except Exception as e:
        print(f"!!! Sheets Storage Error: {str(e)}", flush=True)

def scrape_axiory_ordered():
    url = "https://www.axiory.com/jp/trading-products/forex"
    options = Options()
    # options.add_argument("--headless") 
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        scraped_data_map = {}
        print("\n--- Starting Scraping ---\n", flush=True)

        for page in range(1, 7):
            print(f"PAGE {page}: Waiting for table data...", flush=True)
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr")))
            
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            first_row_text = rows[0].text.strip() # Used for pagination validation
            
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
                try:
                    pager = driver.find_element(By.CLASS_NAME, "configurable-dynamic-table-pager")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pager)
                    time.sleep(1)
                    
                    li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.configurable-dynamic-table-pager li")
                    target_btn = next((li for li in li_elements if li.text.strip() == str(page + 1)), None)
                    
                    if target_btn:
                        driver.execute_script("arguments[0].click();", target_btn)
                        # Explicit wait for page change
                        WebDriverWait(driver, 10).until(
                            lambda d: d.find_elements(By.CSS_SELECTOR, "tbody tr")[0].text.strip() != first_row_text
                        )
                        time.sleep(1)
                except Exception as e:
                    print(f"!!! Pagination Error: {str(e)}", flush=True)
                    break

        # --- NEW SYMBOL DETECTION LOGIC ---
        # Find difference between sets of symbols
        scraped_set = set(scraped_data_map.keys())
        required_set = set(REQUIRED_ORDER)
        new_symbols = scraped_set - required_set

        if new_symbols:
            print(f"\n{RED_BOLD}!!! NEW SYMBOL(S) SPOTTED !!!{RESET}")
            for sym in new_symbols:
                print(f"{RED_BOLD}-> {sym} (New item found on web, but missing from REQUIRED_ORDER){RESET}")
            print("")

        # Prepare ordered results
        ordered_final_data = []
        for symbol in REQUIRED_ORDER:
            if symbol in scraped_data_map:
                ordered_final_data.append({
                    "Symbol": symbol,
                    "Swap Short": scraped_data_map[symbol]["Swap Short"],
                    "Swap Long": scraped_data_map[symbol]["Swap Long"]
                })
            else:
                ordered_final_data.append({
                    "Symbol": symbol, "Swap Short": "Web記載なし", "Swap Long": "Web記載なし"
                })

        # Automatically append NEW symbols at the end so they are not lost
        for sym in new_symbols:
            ordered_final_data.append({
                "Symbol": sym,
                "Swap Short": scraped_data_map[sym]["Swap Short"],
                "Swap Long": scraped_data_map[sym]["Swap Long"]
            })

        print("--- FINAL ORDERED RESULTS ---\n")
        print(pd.DataFrame(ordered_final_data).to_string(index=False), flush=True)

        save_to_google_sheets(ordered_final_data)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_axiory_ordered()