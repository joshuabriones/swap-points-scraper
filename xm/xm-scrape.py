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
from gspread_formatting import set_frozen, format_cell_range, CellFormat, TextFormat, Color

# ANSI Escape Sequences
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
    "JP225Cash", "NETH25Cash", "SA40Cash", "SpainCash", "SWI20Cash", "UK100Cash", "US100Cash",
    "US2000Cash", "US30Cash", "US500Cash", "GOLD", "SILVER", "XAUEUR", "XPDUSD", "XPTUSD", "BRENTCash",
    "NGASCash", "OILCash", "BTCJPY", "VAULTAUSD", "XAUCNH", "XAUJPY", "GAUCNH", "GAUUSD"
]

def save_to_google_sheets(data_list):
    print("\n--- Connecting to Google Sheets ---", flush=True)
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('xm/service_account.json', scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("[DYNAMIC] XM SWAP POINTS")
        sheet_title = datetime.now().strftime('%m/%d/%Y')
        
        try:
            worksheet = spreadsheet.worksheet(sheet_title)
            print(f"Sheet for {sheet_title} already exists. Updating...", flush=True)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_title, rows="200", cols="5")
            print(f"Created new sheet for: {sheet_title}", flush=True)

        worksheet.clear()
        worksheet.append_row(["Symbol", "ロング (Long)", "ショート (Short)"])
        rows_to_upload = [[d['Symbol'], d['Long'], d['Short']] for d in data_list]
        worksheet.append_rows(rows_to_upload)

        print(f"Applying Roboto and Color #333333...", flush=True)
        fmt = CellFormat(textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(0.2, 0.2, 0.2)))
        format_cell_range(worksheet, f"A1:C{len(rows_to_upload) + 1}", fmt)
        set_frozen(worksheet, rows=1)
        print(f"SUCCESS: Data stored in '{sheet_title}'!", flush=True)
    except Exception as e:
        print(f"!!! Sheets Storage Error: {str(e)}", flush=True)

def get_fresh_driver(strategy='normal'):
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Fix for 'timeout from renderer' errors
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.page_load_strategy = strategy # Flexible strategy based on URL behavior
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45) # Higher timeout for heavy Forex/Energies pages
    return driver

def handle_modal(driver):
    try:
        accept_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptDefaultCookie")))
        accept_btn.click()
    except: pass

def scrape_standard_page(url, name_attr):
    # Use 'normal' strategy for standard pages as they are more sensitive to script loading
    driver = get_fresh_driver(strategy='normal')
    results = {}
    try:
        driver.get(url)
        handle_modal(driver)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))
        
        try:
            driver.find_element(By.NAME, "DataTables_Table_0_length").send_keys("100")
            time.sleep(2)
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
    # Use 'eager' strategy for Crypto page as it is extremely dynamic
    driver = get_fresh_driver(strategy='eager')
    results = {}
    try:
        driver.get("https://xem.fxsignup.com/trade/crypto-cfds.html")
        wait = WebDriverWait(driver, 25)
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
            print(f"!!! Retry triggered for {cat} due to timeout...")
            try:
                # One single retry attempt with Normal strategy
                master_map.update(scrape_standard_page(url, attr))
            except:
                print(f"!!! Error in {cat}: {e}")

    print("Scraping Crypto...")
    try:
        master_map.update(scrape_crypto_page())
    except Exception as e:
        print(f"!!! Error in Crypto: {e}")

    scraped_set = set(master_map.keys())
    master_set = set(MASTER_ORDER)
    new_found = sorted(list(scraped_set - master_set))

    if new_found:
        print(f"\n{RED_BOLD}NEW SYMBOL(S) SPOTTED!{RESET}")
        for s in new_found:
            print(f"{RED_BOLD}-> {s}{RESET}")

    final_output = []
    for sym in MASTER_ORDER:
        vals = master_map.get(sym, {"Long": "Web記載なし", "Short": "Web記載なし"})
        final_output.append({"Symbol": sym, "Long": vals["Long"], "Short": vals["Short"]})

    for sym in new_found:
        final_output.append({"Symbol": sym, "Long": master_map[sym]["Long"], "Short": master_map[sym]["Short"]})

    df = pd.DataFrame(final_output)
    print("\n--- FINAL ORDERED XM DATA ---")
    print(df.to_string(index=False))

    save_to_google_sheets(final_output)

if __name__ == "__main__":
    run_main()