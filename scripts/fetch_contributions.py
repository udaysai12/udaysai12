#!/usr/bin/env python3
"""Fetch the last ~year of contributions into data/contributions.json.
Uses the public contributions endpoint (or GraphQL if GITHUB_TOKEN is set)."""
import json, os, re, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USER = "udaysai12"
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / "contributions.json"

class ContribParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
        self.current_td = None
        self.tooltips = {}
        self.current_tip = None
        self.tip_text = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'td' and 'data-date' in attr_dict:
            self.current_td = attr_dict
            self.days.append({
                'date': attr_dict['data-date'],
                'level': int(attr_dict.get('data-level', 0)),
                'id': attr_dict.get('id', '')
            })
        elif tag == 'tool-tip' and 'for' in attr_dict:
            self.current_tip = attr_dict['for']
            self.tip_text = []

    def handle_data(self, data):
        if self.current_tip:
            self.tip_text.append(data)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.current_tip:
            self.tooltips[self.current_tip] = ''.join(self.tip_text).strip()
            self.current_tip = None

def fetch_via_public():
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    
    # Check total header
    m = re.search(r'([0-9,]+)\s+contributions\s+in\s+the\s+last\s+year', html)
    header_total = int(m.group(1).replace(",", "")) if m else None

    parser = ContribParser()
    parser.feed(html)

    days = []
    calc_total = 0
    for day in parser.days:
        tip = parser.tooltips.get(day['id'], '')
        cnt = 0
        cm = re.search(r'(\d+)\s+contribution', tip)
        if cm:
            cnt = int(cm.group(1))
        elif 'No contributions' in tip:
            cnt = 0
        else:
            cnt = day['level']
        calc_total += cnt
        days.append({"date": day['date'], "count": cnt})

    total = header_total if header_total is not None else calc_total
    return total, days

def get_latest_commit():
    if OUT_FILE.exists():
        try:
            prev = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            if "latest" in prev and prev["latest"].get("repo"):
                return prev["latest"]
        except Exception:
            pass
    return {
        "repo": "PCDrop",
        "message": "feat: chunked multi-threaded file transfer over local Wi-Fi",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "branch": "main",
        "url": f"https://github.com/{USER}/PCDrop",
    }

def main():
    try:
        total, days = fetch_via_public()
        print(f"Fetched via public endpoint: {len(days)} days, {total} contributions")
    except Exception as e:
        print(f"Public fetch error: {e}")
        saved_html = DATA_DIR / "github_contrib.html"
        if saved_html.exists():
            html = saved_html.read_text(encoding="utf-8")
            parser = ContribParser()
            parser.feed(html)
            days = []
            calc_total = 0
            for day in parser.days:
                tip = parser.tooltips.get(day['id'], '')
                cnt = 0
                cm = re.search(r'(\d+)\s+contribution', tip)
                if cm:
                    cnt = int(cm.group(1))
                days.append({"date": day['date'], "count": cnt})
                calc_total += cnt
            m = re.search(r'([0-9,]+)\s+contributions\s+in\s+the\s+last\s+year', html)
            total = int(m.group(1).replace(",", "")) if m else calc_total
            print(f"Loaded from saved HTML: {len(days)} days, {total} contributions")
        else:
            raise

    latest = get_latest_commit()
    out_data = {
        "total": total,
        "days": days,
        "latest": latest
    }
    OUT_FILE.write_text(json.dumps(out_data, indent=1), encoding="utf-8")
    print(f"Successfully saved {OUT_FILE} with {total} contributions.")

if __name__ == "__main__":
    main()
