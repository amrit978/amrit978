"""Generates the SVG assets for the profile README.

  python scripts/generate.py          -> refresh live data (repos, commits, heatmap, stats)
  python scripts/generate.py static   -> rebuild hero/about/headers/tiles/pills (edit colors here)
"""
import os, re, sys, json, html, textwrap, datetime, urllib.request
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
LIVE_REPOS = False
REPO_LIMIT = 6   # how many repo cards to show
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
SERIF = "Georgia, Palatino, 'Times New Roman', serif"
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
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r-1}" fill="none" stroke="{LINE}" stroke-width="2"/>')

# ---------------------------------------------------------------- dynamic
def project_cards():
    global LIVE_REPOS
    try:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
        LIVE_REPOS = True
    except Exception:
        repos = FALLBACK_REPOS  # API unavailable (e.g. rate limit): cards only, README left untouched
    repos = [r for r in repos if not r["fork"] and r["name"] not in SKIP_REPOS][:REPO_LIMIT]
    for i, r in enumerate(repos, 1):
        lang = LANG_OVERRIDE.get(r["name"], r["language"] or "")
        desc = r["description"] or "No description yet"
        wrapped = textwrap.wrap(desc, 40)
        lines = wrapped[:2]
        if len(wrapped) > 2:
            lines[1] = lines[1][:37] + "..."
        body = card_frame(392, 130)
        body += f'<text x="24" y="40" font-family="{SERIF}" font-size="21" font-weight="700" fill="{TXT}">{esc(r["name"][:28])}</text>'
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
        b += f'<text x="28" y="52" font-family="{SERIF}" font-size="36" font-weight="700" fill="{C1}">{val}</text>'
        b += f'<text x="28" y="76" font-family="{MONO}" font-size="13" fill="{MUTED}">{label}</text>'
        write(f"{OUT}/stat-{i}.svg", svg(190, 90, b))

def _swap(text, tag, inner):
    pat = re.compile(rf"(<!-- {tag}:START -->).*?(<!-- {tag}:END -->)", re.S)
    return pat.sub(lambda m: f"{m.group(1)}\n{inner}\n{m.group(2)}", text)

def update_readme(repos, commits):
    """Rewrite the repo + commit link blocks in README.md so links always match the cards."""
    with open("README.md", encoding="utf-8") as f:
        text = old = f.read()
    if repos is not None:
        rows = []
        for i, r in enumerate(repos, 1):
            url = r.get("html_url") or f"https://github.com/{USER}/{r['name']}"
            alt = html.escape(f"{r['name']}: {r.get('description') or 'no description yet'}", quote=True)
            rows.append(f'<a href="{url}"><img src="assets/generated/project-{i:02d}.svg" alt="{alt}" width="392"></a>')
        text = _swap(text, "REPOS", '<p align="center">\n' + "\n".join(rows) + "\n</p>")
    if commits is not None:
        rows = []
        for i in range(1, 7):
            img = f'<img src="assets/generated/commit-{i:02d}.svg" alt="recent commit {i}" width="392">'
            rows.append(f'<a href="{commits[i-1]["html_url"]}">{img}</a>' if i <= len(commits) else img)
        text = _swap(text, "COMMITS", '<p align="center">\n' + "\n".join(rows) + "\n</p>")
    if text != old:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(text)
        print("ok update_readme")

def placeholders():
    """Create stand-ins so the README has no broken images before the first Action run."""
    def missing(p):
        return not os.path.exists(p)
    for i in range(1, 7):
        p = f"{OUT}/commit-{i:02d}.svg"
        if missing(p):
            write(p, svg(392, 100, card_frame(392, 100) + f'<text x="24" y="56" font-family="{FONT}" font-size="15" fill="{MUTED}">filling in soon</text>'))
    if missing(f"{OUT}/heatmap.svg"):
        cells = "".join(f'<rect x="{52+x*15}" y="{46+y*15}" width="12" height="12" rx="3" fill="{LEVELS[0]}"/>' for x in range(53) for y in range(7))
        write(f"{OUT}/heatmap.svg", svg(867, 201, f'<rect width="867" height="201" rx="14" fill="{CARD}"/>{cells}'))
    for i, label in enumerate(["contributions", "current streak", "longest streak", "active days"], 1):
        p = f"{OUT}/stat-{i}.svg"
        if missing(p):
            write(p, svg(190, 90, card_frame(190, 90) + f'<text x="28" y="52" font-family="{SERIF}" font-size="36" font-weight="700" fill="{C1}">--</text>'
                  f'<text x="28" y="76" font-family="{MONO}" font-size="13" fill="{MUTED}">{label}</text>'))

def dynamic():
    repos = commits = None
    try:
        r = project_cards()
        repos = r if LIVE_REPOS else None
        print("ok project_cards", "(live)" if LIVE_REPOS else "(offline fallback)")
    except Exception as e:
        print("skip project_cards", e)
    try:
        commits = commit_cards()
        print("ok commit_cards")
    except Exception as e:
        print("skip commit_cards", e)
    try:
        heatmap_and_stats()
        print("ok heatmap_and_stats")
    except Exception as e:
        print("skip heatmap_and_stats", e)
    placeholders()
    try:
        update_readme(repos, commits)
    except Exception as e:
        print("skip update_readme", e)

# ---------------------------------------------------------------- static
def wavy(x, y, width, amp=5, step=36):
    n = max(2, int(width // step))
    return f'<path d="M{x} {y} q{step/2} {-amp} {step} 0' + f' t{step} 0' * (n-1) + f'" fill="none" stroke="{C2}" stroke-width="3" stroke-linecap="round" opacity="0.7"/>'

def static():
    # hero: handwritten-ish, warm, no terminal tropes
    hero = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="#3a2216"/></linearGradient></defs>'
            f'<rect width="1200" height="320" rx="22" fill="url(#bg)"/>'
            f'<circle cx="820" cy="250" r="64" fill="none" stroke="{C3}" stroke-width="7" opacity="0.18"/>'  # coffee ring stain
            f'<text x="84" y="92" font-family="{SERIF}" font-style="italic" font-size="30" fill="{MUTED}">hi, i\'m</text>'
            f'<text x="78" y="190" font-family="{SERIF}" font-weight="700" font-size="112" fill="{C1}">Amrit</text>'
            f'<path d="M84 206 q60 -10 120 0 t120 0 t120 0" fill="none" stroke="{C2}" stroke-width="4" stroke-linecap="round" opacity="0.7"/>')
    lines = [("third-year CSE (AI &amp; ML) student from Asansol", "0;0.03;0.30;0.33;1", "0;1;1;0;0"),
             ("secretary at DevSoc AEC, so yes, i&#8217;m the one sending the reminders", "0;0.33;0.36;0.63;0.66;1", "0;0;1;1;0;0"),
             ("learning javascript, linux &amp; full-stack, one broken thing at a time", "0;0.66;0.69;0.96;1", "0;0;1;1;0")]
    for t, kt, v in lines:
        hero += (f'<text x="84" y="260" opacity="0" font-family="{SERIF}" font-style="italic" font-size="26" fill="{TXT}">{t}'
                 f'<animate attributeName="opacity" dur="10s" repeatCount="indefinite" keyTimes="{kt}" values="{v}"/></text>')
    hero += (f'<g transform="translate(930,55) rotate(-4 100 120)">'
             f'<path d="M30 60 Q20 20 40 5" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.1;0.6;0.1" dur="3s" repeatCount="indefinite"/></path>'
             f'<path d="M70 60 Q60 20 80 0" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.6;0.1;0.6" dur="3s" repeatCount="indefinite"/></path>'
             f'<path d="M110 60 Q100 25 120 8" fill="none" stroke="{C1}" stroke-width="5" stroke-linecap="round" opacity="0.5"><animate attributeName="opacity" values="0.1;0.6;0.1" dur="2.4s" repeatCount="indefinite"/></path>'
             f'<path d="M0 90 H140 V150 Q140 200 90 200 H50 Q0 200 0 150 Z" fill="{C3}"/>'
             f'<path d="M140 105 H165 Q195 105 195 140 Q195 175 160 175 H138" fill="none" stroke="{C3}" stroke-width="14" stroke-linecap="round"/>'
             f'<rect x="0" y="90" width="140" height="14" fill="{C1}" opacity="0.35"/>'
             f'<ellipse cx="70" cy="215" rx="115" ry="12" fill="{C3}" opacity="0.6"/></g>')
    write(f"{STATIC}/hero.svg", svg(1200, 320, hero))

    # about: short bullet points
    rows = ["third-year CSE (AI &amp; ML) at Asansol Engineering College",
            "secretary &amp; management lead, DevSoc AEC",
            "learning javascript, linux &amp; full-stack",
            "building small things: a timer, an expense tracker, a voice assistant",
            "some of it works, the rest is still being fixed"]
    ab = card_frame(1200, 312, 22)
    ab += f'<text x="44" y="64" font-family="{SERIF}" font-style="italic" font-weight="700" font-size="32" fill="{C1}">a little about me</text>'
    ab += wavy(44, 80, 260)
    for i, t in enumerate(rows):
        y = 134 + i*38
        ab += f'<circle cx="52" cy="{y-8}" r="5" fill="{C2}"/>'
        ab += f'<text x="74" y="{y}" font-family="{SERIF}" font-size="24" fill="{TXT}">{t}</text>'
    write(f"{STATIC}/about.svg", svg(1200, 312, ab))

    # section headers: serif italic, wavy underline, lowercase and personal
    for name, label in [("header-projects", "stuff i&#8217;ve built"), ("head-repositories", "the repos"),
                        ("head-activity", "what i touched lately"), ("head-contributions", "days i actually committed"),
                        ("header-tech", "tools &amp; where to find me"), ("head-languages", "languages i write in"),
                        ("head-frameworks", "everything else i use"), ("head-connect", "say hi")]:
        big = name.startswith("header")
        size = 40 if big else 28
        h = 76 if big else 58
        wid = int(len(label) * size * 0.46)
        body = (f'<text x="12" y="{size+4}" font-family="{SERIF}" font-style="italic" font-weight="700" font-size="{size}" fill="{C1}">{label}</text>'
                + wavy(12, size+18, wid))
        write(f"{OUT}/{name}.svg", svg(1200, h, body))

    # tiles: coffee tones, each slightly tilted like pinned notes
    tiles = [("java", "Java", "Jv"), ("python", "Python", "Py"), ("c", "C", "C"), ("cplusplus", "C++", "C++"),
             ("javascript", "JavaScript", "JS"), ("html5", "HTML", "&lt;/&gt;"), ("css3", "CSS", "{ }"),
             ("git", "Git", "git"), ("vercel", "Vercel", "&#9650;"), ("figma", "Figma", "Fg")]
    tones = [C1, C2, "#d9a066"]
    tilts = [-2.5, 1.5, -1, 2.5, -1.8]
    for n, (slug, label, glyph) in enumerate(tiles):
        color = tones[n % 3]
        body = (f'<g transform="translate(5,6) rotate({tilts[n % 5]} 50 55)">' + card_frame(100, 110, 16) +
                f'<circle cx="50" cy="44" r="26" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="2"/>'
                f'<text x="50" y="52" text-anchor="middle" font-family="{MONO}" font-size="20" font-weight="700" fill="{color}">{glyph}</text>'
                f'<text x="50" y="96" text-anchor="middle" font-family="{SERIF}" font-size="14" fill="{TXT}">{label}</text></g>')
        write(f"{OUT}/tile-{slug}.svg", svg(110, 122, body))

    for slug, label, color in [("linkedin", "find me on LinkedIn", C1), ("instagram", "or on instagram", C2),
                               ("email", "or just email me", "#d9a066")]:
        body = (f'<rect width="256" height="48" rx="24" fill="{CARD}"/><rect x="1" y="1" width="254" height="46" rx="23" fill="none" stroke="{color}" stroke-width="2"/>'
                f'<text x="128" y="30" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="17" fill="{TXT}">{label}</text>')
        write(f"{OUT}/pill-{slug}.svg", svg(256, 48, body))

    write(f"{OUT}/signoff.svg", svg(1200, 110,
        f'<rect width="1200" height="110" rx="22" fill="{CARD}"/><rect x="2" y="2" width="1196" height="106" rx="20" fill="none" stroke="{LINE}" stroke-width="2"/>'
        f'<text x="600" y="66" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="28" fill="{C1}">that&#8217;s it. thanks for scrolling all the way down.</text>'))

if __name__ == "__main__":
    static() if "static" in sys.argv else dynamic()
