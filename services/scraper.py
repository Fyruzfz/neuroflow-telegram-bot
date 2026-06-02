"""
NeuroFlow AI Bot - Web Scraping Service
Uses our existing web-scraper skill scripts
"""

import os
import sys
import subprocess
import csv
import json
from datetime import datetime

# Path to the scraper script
SCRAPER_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "..", "..",
    "hermes", "skills", "productivity", "web-scraper", "scripts", "web_scraper.py"
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


async def run_scraper(url: str, selectors: str = None) -> dict:
    """
    Run the web scraper on a given URL.
    Tries the Hermes web-scraper script first, falls back to requests+bs4.
    Returns {"success": bool, "count": int, "csv_path": str, "error": str}
    """
    # Primary: try the Hermes scraper skill script if it exists
    if os.path.exists(SCRAPER_SCRIPT):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")
            outfile = os.path.join(OUTPUT_DIR, f"scrape_{domain}_{timestamp}")

            cmd = [
                sys.executable, SCRAPER_SCRIPT,
                "--url", url,
                "--export", "csv",
                "--output", outfile,
            ]
            if selectors:
                cmd += ["--selectors", selectors]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                cwd=os.path.dirname(SCRAPER_SCRIPT),
            )

            if result.returncode == 0:
                csv_path = outfile + ".csv"
                json_path = outfile + ".json"
                if os.path.exists(csv_path):
                    with open(csv_path, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        count = sum(1 for _ in reader) - 1
                    return {"success": True, "count": max(0, count), "csv_path": csv_path}
                elif os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    _json_to_csv(json_path, csv_path)
                    return {"success": True, "count": len(data) if isinstance(data, list) else 1, "csv_path": csv_path}
        except Exception:
            pass  # Fall through to fallback

    # Fallback: use requests + bs4 directly (always works)
    return await _fallback_scrape(url)


async def _fallback_scrape(url: str) -> dict:
    """Simple fallback scraper using requests + BeautifulSoup."""
    import requests
    from bs4 import BeautifulSoup
    import re

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract common data
        rows = []
        # Find all links, paragraphs, tables
        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "a", "li", "td", "th"]):
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                rows.append({
                    "tag": elem.name,
                    "text": text[:200],
                    "href": elem.get("href", "") if elem.name == "a" else "",
                })

        if not rows:
            return {"success": False, "error": "No extractable content found on this page."}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")
        csv_path = os.path.join(OUTPUT_DIR, f"scrape_{domain}_{timestamp}.csv")

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tag", "text", "href"])
            writer.writeheader()
            writer.writerows(rows)

        return {"success": True, "count": len(rows), "csv_path": csv_path}

    except Exception as e:
        return {"success": False, "error": f"Fallback scraper error: {str(e)[:300]}"}


def _json_to_csv(json_path: str, csv_path: str):
    """Convert JSON scrape output to CSV."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    if not data:
        return

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
