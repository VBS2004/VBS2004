"""
neofetch-style profile card.
Builds dark_mode.svg and light_mode.svg from card/portrait.txt, card/bonnet.txt
and live GitHub stats (GraphQL + the default GITHUB_TOKEN).
"""

import os
import sys
import json
from datetime import date
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "VBS2004").strip()
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
JOINED = date(2020, 6, 14)  # GitHub account creation date

ROOT = Path(__file__).resolve().parent.parent
CARD = Path(__file__).resolve().parent

THEMES = {
    "dark": {"bg": "#12161C", "text": "#D2D9E2", "art": "#C3CBD5", "key": "#F0A35E", "value": "#9CC7FF", "dots": "#56606D"},
    "light": {"bg": "#F6F8FA", "text": "#24292F", "art": "#3B434C", "key": "#A44D00", "value": "#0B57C9", "dots": "#8C959F"},
}

WIDTH, HEIGHT = 1000, 780
LINE_CHARS = 57  # right-hand column width, in characters


def fetch_stats():
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
        contributionsCollection { totalCommitContributions }
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) {
          totalCount
          nodes { stargazerCount }
        }
      }
    }"""
    body = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode()
    req = Request("https://api.github.com/graphql", data=body)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("User-Agent", "profile-card-script")
    with urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if "errors" in data:
        print(data["errors"], file=sys.stderr)
        sys.exit(1)
    u = data["data"]["user"]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "followers": u["followers"]["totalCount"],
    }


def uptime(start, today):
    years = today.year - start.year
    months = today.month - start.month
    days = today.day - start.day
    if days < 0:
        months -= 1
        prev_month_end = date(today.year, today.month, 1).toordinal() - 1
        days += date.fromordinal(prev_month_end).day
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


# a line is a list of (css class, text) parts; "fill" marks where the dot leader goes
def kv(key, value):
    keys = key.split(".")
    parts = [("dots", ". ")]
    for i, k in enumerate(keys):
        if i:
            parts.append((None, "."))
        parts.append(("key", k))
    parts += [(None, ":"), ("fill", None), ("value", value)]
    return parts


def header(title):
    return [(None, title), ("rule", None)]


def stat_pair(left, right):
    return [("dots", ". ")] + left + [("fill", None)] + right


def layout(parts):
    used = sum(len(t) for c, t in parts if t)
    out = []
    for c, t in parts:
        if c == "fill":
            out.append(("dots", " " + "." * max(LINE_CHARS - used - 2, 2) + " "))
        elif c == "rule":
            out.append(("dots", " " + "—" * max(LINE_CHARS - used - 1, 2)))
        else:
            out.append((c, t))
    return out


def lines(stats):
    s = stats
    return [
        [("bold", "venkat@balaji"), ("rule", None)],
        kv("OS", "Arch Linux · Omarchy (Hyprland)"),
        kv("Uptime", uptime(JOINED, date.today()) + " on GitHub"),
        kv("Host", "IDFC FIRST Bank"),
        kv("Kernel", "Application Engineer"),
        kv("Previous", "AlgoAnalytics, Samsung PRISM"),
        kv("GPU", "RTX 3050 4GB, GTX 1650 4GB (send help)"),
        kv("IDE", "VS Code, Zed, Neovim"),
        [("dots", ".")],
        kv("Languages.Code", "Python, Go, Java, JavaScript"),
        kv("Languages.ML", "PyTorch, LoRA, GRPO, RAG"),
        kv("Hobbies", "Mechanical keyboards, Forza"),
        [],
        header("- Achievements"),
        kv("Kaggle", "Notebooks Expert"),
        kv("Zelestra×AWS", "15th / 500+"),
        kv("CIBMTR", "Top 150 / 1,200+"),
        kv("AWS", "Solutions Architect, Associate"),
        [],
        header("- Contact"),
        kv("Email", "venkatbalaji2004@gmail.com"),
        kv("LinkedIn", "venkat-balaji-s"),
        [],
        header("- GitHub Stats"),
        stat_pair(
            [("key", "Repos"), (None, ": "), ("value", str(s["repos"])), (None, " {"), ("key", "Contributed"),
             (None, ": "), ("value", str(s["contributed"])), (None, "}")],
            [("key", "Stars"), (None, ": "), ("value", str(s["stars"]))],
        ),
        stat_pair(
            [("key", "Commits"), (None, ": "), ("value", f"{s['commits']:,}"), ("dots", " (past year)")],
            [("key", "Followers"), (None, ": "), ("value", str(s["followers"]))],
        ),
    ]


def svg(theme, stats):
    c = THEMES[theme]
    portrait = (CARD / "portrait.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    bonnet = (CARD / "bonnet.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    mono = "ui-monospace,SFMono-Regular,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
    braille = "'DejaVu Sans Mono','Segoe UI Symbol','Apple Braille',monospace"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{WIDTH}px" height="{HEIGHT}px" font-family="{mono}" font-size="15px">',
        "<style>",
        f".key{{fill:{c['key']}}} .value{{fill:{c['value']}}} .dots{{fill:{c['dots']}}} .bold{{font-weight:700}}",
        "text,tspan{white-space:pre}",
        "</style>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{c["bg"]}" rx="15"/>',
        f'<text x="24" y="38" fill="{c["art"]}">',
    ]
    for i, row in enumerate(portrait):
        out.append(f'<tspan x="24" y="{38 + i * 20}">{escape(row)}</tspan>')
    out.append("</text>")

    out.append(f'<text x="450" y="38" fill="{c["text"]}">')
    for i, parts in enumerate(lines(stats)):
        y = 38 + i * 20
        spans = "".join(
            f'<tspan class="{cls}">{escape(t)}</tspan>' if cls else escape(t)
            for cls, t in layout(parts)
        )
        out.append(f'<tspan x="450" y="{y}">{spans}</tspan>')
    out.append("</text>")

    out.append(f'<line x1="24" y1="552" x2="{WIDTH - 24}" y2="552" stroke="{c["dots"]}" stroke-dasharray="4 4"/>')
    out.append(f'<text x="{WIDTH // 2}" y="585" text-anchor="middle" font-family="{braille}" font-size="13px" fill="{c["key"]}">')
    for i, row in enumerate(bonnet):
        out.append(f'<tspan x="{WIDTH // 2}" y="{585 + i * 15}">{escape(row)}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    stats = fetch_stats()
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, stats), encoding="utf-8")
    print("wrote dark_mode.svg and light_mode.svg", stats)


if __name__ == "__main__":
    main()
