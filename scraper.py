import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

from db import init_db, upsert_buses, export_json, clear_source

# === SECRETS ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Kaggle datasets (username/dataset-slug)
KAGGLE_DATASETS = [
    # Add more later after token is set
    # "ayushkhaire/indian-cities-buses-routes-and-prices",
]

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] skipped (no secrets)")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}, timeout=20)
    except Exception as e:
        print("[Telegram] error:", e)

def load_kaggle_datasets():
    """Download Kaggle datasets if credentials exist."""
    rows = []
    kaggle_user = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")
    if not kaggle_user or not kaggle_key:
        print("[Kaggle] No credentials. Skipping Kaggle download.")
        return rows

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
    except Exception as e:
        print("[Kaggle] Auth failed:", e)
        return rows

    Path("data/kaggle").mkdir(parents=True, exist_ok=True)

    for ds in KAGGLE_DATASETS:
        try:
            print(f"[Kaggle] Downloading {ds} ...")
            api.dataset_download_files(ds, path="data/kaggle", unzip=True, quiet=False)
            print(f"[Kaggle] Done: {ds}")
        except Exception as e:
            print(f"[Kaggle] Failed {ds}:", e)

    # Try to parse common CSV patterns
    import pandas as pd
    for csv_path in Path("data/kaggle").rglob("*.csv"):
        try:
            df = pd.read_csv(csv_path, low_memory=False)
            cols = {c.lower().strip(): c for c in df.columns}

            def col(*names):
                for n in names:
                    if n in cols:
                        return cols[n]
                return None

            from_c = col("from", "source", "source_city", "origin")
            to_c = col("to", "destination", "destination_city", "dest")
            dep_c = col("departure", "departure_time", "dep_time", "start_time")
            arr_c = col("arrival", "arrival_time", "arr_time", "end_time")
            op_c = col("operator", "operator_name", "travels", "bus_operator")
            name_c = col("bus_name", "bus", "service_name", "name")
            type_c = col("bus_type", "type", "ac_type")

            if not from_c or not to_c:
                continue

            for _, r in df.iterrows():
                src = str(r.get(from_c, "")).strip().title()
                dst = str(r.get(to_c, "")).strip().title()
                if not src or not dst or src == "Nan" or dst == "Nan":
                    continue
                rows.append({
                    "state": None,
                    "bus_name": str(r.get(name_c, "Private Bus")).strip().title() if name_c else "Private Bus",
                    "operator_type": "Private",
                    "operator_name": str(r.get(op_c, "Unknown")).strip().title() if op_c else "Unknown",
                    "source_city": src,
                    "destination_city": dst,
                    "departure_time": str(r.get(dep_c, "N/A")).strip() if dep_c else "N/A",
                    "arrival_time": str(r.get(arr_c, "N/A")).strip() if arr_c else "N/A",
                    "route": f"{src} - {dst}",
                    "stoppages": [],
                    "bus_type": str(r.get(type_c, "")).strip() if type_c else "",
                    "frequency": "",
                    "source": f"kaggle:{csv_path.name}"
                })
        except Exception as e:
            print(f"[Kaggle] Parse error {csv_path}:", e)

    return rows

def load_sample_data():
    """Fallback sample so system works even without Kaggle."""
    return [
        {
            "state": "WB",
            "bus_name": "Soudamini Express",
            "operator_type": "Private",
            "operator_name": "Soudamini Travels",
            "source_city": "Kolkata",
            "destination_city": "Ranchi",
            "departure_time": "06:00 AM",
            "arrival_time": "02:00 PM",
            "route": "Kolkata - Durgapur - Asansol - Ranchi",
            "stoppages": ["Kolkata", "Durgapur", "Asansol", "Ranchi"],
            "bus_type": "Non-AC Seater",
            "frequency": "Daily",
            "source": "sample"
        },
        {
            "state": "WB",
            "bus_name": "SBSTC Ordinary",
            "operator_type": "Govt",
            "operator_name": "SBSTC",
            "source_city": "Kolkata",
            "destination_city": "Digha",
            "departure_time": "07:30 AM",
            "arrival_time": "01:00 PM",
            "route": "Kolkata - Contai - Digha",
            "stoppages": ["Kolkata", "Contai", "Digha"],
            "bus_type": "Non-AC",
            "frequency": "Daily",
            "source": "sample"
        },
        {
            "state": "JH",
            "bus_name": "Jharkhand Express",
            "operator_type": "Private",
            "operator_name": "Local Travels",
            "source_city": "Ranchi",
            "destination_city": "Jamshedpur",
            "departure_time": "08:00 AM",
            "arrival_time": "12:00 PM",
            "route": "Ranchi - Jamshedpur",
            "stoppages": ["Ranchi", "Jamshedpur"],
            "bus_type": "AC",
            "frequency": "Daily",
            "source": "sample"
        },
    ]

def main():
    print("🚀 Bus Database Scraper starting...")
    init_db()

    all_rows = []

    # 1. Kaggle (if token present)
    kaggle_rows = load_kaggle_datasets()
    if kaggle_rows:
        clear_source("kaggle")  # will clear all kaggle:* if needed later
        # clear by prefix roughly
        all_rows.extend(kaggle_rows)
        print(f"[Kaggle] Loaded {len(kaggle_rows)} rows")
    else:
        print("[Kaggle] No data loaded")

    # 2. Sample fallback so frontend always has something
    sample = load_sample_data()
    clear_source("sample")
    all_rows.extend(sample)
    print(f"[Sample] Loaded {len(sample)} rows")

    # Save to DB
    inserted = upsert_buses(all_rows)
    print(f"✅ Inserted/Updated {inserted} rows into SQLite")

    # Export for GitHub Pages
    count = export_json("export/buses.json")
    print(f"✅ Exported {count} buses to export/buses.json")

    # Also keep state-wise json for compatibility with old index.html
    Path("export").mkdir(exist_ok=True)
    by_state = {}
    for r in all_rows:
        st = r.get("state") or "ALL"
        by_state.setdefault(st, []).append(r)
    for st, items in by_state.items():
        with open(f"{st}_busdata.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    send_telegram(f"✅ Bus DB updated\nRows: {inserted}\nExported: {count}\nTime: {datetime.utcnow().isoformat()}Z")
    print("🎉 Done")

if __name__ == "__main__":
    main()
