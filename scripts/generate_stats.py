"""
Self-contained GitHub stats card generator.
Uses only the public REST API + the default GITHUB_TOKEN (no PAT needed).
Outputs generated/overview.svg and generated/languages.svg.
"""

import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "").strip()
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

if not USERNAME:
    print("GITHUB_REPOSITORY_OWNER not set", file=sys.stderr)
    sys.exit(1)

API = "https://api.github.com"


def gh_get(path):
    req = Request(f"{API}{path}")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-stats-script")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        print(f"GitHub API error on {path}: {e.code}", file=sys.stderr)
        return None


def get_all_repos(username):
    repos = []
    page = 1
    while True:
        batch = gh_get(f"/users/{username}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def main():
    user = gh_get(f"/users/{USERNAME}") or {}
    repos = get_all_repos(USERNAME)
    repos = [r for r in repos if not r.get("fork")]

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    public_repos = user.get("public_repos", len(repos))
    followers = user.get("followers", 0)

    lang_bytes = {}
    for r in repos:
        lang_url = r.get("languages_url")
        if not lang_url:
            continue
        path = lang_url.replace(API, "")
        data = gh_get(path) or {}
        for lang, count in data.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + count

    top_langs = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:5]
    total_lang_bytes = sum(v for _, v in top_langs) or 1

    os.makedirs("generated", exist_ok=True)
    write_overview(public_repos, total_stars, total_forks, followers)
    write_languages(top_langs, total_lang_bytes)


PALETTE = ["#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE", "#E0E7FF"]


def write_overview(repos, stars, forks, followers):
    stats = [
        ("Public Repos", repos),
        ("Total Stars", stars),
        ("Total Forks", forks),
        ("Followers", followers),
    ]
    row_h = 34
    height = 40 + row_h * len(stats)
    rows = ""
    for i, (label, value) in enumerate(stats):
        y = 40 + i * row_h
        rows += f'''
        <text x="20" y="{y}" fill="#9CA3AF" font-size="13" font-family="'JetBrains Mono', monospace">{label}</text>
        <text x="320" y="{y}" fill="#E5E7EB" font-size="13" font-family="'JetBrains Mono', monospace" text-anchor="end" font-weight="600">{value:,}</text>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="{height}" viewBox="0 0 340 {height}">
  <rect width="340" height="{height}" rx="10" fill="#0d1117" stroke="#30363d"/>
  <text x="20" y="24" fill="#6366F1" font-size="14" font-family="'JetBrains Mono', monospace" font-weight="700">GitHub Overview</text>
  {rows}
</svg>'''
    with open("generated/overview.svg", "w") as f:
        f.write(svg)


def write_languages(top_langs, total):
    height = 40 + 28 * len(top_langs)
    bars = ""
    for i, (lang, count) in enumerate(top_langs):
        pct = count / total * 100
        y = 40 + i * 28
        bar_w = max(2, pct * 1.6)
        color = PALETTE[i % len(PALETTE)]
        bars += f'''
        <text x="20" y="{y}" fill="#9CA3AF" font-size="12" font-family="'JetBrains Mono', monospace">{lang}</text>
        <rect x="120" y="{y - 10}" width="160" height="8" rx="4" fill="#21262d"/>
        <rect x="120" y="{y - 10}" width="{bar_w:.1f}" height="8" rx="4" fill="{color}"/>
        <text x="290" y="{y}" fill="#E5E7EB" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="end">{pct:.1f}%</text>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="{height}" viewBox="0 0 340 {height}">
  <rect width="340" height="{height}" rx="10" fill="#0d1117" stroke="#30363d"/>
  <text x="20" y="24" fill="#6366F1" font-size="14" font-family="'JetBrains Mono', monospace" font-weight="700">Top Languages</text>
  {bars}
</svg>'''
    with open("generated/languages.svg", "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
