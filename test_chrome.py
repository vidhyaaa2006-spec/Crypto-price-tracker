from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
from datetime import datetime
import re

CSV_FILE = "crypto_prices.csv"
TOP_LIMIT = 10
chrome_version = "109.0.5414.74"

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager(version=chrome_version).install()),
    options=options
)

def parse_number(text):
    if not text:
        return None

    text = text.replace("\n", " ")
    text = text.replace("$", "").replace("%", "").replace(",", "").strip()

    match = re.match(r"([0-9]*\.?[0-9]+)([KMBkmb]?)", text)
    if not match:
        return None

    num, suffix = match.groups()
    num = float(num)

    if suffix:
        suffix = suffix.upper()
        if suffix == "K":
            num *= 1_000
        elif suffix == "M":
            num *= 1_000_000
        elif suffix == "B":
            num *= 1_000_000_000

    return num

wait = WebDriverWait(driver, 20)
driver.get("https://coinmarketcap.com/")
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr")))

rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")[:TOP_LIMIT]

data = []
for i, row in enumerate(rows):

    def safe_sel(selector):
        try:
            return row.find_element(By.CSS_SELECTOR, selector).text.replace("\n", " ").strip()
        except:
            return ""

    name = safe_sel("td:nth-child(3) a") or safe_sel("td:nth-child(3) p")
    price = safe_sel("td:nth-child(4) span")
    change = safe_sel("td:nth-child(5) span")
    market_cap = safe_sel("td:nth-child(9) p")

    data.append({
        "Rank": i + 1,
        "Name": name,                   
        "Price": parse_number(price),
        "24h Change %": parse_number(change),
        "Market Cap": parse_number(market_cap),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

df = pd.DataFrame(data)

df["Name"] = df["Name"].str.replace("\n", " ", regex=False)

try:
    old_df = pd.read_csv(CSV_FILE)
    df = pd.concat([old_df, df], ignore_index=True)
except FileNotFoundError:
    pass

df.to_csv(CSV_FILE, index=False, encoding="utf-8")

print("\nScraping Successful!\n")
print(df)

driver.quit()
