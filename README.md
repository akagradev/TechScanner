# Bloomberg Tech AI Signal Tracker

A lightweight MVP that tracks Bloomberg Technology articles daily and counts how often selected AI-related companies are mentioned.

## Overview

This project:

1. Scrapes recent articles from the [Bloomberg Technology RSS feed](https://feeds.bloomberg.com/technology/news.rss)
2. Counts mentions of 13 tracked companies in article titles and content
3. Stores daily aggregates in `data/mentions.csv`
4. Displays trends and rankings in a Streamlit dashboard

No database, no AI APIs, no authentication — just Python, CSV, and GitHub Actions.

## Tracked Companies

NVIDIA, AMD, Micron, Broadcom, Marvell, Meta, Microsoft, Google, Amazon, OpenAI, Anthropic, Nebius, CoreWeave

## Setup

Requires Python 3.12.

```bash
git clone <your-repo-url>
cd bloomberg-ai-signals
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Local Usage

### SSL on macOS (Homebrew Python)

If `python scraper.py` fails with `CERTIFICATE_VERIFY_FAILED`, you're likely on **Homebrew Python** (not python.org). The scraper auto-detects Homebrew's cert bundle. You can also set it manually:

```bash
export SSL_CERT_FILE=/opt/homebrew/etc/openssl@3/cert.pem
python scraper.py
```

### Run the scraper

Fetches Bloomberg Technology articles and updates `data/mentions.csv`:

```bash
python scraper.py
```

If the scraper runs multiple times on the same day, that day's rows are replaced (no duplicates).

### Run the dashboard

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

## Dashboard Sections

1. **Overview** — companies tracked, total records, latest date
2. **Today's Rankings** — companies sorted by mention count
3. **Historical Trend** — line chart for a selected company
4. **Biggest Movers** — day-over-day percent change for each company

## GitHub Actions

The workflow in `.github/workflows/daily_scrape.yml`:

- Runs every day at **00:00 UTC** (`cron: '0 0 * * *'`)
- Can be triggered manually via **workflow_dispatch**
- Installs dependencies, runs `scraper.py`, commits updated `data/mentions.csv`, and pushes to the repo

To enable scheduled runs, push this repo to GitHub and ensure Actions are enabled.

## Deploy on Streamlit Community Cloud (Free)

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app**
5. Select your repository, branch, and set **Main file path** to `app.py`
6. Deploy

The dashboard reads `data/mentions.csv` from the repo. GitHub Actions keeps the CSV updated daily, so the deployed app always reflects the latest scraped data.

## Project Structure

```
bloomberg-ai-signals/
├── app.py                  # Streamlit dashboard
├── scraper.py              # Bloomberg article scraper
├── companies.py            # Tracked company list
├── data/
│   └── mentions.csv        # Daily mention counts
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── daily_scrape.yml
```

## CSV Format

```
date,company,count
2026-06-07,NVIDIA,18
2026-06-07,AMD,12
```

One row per `(date, company)` combination.
