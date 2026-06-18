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

def scrape_dsex_recent():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)
        
        # নতুন নির্দিষ্ট লিংকে নেভিগেট করা
        print("Navigating to DSE Recent Market Information page...")
        try:
            page.goto("https://www.dsebd.org/recent_market_information.php", wait_until="domcontentloaded")
            
            # টেবিলটি লোড হওয়ার জন্য ৩ সেকেন্ড অপেক্ষা
            print("Waiting for table to render...")
            time.sleep(3)
            
            # Recent Market Information টেবিলের প্রথম সারির DSEX ভ্যালু টার্গেট করার সুনির্দিষ্ট XPath
            # এটি প্রথম টেবিলের ভেতরের প্রথম 'DSEX' লেখার ঠিক ডানপাশের td (ভ্যালু)-টি নেবে
            dsex_xpath = "(//table)[1]//td[normalize-space()='DSEX']/following-sibling::td[1]"
            
            page.wait_for_selector(dsex_xpath, state="visible", timeout=25000)
            
            dsex_value_text = page.locator(dsex_xpath).inner_text()
            print(f"Raw text found in Recent Market table: {dsex_value_text}")
            
            # কমা সরিয়ে সংখ্যায় (Float) রূপান্তর
            dsex_value = float(dsex_value_text.replace(',', '').strip())
            print(f"Successfully scraped DSEX Index: {dsex_value}")
            browser.close()
            return dsex_value
            
        except Exception as e:
            print(f"Scraping failed to find DSEX on recent market page: {e}")
            browser.close()
            return None

def save_to_firebase(value):
    if value is None:
        print("No value to save. Skipping Firebase sync.")
        return
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("Connecting to Firebase and saving data...")
    ref = db.reference(f'dsex_history/{today_str}')
    data = {
        "index_value": value,
        "scraped_at": timestamp_str
    }
    ref.set(data)
    print("Data successfully saved to Firebase!")

if __name__ == "__main__":
    dsex_val = scrape_dsex_recent()
    save_to_firebase(dsex_val)
