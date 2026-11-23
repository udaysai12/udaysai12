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
    repositories(first:10,orderBy:{field:PUSHED_AT,direction:DESC},ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){
      nodes{
        name
        description
        url
        pushedAt
        defaultBranchRef{
          name
          target{
            ... on Commit{
              message
              committedDate
            }
          }
        }
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
    res_user = json.load(r)["data"]["user"]
    cal = res_user["contributionsCollection"]["contributionCalendar"]
    repos = res_user.get("repositories", {}).get("nodes", [])

days = [
    {"date": d["date"], "count": d["contributionCount"]}
    for w in cal["weeks"] for d in w["contributionDays"]
]

out_data = {"total": cal["totalContributions"], "days": days}

if repos:
    r0 = repos[0]
    target = (r0.get("defaultBranchRef") or {}).get("target") or {}
    out_data["latest"] = {
        "repo": r0.get("name", "PCDrop"),
        "message": target.get("message", "Recent activity").split("\n")[0],
        "date": (target.get("committedDate") or r0.get("pushedAt", ""))[:10],
        "branch": (r0.get("defaultBranchRef") or {}).get("name", "main"),
        "url": r0.get("url", f"https://github.com/{USER}"),
    }

out = Path(__file__).resolve().parent.parent / "data"
out.mkdir(exist_ok=True)
(out / "contributions.json").write_text(json.dumps(out_data, indent=1))
print("saved", len(days), "days,", cal["totalContributions"], "contributions")