#!/usr/bin/env python3
"""Fetch the last ~year of contributions into data/contributions.json."""
import json, os, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = "udaysai12"
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from,to:$to){
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
  }
}"""

now = datetime.now(timezone.utc)
variables = {
    "login": USER,
    "from": (now - timedelta(days=364)).isoformat(),
    "to": now.isoformat(),
}
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": variables}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]

days = [
    {"date": d["date"], "count": d["contributionCount"]}
    for w in cal["weeks"] for d in w["contributionDays"]
]
out = Path(__file__).resolve().parent.parent / "data"
out.mkdir(exist_ok=True)
(out / "contributions.json").write_text(
    json.dumps({"total": cal["totalContributions"], "days": days}, indent=1)
)
print("saved", len(days), "days,", cal["totalContributions"], "contributions")