import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, db

# ১. ফায়ারবেইজ ইনিশিয়ালাইজেশন
firebase_creds_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if not firebase_creds_json:
    raise ValueError("Firebase credentials not found in environment variables!")

creds_dict = json.loads(firebase_creds_json)
cred = credentials.Certificate(creds_dict)

FIREBASE_DB_URL = "https://my-share-market-495aa-default-rtdb.firebaseio.com/" 

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

def scrape_dsex():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)
        
        print("Navigating to DSE website...")
        try:
            page.goto("https://www.dsebd.org/", wait_until="domcontentloaded")
            
            # পেজের প্রথম মূল টেবিলটির লোড হওয়া পর্যন্ত অপেক্ষা করা
            page.wait_for_selector("table", timeout=30000)
            time.sleep(3) # ডেটা রেন্ডার হওয়ার জন্য ছোট বিরতি
            
            # প্রথম টেবিলের (index 0) ভেতরের DSEX লেখার ঠিক পরের td (ভ্যালু)-কে টার্গেট করা
            # এই XPath শুধুমাত্র প্রথম টেবিলে থাকা DSEX-এর মানটিই নেবে
            first_table_dsex_xpath = "(//table)[1]//td[normalize-space()='DSEX']/following-sibling::td[1]"
            
            page.wait_for_selector(first_table_dsex_xpath, state="visible", timeout=20000)
            
            dsex_value_text = page.locator(first_table_dsex_xpath).inner_text()
            print(f"Raw text found in first table: {dsex_value_text}")
            
            dsex_value = float(dsex_value_text.replace(',', '').strip())
            print(f"Successfully scraped DSEX Index from first table: {dsex_value}")
            browser.close()
            return dsex_value
            
        except Exception as e:
            print(f"Scraping failed to find DSEX in first table: {e}")
            browser.close()
            return None

def save_to_firebase(value):
    if value is None:
        print("No value to save. Skipping Firebase sync.")
        return
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("Connecting to Firebase...")
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
