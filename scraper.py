import os
import json
import time
import requests
import concurrent.futures
from bs4 import BeautifulSoup

# === SECRETS & KEYS ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# === ALL INDIA STATES (URLS) ===
STATE_URLS = {
    "AP": "https://example.com/ap", "AR": "https://example.com/ar",
    "AS": "https://example.com/as", "BR": "https://example.com/br",
    "CG": "https://example.com/cg", "GA": "https://example.com/ga",
    "GJ": "https://example.com/gj", "HR": "https://example.com/hr",
    "HP": "https://example.com/hp", "JH": "https://example.com/jh",
    "KA": "https://example.com/ka", "KL": "https://example.com/kl",
    "MP": "https://example.com/mp", "MH": "https://example.com/mh",
    "MN": "https://example.com/mn", "ML": "https://example.com/ml",
    "MZ": "https://example.com/mz", "NL": "https://example.com/nl",
    "OD": "https://example.com/od", "PB": "https://example.com/pb",
    "RJ": "https://example.com/rj", "SK": "https://example.com/sk",
    "TN": "https://example.com/tn", "TG": "https://example.com/tg",
    "TR": "https://example.com/tr", "UP": "https://example.com/up",
    "UK": "https://example.com/uk", "WB": "https://example.com/wb"
}

# 1. STEALTH MODE (Website ke guards se bachne ka bhes)
def get_stealthy_text(url):
    try:
        if "example.com" in url:
            return "" # Fake links ko skip karo
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return ""
            
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        return text[:4000] # Token limit protect karna
    except Exception as e:
        return ""

# 2. AI EXTRACTOR (City & Interstate Route Smartness)
def extract_data_with_ai(raw_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """
    You are a precise data extractor for public bus schedules.
    Extract the following from the text: Bus Name, Source City (From), Destination City (To), Departure Time, and Arrival Time.
    Even if the route crosses state borders (Interstate), extract the exact city names.
    Do NOT include prices, AC/Non-AC, or extra text.
    Return ONLY a valid JSON array of objects.
    Example: [{"bus_name": "Soudamini", "source_city": "Kolkata", "destination_city": "Ranchi", "departure": "06:00 AM", "arrival": "02:00 PM"}]
    """
    
    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Raw Text: {raw_text}"}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()['choices'][0]['message']['content']
        clean_json = result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return []

# 3. SMART DATA CLEANER (Kachra Safai & Auto-Fix)
def smart_data_cleaner(ai_json_data):
    cleaned_data = []
    for bus in ai_json_data:
        # Check rule: Source, Destination aur Departure zaroori hain
        if bus.get("source_city") and bus.get("destination_city") and bus.get("departure"):
            # City names ko Title Case (Kolkata) karna
            bus["source_city"] = str(bus["source_city"]).strip().title()
            bus["destination_city"] = str(bus["destination_city"]).strip().title()
            
            # Agar naam missing hai toh default naam dena
            bus["bus_name"] = str(bus.get("bus_name", "Local/Govt Bus")).strip().title()
            bus["arrival"] = str(bus.get("arrival", "N/A")).strip()
            
            cleaned_data.append(bus)
    return cleaned_data

# 4. TELEGRAM ALERT
def send_to_telegram(state, filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(filepath, "rb") as file:
            files = {"document": file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": f"✅ {state} Bus Data Updated!"}
            requests.post(url, files=files, data=data)
    except:
        pass

# 5. SPIDER WORKER (Ek bot ka task)
def spider_worker(state, target_url):
    raw_text = get_stealthy_text(target_url)
    if raw_text:
        ai_data = extract_data_with_ai(raw_text)
        final_clean_data = smart_data_cleaner(ai_data)
        
        if final_clean_data:
            filepath = f"{state}_busdata.json"
            with open(filepath, "w") as f:
                json.dump(final_clean_data, f, indent=4)
            send_to_telegram(state, filepath)
            print(f"🕸️ [{state}] Success: Clean data saved!")
            return True
    return False

# 6. MASTER ENGINE (Spider Bots Release)
def main():
    print("🚀 Releasing Spider Bots across India...")
    
    # max_workers=5 (Ek sath 5 states par scan chalega)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for state, url in STATE_URLS.items():
            if "example.com" not in url:  # Sirf asli links par jayega
                futures.append(executor.submit(spider_worker, state, url))
                time.sleep(1)  # Bonus: 1 second delay taaki API par achanak load na pade
                
        for future in concurrent.futures.as_completed(futures):
            pass # Background me save aur alert ho gaya

    print("🎉 All Spiders Returned. Database Updated!")

if __name__ == "__main__":
    main()
    
