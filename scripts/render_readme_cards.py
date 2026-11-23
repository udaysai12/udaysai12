#!/usr/bin/env python3
"""Render animated SVG cards from data/contributions.json into cards/.
Run with STATIC=1 to render the final frame with no animation."""
import base64, html, json, math, os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
OUT.mkdir(exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"

# ---------- content (edit freely) ----------
NAME = "Uday Sai Setti"
ROLE = "Full Stack, Mobile & AI / ML Engineer"
TAGLINE = "Building modern web apps, cross-platform mobile apps, and applied AI systems."

LATEST = {
    "repo": "PCDrop",
    "message": "feat: chunked multi-threaded file transfer over local Wi-Fi",
    "date": "Recently updated",
    "branch": "main",
    "url": "https://github.com/udaysai12/PCDrop",
}

TILES = [  # file, label, big number, caption, description, bg, text colour
    ("build", "BUILD", "42", "projects delivered", "Web, mobile and backend", "#2F5BFF", "#FFFFFF"),
    ("ship", "SHIP", "6", "production apps", "Healthcare, education, e-commerce", "#E5484D", "#FFFFFF"),
    ("lead", "LEAD", "2", "developers mentored", "Sprints and code reviews", "#F5B700", "#16130F"),
]

PERSONAL_REPOS = [  # name, description, stack, url
    ("PCDrop", "Local Wi-Fi file transfer — no cloud, cross-platform", "Electron · React · TypeScript · Flutter", "https://github.com/udaysai12/PCDrop"),
    ("Sketch-to-Image AR", "Real-time augmented reality generation pipeline", "Python · MediaPipe · TFLite · OpenCV", "https://github.com/udaysai12"),
    ("TIE", "ATS resume analyzer scoring profiles out of 100", "React · Django REST · Docker", "https://github.com/udaysai12"),
    ("Palm AR Reveal", "3D object reveal via palm gesture recognition", "MediaPipe · Three.js · Web Audio", "https://github.com/udaysai12"),
]

COLLAB_REPOS = [  # name, description, stack, url
    ("Errand LearnHub", "Edtech platform with web, Android app, admin & REST API", "React · Expo · Node · MongoDB", "https://github.com/udaysai12"),
    ("WayM8", "Real-time ride-sharing with live tracking & SOS safety", "Flutter · Riverpod · Node · Redis", "https://github.com/udaysai12"),
    ("Jatayuv AI", "Intelligent mobile assistant and utility platform", "React Native · Expo · FastAPI", "https://github.com/udaysai12"),
    ("Dentoji", "Comprehensive clinic practice & patient management system", "MERN Stack · Tailwind CSS · Docker", "https://github.com/udaysai12"),
]

PAPER, INK, BLUE, MUTED, LINE = "#F6F1E7", "#16130F", "#2F5BFF", "#8A8274", "#DDD5C4"
LEVELS = ["#E8E1D0", "#C9D4FF", "#92A9FF", "#5A7DFF", BLUE]

# ---------- fonts and css ----------
def font_face(family, name):
    p = ROOT / "fonts" / name
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{b64})}}"

CSS = font_face("Serif", "serif.woff") + font_face("Sans", "sans.woff") + """
text{font-family:'Sans',-apple-system,'Segoe UI',system-ui,sans-serif}
.serif{font-family:'Serif',Georgia,'Times New Roman',serif}
.c{transform-box:fill-box;transform-origin:center}
.b{transform-box:fill-box;transform-origin:bottom}
.rise{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}
.pop{animation:pop .45s cubic-bezier(.2,.8,.2,1) both}
.grow{animation:grow .7s cubic-bezier(.2,.8,.2,1) both}
.swing{animation:swing .9s cubic-bezier(.2,.9,.3,1.2) both}
.pulse{animation:pulse 1.8s ease-in-out infinite}
.nudge{animation:nudge 1.6s ease-in-out infinite}
.shine{animation:shine 4s ease-in-out infinite}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes swing{0%{opacity:0;transform:translateY(46px) rotate(-5deg)}70%{opacity:1;transform:translateY(-4px) rotate(.8deg)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(1.5)}}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
@keyframes shine{0%,60%{transform:translateX(-120%)}100%{transform:translateX(260%)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
if STATIC:
    CSS += "*{animation:none!important}"

def esc(s):
    return html.escape(str(s))

def svg(w, h, body, bg=PAPER, stroke=LINE):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
        f"<style>{CSS}</style>"
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="{bg}" stroke="{stroke}" stroke-width="2"/>'
        f"{body}</svg>"
    )

def t(x, y, s, size, fill, cls="", delay=0.0, anim="rise", weight=400, anchor="start"):
    c = f"{anim} {cls}".strip()
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
        f'text-anchor="{anchor}" class="{c}" style="animation-delay:{delay}s">{esc(s)}</text>'
    )

# ---------- data ----------
data = json.loads((ROOT / "data" / "contributions.json").read_text())
days = data["days"]
total = data["total"]

def streaks(ds):
    longest = run = 0
    for d in ds:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    cur, seq = 0, ds[:]
    if seq and seq[-1]["count"] == 0:  # today may not have commits yet
        seq = seq[:-1]
    for d in reversed(seq):
        if d["count"] > 0:
            cur += 1
        else:
            break
    return cur, longest

cur_streak, best_streak = streaks(days)
active = sum(1 for d in days if d["count"] > 0)
busiest = max(days, key=lambda d: d["count"])

# ---------- hero ----------
def hero():
    b = t(48, 80, "Hello, I'm", 22, MUTED, delay=0.1)
    b += t(48, 148, NAME, 70, INK, "serif", 0.3)
    b += (
        f'<clipPath id="nm"><rect x="48" y="90" width="600" height="70"/></clipPath>'
        f'<g clip-path="url(#nm)"><rect class="shine" x="48" y="90" width="90" height="70" '
        f'fill="{BLUE}" opacity=".18" transform="skewX(-18)"/></g>'
    )
    b += f'<circle class="pulse c" cx="54" cy="186" r="5" fill="{BLUE}"/>'
    b += t(70, 192, ROLE, 18, INK, delay=0.7)
    b += t(48, 222, TAGLINE, 16, MUTED, delay=0.9)
    return svg(900, 250, b)

# ---------- blue contribution graph ----------
def graph():
    first = date.fromisoformat(days[0]["date"])
    off = (first.weekday() + 1) % 7  # weeks start on Sunday
    mx = max(d["count"] for d in days) or 1
    b = t(28, 40, "Contributions in the last year", 18, INK, "serif", 0.9)
    b += t(872, 40, f"{total} total", 16, BLUE, delay=1.0, anchor="end", weight=600)
    for i, d in enumerate(days):
        w, r = divmod(i + off, 7)
        c = d["count"]
        lvl = 0 if c == 0 else min(4, math.ceil(4 * c / mx))
        x, y = 24 + w * 16, 58 + r * 16
        b += (
            f'<rect class="pop c" x="{x}" y="{y}" width="12" height="12" rx="3" '
            f'fill="{LEVELS[lvl]}" style="animation-delay:{1.0 + w * 0.03:.2f}s"/>'
        )
    return svg(900, 196, b)

# ---------- monthly chart + stats ----------
def months():
    buckets = {}
    for d in days:
        buckets[d["date"][:7]] = buckets.get(d["date"][:7], 0) + d["count"]
    keys = sorted(buckets)[-12:]
    vals = [buckets[k] for k in keys]
    mx, best = max(vals) or 1, vals.index(max(vals))
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

    stats = [
        ("active days", active),
        ("current streak", cur_streak),
        ("longest streak", best_streak),
        (f"busiest day ({busiest['date'][5:]})", busiest["count"]),
    ]
    b = ""
    for i, (label, val) in enumerate(stats):
        x = 28 + i * 215
        b += t(x, 56, val, 38, INK, "serif", 1.6 + i * 0.1)
        b += t(x, 78, label, 13, MUTED, delay=1.7 + i * 0.1)

    base, maxh = 262, 120
    for i, (k, v) in enumerate(zip(keys, vals)):
        h = max(4, v / mx * maxh)
        x = 40 + i * 70
        fill = BLUE if i == best else INK
        op = 1 if i == best else 0.8
        b += (
            f'<rect class="grow b" x="{x}" y="{base - h:.1f}" width="44" height="{h:.1f}" rx="6" '
            f'fill="{fill}" opacity="{op}" style="animation-delay:{1.9 + i * 0.07:.2f}s"/>'
        )
        b += t(x + 22, base + 20, names[int(k[5:]) - 1], 13, MUTED, delay=2.0 + i * 0.07, anchor="middle")
    b += t(40 + best * 70 + 22, base - max(4, vals[best] / mx * maxh) - 10, vals[best],
           16, BLUE, delay=3.0, anim="pop", cls="c", weight=700, anchor="middle")
    return svg(900, 300, b)

# ---------- tiles ----------
def tile(i, spec):
    _, label, num, cap, desc, bg, fg = spec
    d = 3.2 + i * 0.25
    b = t(28, 46, label, 15, fg, delay=d, weight=700)
    b += f'<text class="nudge" x="372" y="46" font-size="22" fill="{fg}" text-anchor="end">→</text>'
    b += t(28, 140, num, 92, fg, "serif", d + 0.2)
    b += t(28, 172, cap, 18, fg, delay=d + 0.3, weight=600)
    b += t(28, 202, desc, 14, fg, delay=d + 0.4)
    inner = (
        f'<rect x="1" y="1" width="398" height="228" rx="16" fill="{bg}"/>' + b
    )
    body = f'<g class="swing" style="animation-delay:{d}s">{inner}</g>'
    return svg(400, 230, body, bg=bg, stroke=bg)

# ---------- latest commit card ----------
def latest_card():
    lt = data.get("latest") or LATEST
    repo_name = lt.get("repo", "PCDrop")
    commit_msg = lt.get("message", "feat: chunked multi-threaded file transfer over local Wi-Fi")
    date_str = lt.get("date", "Recently updated")
    branch = lt.get("branch", "main")
    
    b = f'<circle class="pulse c" cx="42" cy="40" r="5" fill="#10B981"/>'
    b += t(58, 44, "LATEST COMMIT & RECENT ACTIVITY", 12, "#10B981", delay=0.1, weight=700)
    b += t(862, 44, f"Branch: {branch} · {date_str}", 13, MUTED, delay=0.2, anchor="end")
    b += t(42, 88, repo_name, 34, INK, "serif", delay=0.3)
    b += f'<text class="nudge" x="862" y="88" font-size="24" fill="{INK}" text-anchor="end">→</text>'
    
    if len(commit_msg) > 90:
        commit_msg = commit_msg[:87] + "..."
    b += t(42, 118, commit_msg, 15, MUTED, delay=0.5)
    return svg(900, 144, b)

# ---------- repo cards ----------
def repo_card(i, spec, badge="PERSONAL", badge_color="#2F5BFF"):
    name, desc, stack = spec[:3]
    d = 4.4 + i * 0.12
    b = t(28, 34, badge.upper(), 11, badge_color, delay=d, weight=700)
    b += t(28, 70, name, 28, INK, "serif", delay=d + 0.1)
    b += f'<text class="nudge" x="572" y="70" font-size="22" fill="{INK}" text-anchor="end">→</text>'
    b += t(28, 104, desc, 14, INK, delay=d + 0.2)
    b += t(28, 134, stack, 12, badge_color, delay=d + 0.3, weight=600)
    return svg(600, 160, b)

# ---------- write ----------
def write(name, content):
    (OUT / f"{name}.svg").write_text(content)

write("hero", hero())
write("latest", latest_card())
write("graph", graph())
write("months", months())
for i, spec in enumerate(TILES):
    write(spec[0], tile(i, spec))
for i, spec in enumerate(PERSONAL_REPOS, start=1):
    write(f"repo-{i}", repo_card(i - 1, spec, badge="Personal Project", badge_color="#2F5BFF"))
for i, spec in enumerate(COLLAB_REPOS, start=1):
    write(f"collab-{i}", repo_card(i - 1, spec, badge="Collaboration / Team", badge_color="#059669"))

total_cards = 4 + len(TILES) + len(PERSONAL_REPOS) + len(COLLAB_REPOS)
print("rendered", total_cards, "cards", "(static)" if STATIC else "")