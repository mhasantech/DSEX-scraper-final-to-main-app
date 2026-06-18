import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, db

firebase_creds_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if not firebase_creds_json:
    raise ValueError("Firebase credentials not found in environment variables!")

creds_dict = json.loads(firebase_creds_json)
cred = credentials.Certificate(creds_dict)

# আপনার প্রোজেক্ট আইডি অনুযায়ী ডাটাবেজ URL
FIREBASE_DB_URL = "https://my-share-market-495aa-default-rtdb.firebaseio.com/" 

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

def scrape_dsex():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to DSE website...")
        page.goto("https://www.dsebd.org/", wait_until="domcontentloaded")

        try:
            dsex_value_text = page.locator("a:has-text('DSEX') >> xpath=../following-sibling::td[1]").inner_text()
            dsex_value = float(dsex_value_text.replace(',', '').strip())
            print(f"Successfully scraped DSEX Index: {dsex_value}")
            return dsex_value
        except Exception as e:
            print(f"Error finding DSEX element: {e}")
            browser.close()
            return None

def save_to_firebase(value):
    if value is None:
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ref = db.reference(f'dsex_history/{today_str}')
    data = {
        "index_value": value,
        "scraped_at": timestamp_str
    }
    ref.set(data)
    print("Data successfully saved to Firebase!")

if __name__ == "__main__":
    dsex_val = scrape_dsex()
    save_to_firebase(dsex_val)
