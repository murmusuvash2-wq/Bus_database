import os
import json
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

STATES_TO_SCRAPE = ["WB"] # Abhi sirf ek state test ke liye
VISITED_FILE = "visited_urls.json"

def get_clean_text(url):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Faltu scripts aur styles hata dein
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text[:4000] # AI API limit ke liye shuruat ka text
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return ""

def extract_data_with_ai(raw_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """
    You are an expert data extractor. Look at the following raw text from a website.
    Extract the bus schedule (Bus Name, Route, Departure Time, Arrival Time).
    Return ONLY a valid JSON array of objects. Do not write any markdown, greetings, or extra text.
    Example output: [{"bus_name": "Soudamini", "route": "Bankura to Digha", "departure": "06:00 AM", "arrival": "12:00 PM"}]
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
        ai_response = response.json()
        result = ai_response['choices'][0]['message']['content']
        # AI kabhi-kabhi markdown backticks (```json) bhej deta hai, usko hatana
        clean_json = result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Extraction failed: {e}")
        return [{"error": "Data could not be extracted"}]

def send_to_telegram(state, filepath):
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(filepath, "rb") as file:
            files = {"document": file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": f"🤖 AI Data Extracted for: {state}"}
            requests.post(url, files=files, data=data)
    except Exception as e:
        pass

def main():
    # Test ke liye ek fake URL jo text return karega (Isko baad mein real link se replace karenge)
    test_url = "[https://example.com](https://example.com)" 
    
    for state in STATES_TO_SCRAPE:
        print(f"Fetching HTML for {state}...")
        raw_text = get_clean_text(test_url)
        
        if raw_text:
            print("Sending text to OpenRouter AI...")
            extracted_json = extract_data_with_ai(raw_text)
            
            state_file = f"{state}_busdata.json"
            with open(state_file, "w") as f:
                json.dump(extracted_json, f, indent=4)
                
            send_to_telegram(state, state_file)
            print("Done! Check Telegram.")

if __name__ == "__main__":
    main()
    
