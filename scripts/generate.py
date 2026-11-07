"""Generates the SVG assets for the profile README.

  python scripts/generate.py          -> refresh live data (repos, commits, heatmap, stats)
  python scripts/generate.py static   -> rebuild hero/about/headers/tiles/pills (edit colors here)
"""
import os, sys, json, textwrap, datetime, urllib.request
from xml.sax.saxutils import escape as esc

USER = "amrit978"
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = "assets/generated"
STATIC = "assets"
# GitHub guesses languages from files; fix any that are misleading
LANG_OVERRIDE = {"pomodoro-timer": "C++"}
LANG_COLORS = {"Python": "#e0b07a", "C++": "#d98c5f", "HTML": "#c46a3c", "CSS": "#a8794f",
               "JavaScript": "#f0d49a", "Java": "#b5651d", "C": "#c9b8a6"}
SKIP_REPOS = {USER}
FALLBACK_REPOS = [
    {"name": "portfolio", "language": "CSS", "description": None, "fork": False, "homepage": "https://amrit-kumar.vercel.app/"},
    {"name": "pomodoro-timer", "language": "Makefile", "description": "A simple desktop Pomodoro timer built with C++ and Qt6 Widgets.", "fork": False, "homepage": "https://pomodoro-timer-amrit5.vercel.app"},
    {"name": "Expense-Tracker", "language": "Python", "description": None, "fork": False, "homepage": "https://expense-tracker-amrit5.vercel.app"},
    {"name": "Tip-Calculator", "language": "HTML", "description": None, "fork": False, "homepage": None},
    {"name": "jarvis", "language": "Python", "description": None, "fork": False, "homepage": None},
]

C1, C2, C3 = "#f0c892", "#c98a4b", "#9c5a32"  # latte -> caramel -> mocha
BG, CARD, LINE, TXT, MUTED = "#1a0f0a", "#2a1a12", "#4e3326", "#f5e6d3", "#b89b84"  # espresso, roast, cream
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "Consolas, Menlo, monospace"
DEFS = (f'<defs><linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C1}"/>'
        f'<stop offset="0.5" stop-color="{C2}"/><stop offset="1" stop-color="{C3}"/></linearGradient></defs>')

def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}{body}</svg>'

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def api(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-readme-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def card_frame(w, h, r=14):
    return (f'<rect width="{w}" height="{h}" rx="{r}" fill="{CARD}"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r-1}" fill="none" stroke="{LINE}" stroke-width="2"/>'
            f'<rect x="0" y="18" width="4" height="{h-36}" rx="2" fill="url(#ac)"/>')

# ---------------------------------------------------------------- dynamic
def project_cards():
    try:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    except Exception:
        repos = FALLBACK_REPOS  # API unavailable (e.g. rate limit): use last known data
    repos = [r for r in repos if not r["fork"] and r["name"] not in SKIP_REPOS][:6]
    for i, r in enumerate(repos, 1):
        lang = LANG_OVERRIDE.get(r["name"], r["language"] or "")
        desc = r["description"] or "No description yet"
        wrapped = textwrap.wrap(desc, 40)
        lines = wrapped[:2]
        if len(wrapped) > 2:
            lines[1] = lines[1][:37] + "..."
        body = card_frame(392, 130)
        body += f'<text x="24" y="40" font-family="{FONT}" font-size="20" font-weight="700" fill="{TXT}">{esc(r["name"][:28])}</text>'
        for j, ln in enumerate(lines):
            body += f'<text x="24" y="{66+j*20}" font-family="{FONT}" font-size="14" fill="{MUTED}">{esc(ln)}</text>'
        if lang:
            body += (f'<circle cx="30" cy="108" r="6" fill="{LANG_COLORS.get(lang, C2)}"/>'
                     f'<text x="44" y="113" font-family="{MONO}" font-size="13" fill="{TXT}">{esc(lang)}</text>')
        if r.get("homepage"):
            body += (f'<rect x="300" y="94" width="72" height="26" rx="13" fill="none" stroke="url(#ac)" stroke-width="1.5"/>'
                     f'<text x="336" y="112" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{TXT}">live</text>')
        write(f"{OUT}/project-{i:02d}.svg", svg(392, 130, body))
    return repos

def ago(iso):
    d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (datetime.datetime.now(datetime.timezone.utc) - d).days
    return "today" if days == 0 else "1 day ago" if days == 1 else f"{days} days ago"

def commit_cards():
    res = api(f"https://api.github.com/search/commits?q=author:{USER}&sort=author-date&order=desc&per_page=6")
    items = res.get("items", [])
    for i in range(1, 7):
        body = card_frame(392, 100)
        if i <= len(items):
            it = items[i-1]
            repo = it["repository"]["name"]
            msg = it["commit"]["message"].splitlines()[0]
            msg = msg if len(msg) <= 44 else msg[:41] + "..."
            body += (f'<text x="24" y="36" font-family="{MONO}" font-size="14" fill="{C1}">{esc(repo[:32])}</text>'
                     f'<text x="24" y="62" font-family="{FONT}" font-size="16" fill="{TXT}">{esc(msg)}</text>'
                     f'<text x="24" y="84" font-family="{FONT}" font-size="12" fill="{MUTED}">{ago(it["commit"]["author"]["date"])}</text>')
        else:
            body += f'<text x="24" y="56" font-family="{FONT}" font-size="15" fill="{MUTED}">no more commits yet</text>'
        write(f"{OUT}/commit-{i:02d}.svg", svg(392, 100, body))
    return items

LEVELS = ["#3d2a20", "#6b4430", "#94603c", "#c58849", "#f0c892"]

def heatmap_and_stats():
    q = ("query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions "
         "weeks{contributionDays{contributionCount date}}}}}}")
    data = api("https://api.github.com/graphql", {"query": q, "variables": {"u": USER}})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    cell, gap, ox, oy = 12, 3, 52, 46
    w = ox + len(weeks)*(cell+gap) + 20
    h = oy + 7*(cell+gap) + 50
    body = f'<rect width="{w}" height="{h}" rx="14" fill="{CARD}"/><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="13" fill="none" stroke="{LINE}" stroke-width="2"/>'
    # day labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body += f'<text x="{ox-10}" y="{oy+row*(cell+gap)+cell-2}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">{name}</text>'
    # month labels + cells
    prev_month = None
    for wi, wk in enumerate(weeks):
        d0 = datetime.date.fromisoformat(wk["contributionDays"][0]["date"])
        if d0.month != prev_month:
            if prev_month is not None or d0.day <= 7:
                body += f'<text x="{ox+wi*(cell+gap)}" y="{oy-14}" font-family="{MONO}" font-size="11" fill="{MUTED}">{d0.strftime("%b")}</text>'
            prev_month = d0.month
        for di, d in enumerate(wk["contributionDays"]):
            n = d["contributionCount"]
            lvl = 0 if n == 0 else 1 if n < 2 else 2 if n < 4 else 3 if n < 7 else 4
            body += f'<rect x="{ox+wi*(cell+gap)}" y="{oy+di*(cell+gap)}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[lvl]}"/>'
    # legend
    lx, ly = w - 20 - 5*(cell+gap) - 70, h - 30
    body += f'<text x="{lx}" y="{ly+cell-2}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">Less</text>'
    for i, col in enumerate(LEVELS):
        body += f'<rect x="{lx+10+i*(cell+gap)}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{col}"/>'
    body += f'<text x="{lx+10+5*(cell+gap)+4}" y="{ly+cell-2}" font-family="{MONO}" font-size="11" fill="{MUTED}">More</text>'
    write(f"{OUT}/heatmap.svg", svg(w, h, body))

    counts = [d["contributionCount"] for d in days if d["date"] <= datetime.date.today().isoformat()]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, seen_today = 0, False
    for idx, c in enumerate(reversed(counts)):
        if c:
            cur += 1
        elif idx == 0:
            continue  # today may still be empty
        else:
            break
    stats = [("contributions", cal["totalContributions"]), ("current streak", cur),
             ("longest streak", longest), ("active days", sum(1 for c in counts if c))]
    for i, (label, val) in enumerate(stats, 1):
        b = card_frame(190, 90)
        b += f'<text x="28" y="52" font-family="{FONT}" font-size="34" font-weight="800" fill="url(#ac)">{val}</text>'
        b += f'<text x="28" y="76" font-family="{MONO}" font-size="13" fill="{MUTED}">{label}</text>'
        write(f"{OUT}/stat-{i}.svg", svg(190, 90, b))

def placeholders():
    """Create stand-ins so the README has no broken images before the first Action run."""
    def missing(p):
        return not os.path.exists(p)
    for i in range(1, 7):
        p = f"{OUT}/commit-{i:02d}.svg"
        if missing(p):
            write(p, svg(392, 100, card_frame(392, 100) + f'<text x="24" y="56" font-family="{FONT}" font-size="15" fill="{MUTED}">updates after first Action run</text>'))
    if missing(f"{OUT}/heatmap.svg"):
        cells = "".join(f'<rect x="{52+x*15}" y="{46+y*15}" width="12" height="12" rx="3" fill="{LEVELS[0]}"/>' for x in range(53) for y in range(7))
        write(f"{OUT}/heatmap.svg", svg(867, 201, f'<rect width="867" height="201" rx="14" fill="{CARD}"/>{cells}'))
    for i, label in enumerate(["contributions", "current streak", "longest streak", "active days"], 1):
        p = f"{OUT}/stat-{i}.svg"
        if missing(p):
            write(p, svg(190, 90, card_frame(190, 90) + f'<text x="28" y="52" font-family="{FONT}" font-size="34" font-weight="800" fill="url(#ac)">--</text>'
                  f'<text x="28" y="76" font-family="{MONO}" font-size="13" fill="{MUTED}">{label}</text>'))

def dynamic():
    for fn in (project_cards, commit_cards, heatmap_and_stats):
        try:
            fn()
            print("ok", fn.__name__)
        except Exception as e:  # keep the previous files if the API hiccups
            print("skip", fn.__name__, e)
    placeholders()

# ---------------------------------------------------------------- static
def static():
    hero = (f'<defs><pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#fff" stroke-opacity="0.04"/></pattern>'
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="0.6" stop-color="#2b1810"/><stop offset="1" stop-color="#4a2c1a"/></linearGradient></defs>'
            f'<rect width="1200" height="320" rx="18" fill="url(#bg)"/><rect width="1200" height="320" rx="18" fill="url(#g)"/>'
            f'<circle cx="1030" cy="90" r="130" fill="{C2}" fill-opacity="0.08"/><circle cx="1100" cy="250" r="90" fill="{C1}" fill-opacity="0.08"/>'
            f'<text x="80" y="80" font-family="{MONO}" font-size="20" fill="{MUTED}">~/amrit978 $ whoami</text>'
            f'<text x="76" y="180" font-family="{FONT}" font-size="104" font-weight="800" fill="url(#ac)">Amrit</text>'
            f'<rect x="390" y="108" width="8" height="84" fill="{C1}"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    lines = [("CSE (AI &amp; ML) @ Asansol Engineering College", "0;0.03;0.30;0.33;1", "0;1;1;0;0"),
             ("Secretary &amp; Management Lead @ DevSoc AEC", "0;0.33;0.36;0.63;0.66;1", "0;0;1;1;0;0"),
             ("building things in Python, C++ &amp; the web", "0;0.66;0.69;0.96;1", "0;0;1;1;0")]
    for t, kt, v in lines:
        hero += (f'<text x="80" y="245" opacity="0" font-family="{MONO}" font-size="26" fill="#c9d1d9">&gt; {t}'
                 f'<animate attributeName="opacity" dur="9s" repeatCount="indefinite" keyTimes="{kt}" values="{v}"/></text>')

    hero += (f'<g transform="translate(930,70)">'
             f'<path d="M30 60 Q20 20 40 5" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.1;0.6;0.1" dur="3s" repeatCount="indefinite"/></path>'
             f'<path d="M70 60 Q60 20 80 0" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.6;0.1;0.6" dur="3s" repeatCount="indefinite"/></path>'
             f'<path d="M110 60 Q100 25 120 8" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.1;0.6;0.1" dur="2.4s" repeatCount="indefinite"/></path>'
             f'<path d="M0 90 H140 V150 Q140 200 90 200 H50 Q0 200 0 150 Z" fill="{C3}"/>'
             f'<path d="M140 105 H165 Q195 105 195 140 Q195 175 160 175 H138" fill="none" stroke="{C3}" stroke-width="14" stroke-linecap="round"/>'
             f'<rect x="0" y="90" width="140" height="14" fill="{C1}" opacity="0.35"/>'
             f'<ellipse cx="70" cy="215" rx="115" ry="12" fill="{C3}" opacity="0.6"/></g>')
    write(f"{STATIC}/hero.svg", svg(1200, 320, hero))

    rows = [("focus", "Web development, Java &amp; AI/ML"), ("role", "Secretary &amp; Management Lead, DevSoc AEC"),
            ("learning", "JavaScript, Linux, full-stack development"), ("languages", "C, C++, Java, Python, JavaScript"),
            ("building", "side projects, one at a time"), ("status", "Student. Learner. Shipper.")]
    ab = card_frame(1200, 330, 18)
    ab += f'<text x="40" y="58" font-family="{MONO}" font-size="26" font-weight="700" fill="url(#ac)">a little about me</text>'
    for i, (k, v) in enumerate(rows):
        y = 108 + i*40
        ab += f'<text x="40" y="{y}" font-family="{MONO}" font-size="20" fill="{C1}">{k}</text>'
        ab += f'<text x="220" y="{y}" font-family="{FONT}" font-size="21" fill="{TXT}">{v}</text>'
    write(f"{STATIC}/about.svg", svg(1200, 330, ab))

    for name, label in [("header-projects", "Things I'm building"), ("head-repositories", "Repositories"),
                        ("head-activity", "Recent Activity"), ("head-contributions", "Contribution Activity"),
                        ("header-tech", "Tech Stack &amp; Connect"), ("head-languages", "Languages"),
                        ("head-frameworks", "Frameworks &amp; Tools"), ("head-connect", "Find me around the internet")]:
        big = name.startswith("header")
        size = 38 if big else 26
        body = (f'<text x="10" y="{44 if big else 34}" font-family="{MONO}" font-size="{size}" font-weight="700" fill="url(#ac)">// {label}</text>'
                f'<rect x="10" y="{58 if big else 46}" width="{1180 if big else 300}" height="3" rx="1.5" fill="url(#ac)" opacity="0.5"/>')
        write(f"{OUT}/{name}.svg", svg(1200, 70 if big else 56, body))

    tiles = [("java", "Java", "Jv", "#ED8B00"), ("python", "Python", "Py", "#3572A5"), ("c", "C", "C", "#9aa0a6"),
             ("cplusplus", "C++", "C++", "#f34b7d"), ("javascript", "JavaScript", "JS", "#f1e05a"),
             ("html5", "HTML", "&lt;/&gt;", "#e34c26"), ("css3", "CSS", "{ }", "#9b6bd6"),
             ("git", "Git", "git", "#F05033"), ("vercel", "Vercel", "&#9650;", "#e6edf3"), ("figma", "Figma", "Fg", "#F24E1E")]
    tones = [C1, C2, "#d9a066"]
    for n, (slug, label, glyph, color) in enumerate(tiles):
        color = tones[n % 3]
        body = (card_frame(100, 110, 16) +
                f'<circle cx="50" cy="44" r="26" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="2"/>'
                f'<text x="50" y="52" text-anchor="middle" font-family="{MONO}" font-size="20" font-weight="700" fill="{color}">{glyph}</text>'
                f'<text x="50" y="96" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{TXT}">{label}</text>')
        write(f"{OUT}/tile-{slug}.svg", svg(100, 110, body))

    for slug, label, color in [("linkedin", "LinkedIn: Amrit Kumar", C1), ("instagram", "Instagram: @amrit_kuma_r", C2),
                               ("email", "itsmeamrit@proton.me", "#d9a066")]:
        body = (f'<rect width="256" height="48" rx="24" fill="{CARD}"/><rect x="1" y="1" width="254" height="46" rx="23" fill="none" stroke="{color}" stroke-width="2"/>'
                f'<circle cx="26" cy="24" r="6" fill="{color}"/>'
                f'<text x="44" y="29" font-family="{FONT}" font-size="14" fill="{TXT}">{label}</text>')
        write(f"{OUT}/pill-{slug}.svg", svg(256, 48, body))

    write(f"{OUT}/signoff.svg", svg(1200, 110,
        f'<rect width="1200" height="110" rx="18" fill="{BG}"/><rect x="2" y="2" width="1196" height="106" rx="16" fill="none" stroke="url(#ac)" stroke-opacity="0.6" stroke-width="2"/>'
        f'<text x="600" y="64" text-anchor="middle" font-family="{MONO}" font-size="28" fill="#c9d1d9">still learning. still shipping.</text>'))

if __name__ == "__main__":
    static() if "static" in sys.argv else dynamic()