# Bus_database

All India Bus Timetable (Govt + Private)

## Features
- SQLite database (`data/bus.db`)
- Auto export to `export/buses.json` for GitHub Pages
- Kaggle dataset support (add token later)
- Daily GitHub Actions scraper
- Telegram notification on update
- Search by city / operator / type

## Setup Secrets (GitHub → Settings → Secrets)

| Secret | Required |
|--------|----------|
| `TELEGRAM_BOT_TOKEN` | Optional |
| `TELEGRAM_CHAT_ID` | Optional |
| `OPENROUTER_API_KEY` | Optional |
| `KAGGLE_USERNAME` | For Kaggle data |
| `KAGGLE_KEY` | For Kaggle data |

## How to add Kaggle datasets
1. Create Kaggle account → Account → Create New API Token
2. Add `KAGGLE_USERNAME` + `KAGGLE_KEY` in repo secrets
3. Edit `scraper.py` → `KAGGLE_DATASETS` list and add dataset slugs
4. Run Actions → Automated Bus Scraper → Run workflow

## Local run
```bash
pip install -r requirements.txt
python scraper.py
```

## GitHub Pages
Enable Pages on `main` branch / root.  
Site will use `index.html` + `export/buses.json`.
