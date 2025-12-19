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
from selenium.common.exceptions import TimeoutException
# Formatting library
from gspread_formatting import set_frozen, format_cell_range, CellFormat, TextFormat, Color

# ANSI Escape Sequences for console highlighting
RED_BOLD = "\033[1;91m"
RESET = "\033[0m"

# Your strict master order (145 symbols)
MASTER_ORDER = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY", "CHFSGD",
    "EURAUD", "EURCAD", "EURCHF", "EURDKK", "EURGBP", "EURHKD", "EURHUF", "EURJPY", "EURNOK",
    "EURNZD", "EURPLN", "EURSEK", "EURSGD", "EURTRY", "EURUSD", "EURZAR", "GBPAUD", "GBPCAD",
    "GBPCHF", "GBPDKK", "GBPJPY", "GBPNOK", "GBPNZD", "GBPSEK", "GBPSGD", "GBPUSD", "NZDCAD",
    "NZDCHF", "NZDJPY", "NZDSGD", "NZDUSD", "SGDJPY", "USDCAD", "USDCHF", "USDCNH", "USDDKK",
    "USDHKD", "USDHUF", "USDJPY", "USDMXN", "USDNOK", "USDPLN", "USDSEK", "USDSGD", "USDTRY", "USDZAR",
    "1INCHUSD", "AAVEUSD", "ADAUSD", "ALGOUSD", "APEUSD", "APTUSD", "ARBUSD", "ATOMUSD", "AVAXUSD",
    "AXSUSD", "BATUSD", "BCHUSD", "BTCEUR", "BTCGBP", "BTCUSD", "BTGUSD", "CHZUSD", "COMPUSD",
    "CRVUSD", "DASHUSD", "DOGEUSD", "DOTUSD", "EGLDUSD", "ENJUSD", "EOSUSD", "ETCUSD", "ETHBTC",
    "ETHEUR", "ETHGBP", "ETHUSD", "FETUSD", "FILUSD", "FLOWUSD", "GRTUSD", "ICPUSD", "IMXUSD",
    "LDOUSD", "LINKUSD", "LRCUSD", "LTCUSD", "MANAUSD", "MATICUSD", "NEARUSD", "OMGUSD", "OPUSD",
    "SANDUSD", "SHIBUSD", "SKLUSD", "SNXUSD", "SOLUSD", "STORJUSD", "STXUSD", "SUSHIUSD", "UMAUSD",
    "UNIUSD", "XLMUSD", "XRPUSD", "XTZUSD", "ZECUSD", "ZRXUSD", "AUS200Cash", "CA60Cash", "ChinaHCash",
    "EU50Cash", "FRA40Cash", "GER40Cash", "GerMid50Cash", "GerTech30Cash", "HK50Cash", "IT40Cash",
    "JP225Cash", "NETH25Cash", "SA40Cash", "SPAIN35Cash", "SWI20Cash", "UK100Cash", "US100Cash",
    "US2000Cash", "US30Cash", "US500Cash", "GOLD", "SILVER", "XAUEUR", "XPDUSD", "XPTUSD", "BRENTCash",
    "NGASCash", "OILCash", "BTCJPY", "VAULTAUSD", "XAUCNH", "XAUJPY", "GAUCNH", "GAUUSD"
]

def save_to_google_sheets(data_list):
    """Creates a new tab, saves data, and applies custom #333333 formatting."""
    print("\n--- Connecting to Google Sheets ---", flush=True)
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Ensure your service_account.json is in the correct directory
        creds = ServiceAccountCredentials.from_json_keyfile_name('xm/service_account.json', scope)
        client = gspread.authorize(creds)

        # Opens the specific XM spreadsheet
        spreadsheet = client.open("[DYNAMIC] XM SWAP POINTS")
        sheet_title = datetime.now().strftime('%m/%d/%Y')
        
        try:
            worksheet = spreadsheet.worksheet(sheet_title)
            print(f"Sheet for {sheet_title} already exists. Updating...", flush=True)
        except gspread.exceptions.WorksheetNotFound:
            # Create a new tab with enough rows for the 145+ symbols
            worksheet = spreadsheet.add_worksheet(title=sheet_title, rows="200", cols="5")
            print(f"Created new sheet for: {sheet_title}", flush=True)

        worksheet.clear()
        # Headers matching your required order
        worksheet.append_row(["Symbol", "ロング (Long)", "ショート (Short)"])
        rows_to_upload = [[d['Symbol'], d['Long'], d['Short']] for d in data_list]
        worksheet.append_rows(rows_to_upload)

        # --- APPLYING YOUR SPECIFIC FORMATTING ---
        print(f"Applying Noto Sans JP and Custom Color #333333...", flush=True)
        
        # #333333 is RGB (51, 51, 51) -> 51/255 = ~0.2
        fmt = CellFormat(
            textFormat=TextFormat(
                fontFamily="Noto Sans JP",
                fontSize=9,
                foregroundColor=Color(0.2, 0.2, 0.2)
            )
        )
        
        total_range = f"A1:C{len(rows_to_upload) + 1}"
        format_cell_range(worksheet, total_range, fmt)
        set_frozen(worksheet, rows=1)
        
        print(f"SUCCESS: Data stored and formatted in tab '{sheet_title}'!", flush=True)
    except Exception as e:
        print(f"!!! Sheets Storage Error: {str(e)}", flush=True)

def get_optimized_driver():
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'eager'
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(25)
    return driver

def handle_modal(driver):
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie"))
        )
        accept_btn.click()
    except: pass

def scrape_standard_page(url, name_attr):
    driver = get_fresh_driver() # Using the fresh driver method to prevent hangs
    results = {}
    try:
        driver.get(url)
        handle_modal(driver)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
        
        try:
            driver.find_element(By.NAME, "DataTables_Table_0_length").send_keys("100")
            time.sleep(1)
        except: pass

        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")
        for row in rows:
            try:
                sym = row.find_element(By.CSS_SELECTOR, f"td[data-xm-qa-name='{name_attr}']").get_attribute("textContent").strip()
                l = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapLong']").get_attribute("textContent").strip()
                s = row.find_element(By.CSS_SELECTOR, "td[data-xm-qa-name='swapShort']").get_attribute("textContent").strip()
                if sym: results[sym] = {"Long": l, "Short": s}
            except: continue
    finally: driver.quit()
    return results

def scrape_crypto_page():
    driver = get_fresh_driver()
    results = {}
    try:
        driver.get("https://xem.fxsignup.com/trade/crypto-cfds.html")
        wait = WebDriverWait(driver, 20)
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "div.toggleBtnTable")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
        except: pass
        
        wait.until(lambda d: len(d.find_element(By.CSS_SELECTOR, "span[data-id$='data01']").get_attribute("textContent").strip()) > 0)

        rows = driver.find_elements(By.CSS_SELECTOR, "table.tableCommon03 tbody tr")
        for row in rows:
            try:
                sym = row.find_element(By.CSS_SELECTOR, "td.tc").get_attribute("textContent").strip()
                if not sym or "商品/銘柄" in sym: continue
                l = row.find_element(By.CSS_SELECTOR, "span[data-id$='data01']").get_attribute("textContent").strip()
                s = row.find_element(By.CSS_SELECTOR, "span[data-id$='data02']").get_attribute("textContent").strip()
                results[sym] = {"Long": l, "Short": s}
            except: continue
    finally: driver.quit()
    return results

# Helper to maintain fresh drivers for each link
def get_fresh_driver():
    return get_optimized_driver()

def run_main():
    master_map = {}
    links = [
        ("Forex", "https://www.xmtrading.com/jp/forex-trading", "currencyPair"),
        ("Indices", "https://www.xmtrading.com/jp/equity-indices", "symbol"),
        ("Metals", "https://www.xmtrading.com/jp/precious-metals", "currencyPair"),
        ("Energies", "https://www.xmtrading.com/jp/energies", "symbol")
    ]

    for cat, url, attr in links:
        print(f"Scraping {cat}...")
        try:
            master_map.update(scrape_standard_page(url, attr))
        except Exception as e:
            print(f"!!! Error in {cat}: {e}")
    
    print("Scraping Crypto...")
    try:
        master_map.update(scrape_crypto_page())
    except Exception as e:
        print(f"!!! Error in Crypto: {e}")

    # Detect New Symbols
    scraped_set = set(master_map.keys())
    master_set = set(MASTER_ORDER)
    new_found = sorted(list(scraped_set - master_set))

    if new_found:
        print(f"\n{RED_BOLD}NEW SYMBOL(S) SPOTTED!{RESET}")
        for s in new_found:
            print(f"{RED_BOLD}-> {s}{RESET}")

    # Build Final List with Order
    final_output = []
    for sym in MASTER_ORDER:
        vals = master_map.get(sym, {"Long": "Web記載なし", "Short": "Web記載なし"})
        final_output.append({"Symbol": sym, "Long": vals["Long"], "Short": vals["Short"]})

    # Append spotted symbols to the end
    for sym in new_found:
        final_output.append({"Symbol": sym, "Long": master_map[sym]["Long"], "Short": master_map[sym]["Short"]})

    # Render to Console
    df = pd.DataFrame(final_output)
    print("\n--- FINAL ORDERED XM DATA ---")
    print(df.to_string(index=False))

    # Save to Google Sheets
    save_to_google_sheets(final_output)

if __name__ == "__main__":
    run_main()