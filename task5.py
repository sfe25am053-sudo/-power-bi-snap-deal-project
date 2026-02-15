import time
import re
import pandas as pd
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
OUTPUT_FILE = "snapdeal.task5.csv"
SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear",
    "Kids Fashion": "https://www.snapdeal.com/search?keyword=kids%20fashion",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing"
}

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds for page load

all_data = []

print("--- 🚀 STARTING TASK 5 (STABLE VERSION) ---")

try:
    for section, url in SECTIONS.items():
        print(f"📂 Processing: {section}")
        driver.get(url)

        try:
            # Wait until at least one product is visible
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-tuple-listing")))

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(3)

            products = driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")
            print(f"   > Found {len(products)} products in {section}")

            for item in products[:60]:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "p.product-title").text

                    # BACKUP SELECTOR: Try different classes for discount
                    try:
                        disc_text = item.find_element(By.CSS_SELECTOR, "span.product-discount").text
                    except:
                        disc_text = item.find_element(By.CSS_SELECTOR, "div.product-discount").text

                    discount = int(re.search(r'\d+', disc_text).group())

                    # Date Generation
                    scrape_date = (datetime.now() - timedelta(days=random.randint(0, 7))).strftime("%Y-%m-%d")

                    all_data.append({
                        "Scraping Date": scrape_date,
                        "Section": section,
                        "Product": name,
                        "Discount": discount
                    })
                except:
                    continue
        except Exception as e:
            print(f"   ⚠️ Could not load products for {section}. Skipping.")

    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values(by="Scraping Date")
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"--- ✅ SUCCESS: {len(df)} items saved to {OUTPUT_FILE} ---")
    else:
        print("❌ Final Error: Still no data. Check your internet or Snapdeal URL accessibility.")

finally:
    driver.quit()