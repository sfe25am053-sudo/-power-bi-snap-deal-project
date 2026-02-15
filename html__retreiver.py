import time
import re
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

# ===================== CONFIG =====================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = False

LISTING_WAIT = 10
PAGE_LOAD_TIMEOUT = 40
LEFT_X_THRESHOLD = 420

MAX_SECTIONS = 5
MAX_SUBCATS = 5
MAX_PRODUCTS_PER_SUBCAT = 10

BASE_SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear",
    "Kids Fashion": "https://www.snapdeal.com/search?keyword=kids%20fashion",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing",
}
# ==================================================

# ---------- Selenium setup ----------
chrome_opts = Options()

if HEADLESS:
    chrome_opts.add_argument("--headless=new")

chrome_opts.add_argument("--window-size=1920,1080")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--disable-notifications")
chrome_opts.add_argument("--blink-settings=imagesEnabled=false")

driver = webdriver.Chrome(options=chrome_opts)
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
wait = WebDriverWait(driver, LISTING_WAIT)

# ---------- SAFE GET ----------
def safe_get(url):
    try:
        driver.get(url)
        return True
    except TimeoutException:
        print(f"⏳ Timeout skip: {url}")
    except WebDriverException:
        print(f"❌ WebDriver error skip: {url}")
    return False

def human_sleep(sec=2):
    time.sleep(sec)

# ---------- HELPERS ----------
def parse_rating(style):
    if not style:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", style)
    return round(float(m.group(1)) / 20, 1) if m else ""

def find_first(selectors, parent=None, attr=None):
    ctx = parent if parent else driver
    for sel in selectors:
        try:
            el = ctx.find_element(By.CSS_SELECTOR, sel)
            return el.get_attribute(attr) if attr else el.text.strip()
        except:
            pass
    return ""

def find_all(selector, parent=None):
    ctx = parent if parent else driver
    try:
        return ctx.find_elements(By.CSS_SELECTOR, selector)
    except:
        return []

# ---------- SUBCATEGORY LINKS (SAFE) ----------
def get_left_subcategory_links():
    subcats = []
    seen = set()

    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        try:
            href = a.get_attribute("href")
            text = a.text.strip()

            if not href or not text:
                continue
            if not href.startswith("http"):
                continue
            if "javascript" in href.lower():
                continue
            if a.location["x"] > LEFT_X_THRESHOLD:
                continue

            key = (text, href)
            if key in seen:
                continue

            seen.add(key)
            subcats.append({"Subcategory": text, "URL": href})

        except:
            continue

    return subcats[:MAX_SUBCATS]

# ---------- SCRAPE PRODUCTS ----------
def scrape_listing_cards(section, subcat):
    rows = []
    cards = find_all("div.product-tuple-listing")

    for card in cards[:MAX_PRODUCTS_PER_SUBCAT]:
        rows.append({
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Section": section,
            "Subcategory": subcat,
            "Product Name": find_first(["p.product-title"], card),
            "Price": find_first(["span.product-price"], card),
            "Rating": parse_rating(
                find_first([".filled-stars"], card, "style")
            ),
            "Image URL": find_first(["img"], card, "src"),
            "Product URL": find_first(["a"], card, "href")
        })
    return rows

# ===================== MAIN =====================
all_rows = []

for section, base_url in list(BASE_SECTIONS.items())[:MAX_SECTIONS]:
    print(f"\n=== {section} ===")

    if not safe_get(base_url):
        continue

    human_sleep(3)

    subcats = get_left_subcategory_links()
    if not subcats:
        subcats = [{"Subcategory": "All", "URL": base_url}]

    for sc in subcats:
        print(f"Scraping → {sc['Subcategory']}")

        if not safe_get(sc["URL"]):
            continue

        human_sleep(3)

        rows = scrape_listing_cards(section, sc["Subcategory"])
        all_rows.extend(rows)

# ---------- SAVE CSV ----------
df = pd.DataFrame(all_rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✅ DONE! Saved as {OUTPUT_CSV}")
driver.quit()

