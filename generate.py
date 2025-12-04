#!/usr/bin/env python3
import os
import requests
import datetime
from feedgen.feed import FeedGenerator

TOKEN = os.environ.get("AQICN_TOKEN")
if not TOKEN:
    raise SystemExit("AQICN_TOKEN not found in environment")

API_URL = f"https://api.waqi.info/feed/shanghai/pudongjiancezhan/?token={TOKEN}"
OUT_DIR = "public"
OUT_FILE = os.path.join(OUT_DIR, "aqi.xml")
LAST_STATUS_FILE = os.path.join(OUT_DIR, "last_status.txt")
ALERT_THRESHOLD = 100

def fetch_aqi():
    r = requests.get(API_URL, timeout=15)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != "ok":
        raise RuntimeError(f"API error: {j}")
    return j["data"]["aqi"]

def ensure_outdir():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR, exist_ok=True)

def read_last_status():
    try:
        with open(LAST_STATUS_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def write_last_status(s):
    with open(LAST_STATUS_FILE, "w") as f:
        f.write(s)

def build_feed(aqi_value, changed):
    fg = FeedGenerator()
    fg.title("Shanghai Pudong AQI Updates")
    fg.link(href="https://aqicn.org/city/shanghai/pudongjiancezhan/")
    fg.description("AQI updates for Shanghai Pudong (Pudong Jiance Zhan) — scheduled updates + alerts")
    fg.language("en")

    now = datetime.datetime.utcnow()

    # Scheduled update
    e = fg.add_entry()
    e.id(str(now) + "-update")
    e.title(f"AQI: {aqi_value}")
    e.link(href="https://aqicn.org/city/shanghai/pudongjiancezhan/")
    e.description(f"Current AQI: {aqi_value}. Data source: AQICN.")
    e.pubDate(now)

    # Alert if state changed
    if changed:
        e2 = fg.add_entry()
        if aqi_value > ALERT_THRESHOLD:
            e2.title("⚠️ Air Pollution Alert: AQI above 100")
            e2.description(f"AQI is now {aqi_value} — above {ALERT_THRESHOLD}.")
        else:
            e2.title("✅ AQI Improved: Back below 100")
            e2.description(f"AQI is now {aqi_value} — below {ALERT_THRESHOLD}.")
        e2.id(str(now) + "-alert")
        e2.link(href="https://aqicn.org/city/shanghai/pudongjiancezhan/")
        e2.pubDate(now)

    return fg

def main():
    ensure_outdir()
    aqi_value = fetch_aqi()
    last = read_last_status()
    current_state = "above" if aqi_value > ALERT_THRESHOLD else "below"
    changed = (last != current_state)
    fg = build_feed(aqi_value, changed)
    fg.rss_file(OUT_FILE)
    write_last_status(current_state)
    print(f"Wrote {OUT_FILE} (AQI={aqi_value}). Changed:{changed}")

if __name__ == "__main__":
    main()
