"""Collect public GitHub counts and render an offline, zero-safe engagement chart.

Uses the GitHub CLI for authenticated, read-only API calls. No application imports,
tracking, third-party plotting dependency or changes to repository settings.
"""

import argparse
from datetime import date, datetime, timezone
from html import escape
import json
import math
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    ("stars", "Stars"),
    ("forks", "Forks"),
    ("contributors", "Human contributors"),
    ("documented_adoption", "Documented external uses"),
)


def log_count(value):
    """Keep unavailable observations missing; zero is a measured value."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Counts must be nonnegative integers or null")
    return math.log1p(value)


def api(endpoint, paginate=False):
    args = ["gh", "api", "--hostname", "github.com", endpoint]
    if paginate:
        args.extend(["--paginate", "--slurp"])
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout or "[]")
    return [item for page in data for item in page] if paginate else data


def adoption_counts(ledger, repositories, owner):
    if ledger.get("schema") != 1 or not isinstance(ledger.get("entries"), list):
        raise ValueError("Unsupported adoption ledger")
    counts = {repo: set() for repo in repositories}
    for entry in ledger["entries"]:
        repo = entry["repository"]
        if repo not in counts:
            raise ValueError(f"Adoption entry is outside the collected scope: {repo}")
        project = entry["project_key"].strip().casefold()
        independent_owner = entry["independent_owner"].strip().casefold()
        if not project or not independent_owner or independent_owner == owner.casefold():
            raise ValueError("Adoption requires an identified independent project")
        if not entry["evidence_url"].startswith("https://") or not entry["description"].strip():
            raise ValueError("Adoption requires public HTTPS evidence and a description")
        if date.fromisoformat(entry["reviewed_on"]) > date.today():
            raise ValueError("Adoption review cannot be dated in the future")
        # Multiple links to the same project count only once for each repository.
        counts[repo].add(project)
    return {repo: len(projects) for repo, projects in counts.items()}


def contributor_counts(records, owner):
    humans = {r["login"].casefold() for r in records if r.get("type") == "User"}
    return len(humans), len(humans - {owner.casefold()})


def collect(owner, ledger):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", owner):
        raise ValueError("Invalid GitHub account name")
    repositories = api(f"users/{owner}/repos?type=owner&per_page=100", paginate=True)
    repositories = sorted(
        (r for r in repositories if not r["private"] and not r["fork"]
         and r["owner"]["login"].casefold() == owner.casefold()),
        key=lambda r: r["full_name"],
    )
    adoption = adoption_counts(ledger, [r["full_name"] for r in repositories], owner)
    rows = []
    for repo in repositories:
        name = repo["full_name"]
        source = f"https://api.github.com/repos/{name}/contributors?per_page=100"
        try:
            records = api(f"repos/{name}/contributors?per_page=100", paginate=True)
            humans, external = contributor_counts(records, owner)
            status = "available"
        except (subprocess.CalledProcessError, ValueError, KeyError):
            humans, external = None, None
            status = "unavailable; retry collection"
        raw = {"stars": repo["stargazers_count"], "forks": repo["forks_count"],
               "contributors": humans, "external_contributors": external,
               "documented_adoption": adoption[name]}
        rows.append({"repository": name, "url": repo["html_url"],
                     "archived": repo["archived"], "raw": raw,
                     "log1p": {key: log_count(raw[key]) for key, _ in METRICS},
                     "contributor_status": status,
                     "sources": [repo["url"], source]})
    return {"schema": 1, "owner": owner,
            "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": "Public, directly owned, non-fork repositories; archived included",
            "transform": "natural log(1 + count); unavailable values stay null",
            "adoption_basis": "Reviewed ledger; documented lower bound, not total use",
            "adoption_evidence": ledger["entries"], "repositories": rows}


def render(snapshot):
    rows = snapshot["repositories"]
    maximum = max([10] + [r["raw"][key] or 0 for r in rows for key, _ in METRICS])
    ceiling = 10 ** math.ceil(math.log10(maximum))
    ticks = [0, 1] + [10 ** p for p in range(1, int(math.log10(ceiling)) + 1)]
    domain = math.log1p(ceiling)
    height = 205 + 122 * len(rows)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{height}" '
           'viewBox="0 0 1120 ' + str(height) + '" role="img" aria-labelledby="title desc">',
           '<title id="title">Public repository engagement, log scale with raw counts</title>',
           '<desc id="desc">All panels share natural log of one plus the count. '
           'Contributors include the owner and exclude bots. External adoption counts only '
           'reviewed public evidence. Missing values are not zero.</desc>',
           '<rect width="100%" height="100%" rx="12" fill="#ffffff"/>',
           '<g font-family="system-ui, sans-serif" fill="#18333e">']

    def text(x, y, value, size=13, color="#18333e", weight="400"):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
                   f'font-weight="{weight}">{escape(str(value))}</text>')

    text(28, 38, f'{snapshot["owner"]} / Public repository engagement', 23, weight="650")
    text(28, 64, f'Observed {snapshot["collected_at"]} · Shared scale: ln(1 + count)',
         13, "#526870")
    for j, (_, label) in enumerate(METRICS):
        text(270 + j * 207, 104, label, 13, weight="650")
    for i, row in enumerate(rows):
        y = 143 + 122 * i
        text(28, y, row["repository"].split("/", 1)[1], 17, weight="650")
        ext = row["raw"]["external_contributors"]
        text(28, y + 23, f'Outside contributors: {ext if ext is not None else "unavailable"}',
             12, "#526870")
        for j, (key, _) in enumerate(METRICS):
            x = 270 + j * 207
            count = row["raw"][key]
            label = "Unavailable" if count is None else str(count)
            if key == "documented_adoption" and count == 0:
                label = "0 documented"
            text(x, y, label, 18, weight="650")
            svg.append(f'<path d="M{x} {y+20}h175" stroke="#d7e1e5" stroke-width="6"/>')
            if count is not None:
                end = x + 175 * log_count(count) / domain
                svg.append(f'<path d="M{x} {y+20}H{end:.2f}" stroke="#007f87" '
                           'stroke-width="6"/>')
                svg.append(f'<circle cx="{end:.2f}" cy="{y+20}" r="4" fill="#007f87"/>')
            for tick in ticks:
                tx = x + 175 * log_count(tick) / domain
                text(round(tx - 3, 1), y + 45, tick, 11, "#526870")
    base = height - 57
    text(28, base, "Counts describe interest, contribution and documented use separately; no composite ranking.", 13)
    text(28, base + 23, "Human contributors include the owner. No documented adoption is not proof of no adoption.",
         13, "#526870")
    svg.append("</g></svg>\n")
    return "\n".join(svg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="zakimaths")
    parser.add_argument("--adoption", type=Path, default=ROOT / "docs/engagement/adoption.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "docs/engagement/snapshot.json")
    parser.add_argument("--chart", type=Path, default=ROOT / "docs/engagement/engagement.svg")
    parser.add_argument("--offline", action="store_true", help="Render an existing snapshot without network")
    args = parser.parse_args()
    if args.offline:
        snapshot = json.loads(args.snapshot.read_text())
    else:
        snapshot = collect(args.owner, json.loads(args.adoption.read_text()))
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(json.dumps(snapshot, indent=2) + "\n")
    args.chart.parent.mkdir(parents=True, exist_ok=True)
    args.chart.write_text(render(snapshot))
    print(f'Reported {len(snapshot["repositories"])} public owned repositories.')


if __name__ == "__main__":
    main()
