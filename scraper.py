import os
import json
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
        page.set_default_timeout(45000) 
        
        print("Navigating to DSE website...")
        try:
            page.goto("https://www.dsebd.org/", wait_until="domcontentloaded")
            
            # ডিএসই-র লেটেস্ট সাইট স্ট্রাকচার অনুযায়ী DSEX ভ্যালু খোঁজার আরও সহজ ও নির্ভুল সিলেক্টর
            # এটি সরাসরি টেবিলের ভেতরের শক্তিশালী বা বোল্ড করা টেক্সটগুলো চেক করবে
            page.wait_for_selector("text=DSEX", timeout=20000)
            
            # নিখুঁত লোকেশন টার্গেট করার জন্য অল্টারনেটিভ কুয়েরি
            dsex_value_text = page.locator("//td[normalize-space()='DSEX']/following-sibling::td[1]").inner_text()
            
            # যদি প্রথম উপায়ে না পায়, তবে সাধারণ টেক্সট ম্যাচ ট্রাই করবে
            if not dsex_value_text:
                dsex_value_text = page.locator("b:has-text('DSEX') >> xpath=../following-sibling::td[1]").inner_text()

            dsex_value = float(dsex_value_text.replace(',', '').strip())
            print(f"Successfully scraped DSEX Index: {dsex_value}")
            browser.close()
            return dsex_value
            
        except Exception as e:
            print(f"Scraping failed to find DSEX: {e}")
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
