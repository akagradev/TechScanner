import os
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
import requests
from bs4 import BeautifulSoup

from companies import COMPANIES

RSS_URL = "https://feeds.bloomberg.com/technology/news.rss"
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "mentions.csv"
MAX_ARTICLES = 50
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_ssl_verify():
    """Use system CA bundle when available (fixes Homebrew Python on macOS)."""
    env_cert = os.environ.get("SSL_CERT_FILE")
    if env_cert and os.path.exists(env_cert):
        return env_cert

    for cert_path in (
        "/opt/homebrew/etc/openssl@3/cert.pem",
        "/usr/local/etc/openssl@3/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if os.path.exists(cert_path):
            return cert_path

    return True


def ensure_csv_exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        pd.DataFrame(columns=["date", "company", "count"]).to_csv(CSV_PATH, index=False)


def fetch_rss_articles():
    response = requests.get(
        RSS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=get_ssl_verify()
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.content)
    articles = []

    for item in root.findall(".//item")[:MAX_ARTICLES]:
        title = item.findtext("title", default="").strip()
        description = item.findtext("description", default="").strip()
        link = item.findtext("link", default="").strip()

        if title and link:
            articles.append({"title": title, "description": description, "link": link})

    return articles


def fetch_article_content(url, fallback_description=""):
    try:
        response = requests.get(
            url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=get_ssl_verify()
        )
        response.raise_for_status()
    except requests.RequestException:
        return fallback_description

    soup = BeautifulSoup(response.text, "html.parser")

    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_text = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""

    paragraphs = [
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    ]
    body_text = " ".join(paragraphs)

    if body_text:
        return body_text
    if meta_text:
        return meta_text
    return fallback_description


def count_mentions(text, company):
    pattern = re.compile(r"\b" + re.escape(company) + r"\b", re.IGNORECASE)
    return len(pattern.findall(text))


def scrape_today():
    today = date.today().isoformat()
    articles = fetch_rss_articles()
    counts = {company: 0 for company in COMPANIES}

    for article in articles:
        content = fetch_article_content(article["link"], article["description"])
        full_text = f"{article['title']} {content}"

        for company in COMPANIES:
            counts[company] += count_mentions(full_text, company)

    return today, counts


def save_counts(today, counts):
    ensure_csv_exists()
    df = pd.read_csv(CSV_PATH)

    if not df.empty:
        df["date"] = df["date"].astype(str)
        df = df[df["date"] != today]

    new_rows = pd.DataFrame(
        [{"date": today, "company": company, "count": count} for company, count in counts.items()]
    )
    df = pd.concat([df, new_rows], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)


def main():
    today, counts = scrape_today()
    save_counts(today, counts)
    print(f"Scraped {today}: {sum(counts.values())} total mentions across {len(COMPANIES)} companies")


if __name__ == "__main__":
    main()
