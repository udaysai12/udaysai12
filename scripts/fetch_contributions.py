#!/usr/bin/env python3
"""Fetch the latest contributions and Git statistics from GitHub.
Supports both GitHub GraphQL API (when GITHUB_TOKEN is available)
and the public GitHub endpoints / HTML scraper."""
import json, os, re, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USER = "udaysai12"
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / "contributions.json"
TOKEN = os.environ.get("GITHUB_TOKEN")

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
        if tag == "td" and "data-date" in attr_dict:
            self.current_td = attr_dict
            self.days.append({
                "date": attr_dict["data-date"],
                "level": int(attr_dict.get("data-level", 0)),
                "id": attr_dict.get("id", "")
            })
        elif tag == "tool-tip" and "for" in attr_dict:
            self.current_tip = attr_dict["for"]
            self.tip_text = []

    def handle_data(self, data):
        if self.current_tip:
            self.tip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.current_tip:
            self.tooltips[self.current_tip] = "".join(self.tip_text).strip()
            self.current_tip = None

def get_headers():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if TOKEN:
        headers["Authorization"] = f"bearer {TOKEN}"
    return headers

def fetch_contributions_html():
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")
    
    m = re.search(r'([0-9,]+)\s+contributions\s+in\s+the\s+last\s+year', html)
    header_total = int(m.group(1).replace(",", "")) if m else None

    parser = ContribParser()
    parser.feed(html)

    days = []
    calc_total = 0
    for day in parser.days:
        tip = parser.tooltips.get(day["id"], "")
        cnt = 0
        cm = re.search(r'(\d+)\s+contribution', tip)
        if cm:
            cnt = int(cm.group(1))
        elif "No contributions" in tip:
            cnt = 0
        else:
            cnt = day["level"]
        calc_total += cnt
        days.append({"date": day["date"], "count": cnt})

    total = header_total if header_total is not None else calc_total
    return total, days

def fetch_user_stats():
    stats = {"public_repos": 30, "followers": 3, "total_stars": 0}
    try:
        url = f"https://api.github.com/users/{USER}"
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            stats["public_repos"] = data.get("public_repos", stats["public_repos"])
            stats["followers"] = data.get("followers", stats["followers"])
    except Exception as e:
        print(f"Warning: could not fetch user stats: {e}")

    try:
        url = f"https://api.github.com/users/{USER}/repos?per_page=100"
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = json.load(resp)
            stats["total_stars"] = sum(r.get("stargazers_count", 0) for r in repos)
            stats["total_forks"] = sum(r.get("forks_count", 0) for r in repos)
    except Exception as e:
        print(f"Warning: could not fetch repos stats: {e}")

    return stats

def fetch_latest_commit():
    # 1. Try events API
    try:
        url = f"https://api.github.com/users/{USER}/events"
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req, timeout=10) as resp:
            events = json.load(resp)
            for e in events:
                if e.get("type") == "PushEvent":
                    repo_full = e.get("repo", {}).get("name", "")
                    repo_name = repo_full.split("/")[-1] if "/" in repo_full else repo_full
                    ref = e.get("payload", {}).get("ref", "").replace("refs/heads/", "")
                    date_str = e.get("created_at", "")[:10]
                    commits = e.get("payload", {}).get("commits", [])
                    msg = commits[-1].get("message", "") if commits else ""
                    if not msg or msg == "Recent commit activity":
                        # Attempt to query commits API for actual message
                        try:
                            c_url = f"https://api.github.com/repos/{repo_full}/commits?per_page=1"
                            c_req = urllib.request.Request(c_url, headers=get_headers())
                            with urllib.request.urlopen(c_req, timeout=5) as c_resp:
                                c_data = json.load(c_resp)
                                if c_data:
                                    msg = c_data[0].get("commit", {}).get("message", "")
                        except Exception:
                            pass
                    if not msg:
                        msg = "Recent commit & activity"
                    return {
                        "repo": repo_name,
                        "message": msg.split("\n")[0],
                        "date": date_str,
                        "branch": ref or "main",
                        "url": f"https://github.com/{repo_full}"
                    }
    except Exception as e:
        print(f"Warning: could not fetch latest commit from events: {e}")

    # Fallback to existing or default
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
        "url": f"https://github.com/{USER}/PCDrop"
    }

def main():
    # 1. Contributions calendar
    try:
        total, days = fetch_contributions_html()
        print(f"Fetched live contributions: {len(days)} days, {total} total")
    except Exception as e:
        print(f"Live fetch failed ({e}), checking existing contributions.json...")
        if OUT_FILE.exists():
            prev = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            total = prev.get("total", 1022)
            days = prev.get("days", [])
        else:
            raise

    # 2. User & Repository Stats
    user_stats = fetch_user_stats()
    print(f"User stats: {user_stats}")

    # 3. Latest Commit
    latest = fetch_latest_commit()
    print(f"Latest activity: {latest['repo']} @ {latest['date']}: {latest['message']}")

    # 4. Save combined data
    out_data = {
        "total": total,
        "public_repos": user_stats.get("public_repos", 30),
        "followers": user_stats.get("followers", 3),
        "total_stars": user_stats.get("total_stars", 0),
        "days": days,
        "latest": latest,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    OUT_FILE.write_text(json.dumps(out_data, indent=1), encoding="utf-8")
    print(f"Successfully saved {OUT_FILE} with all Git statistics.")

if __name__ == "__main__":
    main()
