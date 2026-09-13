import os
import json
import requests

# GitHub Secrets se credentials lena
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

STATES_TO_SCRAPE = ["WB", "JH", "BR", "OD"]
VISITED_FILE = "visited_urls.json"

def load_visited_urls():
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r") as f:
            return json.load(f)
    return []

def save_visited_urls(urls):
    with open(VISITED_FILE, "w") as f:
        json.dump(urls, f, indent=4)

def extract_data_with_ai(text):
    # Abhi ke liye dummy data. Baad mein yahan OpenRouter API ka logic aayega.
    return {"bus_name": "Test Express", "route": "City A to City B", "time": "10:00 AM"}

def send_to_telegram(state, filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(filepath, "rb") as file:
            files = {"document": file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": f"✅ New Bus Data for: {state}"}
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                print(f"[{state}] File successfully sent to Telegram!")
            else:
                print(f"[{state}] Telegram error: {response.text}")
    except Exception as e:
        print(f"[{state}] Failed to send file: {e}")

def main():
    visited_urls = load_visited_urls()
    
    for state in STATES_TO_SCRAPE:
        print(f"\n🚀 Processing State: {state}")
        state_data = []
        state_file = f"{state}_busdata.json"
        
        # Test ke liye ek dummy URL
        test_url = f"https://example.com/{state.lower()}_buses"
        
        if test_url in visited_urls:
            print(f"Skipping {test_url}, already scraped.")
            continue
            
        print(f"Scraping data from {test_url}...")
        
        # Data extract karna aur save karna
        extracted_json = extract_data_with_ai("Sample page text")
        state_data.append(extracted_json)
        visited_urls.append(test_url)
        
        # JSON file save karna
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=4)
            
        # File Telegram par push karna
        send_to_telegram(state, state_file)
        
    # Memory update karna taaki bot URL yaad rakhe
    save_visited_urls(visited_urls)
    print("\n🎉 Scraping Job Completed!")

if __name__ == "__main__":
    main()
  
