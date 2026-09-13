import os
import json
import requests
from datetime import datetime

# Environment Variables se API keys lena (GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# State list (Ek ke baad ek scrape honge)
STATES_TO_SCRAPE = ["WB", "JH", "BR", "OD"]
VISITED_FILE = "visited_urls.json"

def load_visited_urls():
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r") as f:
            return json.load(f)
    return []

def save_visited_urls(urls):
    with open(VISITED_FILE, "w") as f:
        json.dump(urls, f)

def extract_data_with_ai(text):
    # Yahan aapka OpenRouter API call aayega
    # Dummy structure for now
    return {"route": "Test Route", "time": "10:00 AM", "status": "Success"}

def send_to_telegram(state, filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(filepath, "rb") as file:
            files = {"document": file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": f"✅ Data Extracted for State: {state}"}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            print(f"[{state}] File sent to Telegram successfully.")
    except Exception as e:
        print(f"[{state}] Telegram push failed: {e}")

def main():
    visited_urls = load_visited_urls()
    
    for state in STATES_TO_SCRAPE:
        print(f"\n🚀 Starting scraping for {state}...")
        state_data = []
        state_file = f"{state}_busdata.json"
        
        try:
            # Yahan URL search aur loop aayega
            dummy_url = f"https://example.com/bus/{state.lower()}"
            
            if dummy_url in visited_urls:
                print(f"Skipping {dummy_url}, already visited.")
                continue
                
            print(f"Scraping {dummy_url}...")
            
            # Error cross-verification block
            try:
                response = requests.get(dummy_url, timeout=10)
                response.raise_for_status()
                
                # AI Extraction
                clean_json = extract_data_with_ai(response.text)
                state_data.append(clean_json)
                visited_urls.append(dummy_url)
                
            except requests.exceptions.RequestException as req_err:
                print(f"❌ Network Error on {dummy_url}: {req_err}")
                continue # Ek URL fail hua toh agle URL par jao
                
        except Exception as e:
            print(f"❌ Critical Error in state {state}: {e}")
            continue # Ek State fail hua toh agle State par jao
            
        # State ka data save karna aur Telegram par bhejna
        if state_data:
            with open(state_file, "w") as f:
                json.dump(state_data, f, indent=4)
            send_to_telegram(state, state_file)
            
    # Run complete hone par visited list update karna
    save_visited_urls(visited_urls)
    print("\n🎉 All assigned states processed!")

if __name__ == "__main__":
    main()
          
