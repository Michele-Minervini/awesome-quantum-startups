#!/usr/bin/env python3
"""Generate README.md and data/startups.csv from the canonical dataset data/startups.json.

The JSON file is the single source of truth. Run this script after editing it:

    python3 scripts/generate.py

Use --check to verify (in CI) that README.md and the CSV are in sync with the JSON
without writing anything:

    python3 scripts/generate.py --check
"""

import csv
import io
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, "data", "startups.json")
DATA_CSV = os.path.join(ROOT, "data", "startups.csv")
README = os.path.join(ROOT, "README.md")

# Canonical category order. Must match the "category" values used in the dataset.
CATEGORIES = [
    "Quantum Computing Hardware",
    "Software, Algorithms & Error Correction",
    "Cloud & Access Platforms",
    "Quantum Sensing & Metrology",
    "Quantum Communication & Networking",
    "Quantum Security & Post-Quantum Cryptography",
    "Components & Enabling Technologies",
    "Applications, Consulting & Services",
]

# Short anchors / blurbs per category, shown under each heading.
CATEGORY_BLURB = {
    "Quantum Computing Hardware": "Companies building quantum processors and full-stack quantum computers, across every qubit modality.",
    "Software, Algorithms & Error Correction": "SDKs, compilers, simulators, error-correction, and algorithm/middleware developers (hardware-agnostic).",
    "Cloud & Access Platforms": "Cloud aggregators, orchestration layers, and access platforms that deliver quantum compute as a service.",
    "Quantum Sensing & Metrology": "Quantum sensors, magnetometers, gravimeters, atomic clocks, timing, and quantum imaging.",
    "Quantum Communication & Networking": "QKD, the quantum internet, entanglement distribution, repeaters, and quantum-secure telecom.",
    "Quantum Security & Post-Quantum Cryptography": "Post-quantum cryptography, quantum-safe security, and quantum random number generators (QRNG).",
    "Components & Enabling Technologies": "Cryogenics, control electronics, lasers/photonics, materials, fabrication, packaging, and test & measurement.",
    "Applications, Consulting & Services": "End-use applications (chemistry, finance, logistics, ML), consulting, education, talent, and investment.",
}

CSV_FIELDS = [
    "name", "website", "hq_country", "hq_city", "founded",
    "category", "subsector", "modality", "company_type", "status",
    "acquired_by", "acquired_year", "description", "notes",
]

# company_type values that get their own separated reference section.
BIG_TECH = "big-tech-division"
PUBLIC = "public-company"


def load():
    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "companies" in data:
        data = data["companies"]
    if not isinstance(data, list):
        raise SystemExit("data/startups.json must be a JSON array of company objects (or {\"companies\": [...]}).")
    for c in data:
        for k in CSV_FIELDS:
            c.setdefault(k, "")
    return data


def cell(s):
    """Sanitize a string for use inside a Markdown table cell."""
    s = (s or "").replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()
    return s


def name_cell(c):
    name = cell(c["name"])
    badge = ""
    if c.get("company_type") == PUBLIC:
        badge = " 📈"
    status = (c.get("status") or "").strip().lower()
    if status in ("acquired", "merged"):
        by = cell(c.get("acquired_by"))
        year = cell(c.get("acquired_year"))
        if by and year:
            badge += f" _({status} by {by}, {year})_"
        elif by:
            badge += f" _({status} by {by})_"
        else:
            badge += f" _({status})_"
    elif status == "defunct":
        badge += " _(defunct)_"
    elif status == "uncertain":
        badge += " _(unverified)_"
    web = (c.get("website") or "").strip()
    if web:
        return f"[{name}]({web}){badge}"
    return f"{name}{badge}"


def focus_cell(c):
    parts = []
    mod = cell(c.get("modality"))
    sub = cell(c.get("subsector"))
    if mod:
        parts.append(mod)
    if sub:
        parts.append(sub)
    return " · ".join(parts)


def hq_cell(c):
    city = cell(c.get("hq_city"))
    country = cell(c.get("hq_country"))
    if city and country:
        return f"{city}, {country}"
    return country or city or ""


def table(companies):
    rows = ["| Company | HQ | Founded | Focus | Description |",
            "| --- | --- | --- | --- | --- |"]
    for c in sorted(companies, key=lambda x: x["name"].lower()):
        rows.append("| {} | {} | {} | {} | {} |".format(
            name_cell(c), hq_cell(c), cell(c.get("founded")),
            focus_cell(c), cell(c.get("description"))))
    return "\n".join(rows)


def big_tech_table(companies):
    rows = ["| Organization | HQ | Quantum focus | Notes |",
            "| --- | --- | --- | --- |"]
    for c in sorted(companies, key=lambda x: x["name"].lower()):
        focus = focus_cell(c) or cell(c.get("category"))
        rows.append("| {} | {} | {} | {} |".format(
            name_cell(c), hq_cell(c), focus, cell(c.get("description"))))
    return "\n".join(rows)


def public_table(companies):
    rows = ["| Company | HQ | Category | Description |",
            "| --- | --- | --- | --- |"]
    for c in sorted(companies, key=lambda x: x["name"].lower()):
        rows.append("| {} | {} | {} | {} |".format(
            name_cell(c), hq_cell(c), cell(c.get("category")), cell(c.get("description"))))
    return "\n".join(rows)


def slug(title):
    out = []
    for ch in title.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -":
            out.append("-")
    return "".join(out)


def build_readme(data):
    total = len(data)
    by_cat = {cat: [c for c in data if c.get("category") == cat] for cat in CATEGORIES}
    # Main sector tables exclude big-tech divisions (they get their own section).
    main = {cat: [c for c in lst if c.get("company_type") != BIG_TECH] for cat, lst in by_cat.items()}
    big = [c for c in data if c.get("company_type") == BIG_TECH]
    public = [c for c in data if c.get("company_type") == PUBLIC]

    countries = {}
    for c in data:
        k = c.get("hq_country") or "Unknown"
        countries[k] = countries.get(k, 0) + 1
    top_countries = sorted(countries.items(), key=lambda kv: (-kv[1], kv[0]))[:12]

    listed = sum(len(v) for v in main.values())

    out = io.StringIO()
    w = out.write

    w("# Awesome Quantum Startups [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)\n\n")
    w("> A curated directory of companies building quantum technology: "
      "quantum computing, sensing, communication, security, and the components that make it all work.\n\n")
    w(f"**{total} organizations** tracked across **{len([c for c in CATEGORIES if main[c] or by_cat[c]])} sectors** "
      f"and **{len(countries)} countries**. Last updated: {date.today().isoformat()}.\n\n")
    w("This list covers pure-play startups and scale-ups, publicly traded quantum companies (marked 📈), "
      "university spin-outs, and the quantum divisions of large technology and enterprise organizations "
      "(listed separately). It is auto-generated from [`data/startups.json`](data/startups.json); "
      "see [Contributing](#contributing) to add or fix an entry.\n\n")

    # Table of contents
    w("## Contents\n\n")
    for cat in CATEGORIES:
        if main[cat]:
            w(f"- [{cat}](#{slug(cat)}) ({len(main[cat])})\n")
    if big:
        w(f"- [Big Tech & Large-Enterprise Quantum Initiatives](#big-tech--large-enterprise-quantum-initiatives) ({len(big)})\n")
    if public:
        w(f"- [Publicly Traded Pure-Play Quantum Companies](#publicly-traded-pure-play-quantum-companies) ({len(public)})\n")
    w("- [Statistics](#statistics)\n")
    w("- [Related Lists & Resources](#related-lists--resources)\n")
    w("- [Contributing](#contributing)\n")
    w("- [Disclaimer](#disclaimer)\n")
    w("- [License](#license)\n\n")

    # Sector sections
    for cat in CATEGORIES:
        if not main[cat]:
            continue
        w(f"## {cat}\n\n")
        w(f"{CATEGORY_BLURB.get(cat, '')}\n\n")
        w(table(main[cat]))
        w("\n\n[⬆ Back to top](#contents)\n\n")

    # Big tech
    if big:
        w("## Big Tech & Large-Enterprise Quantum Initiatives\n\n")
        w("Major technology, hardware, telecom, defense, and finance organizations with dedicated quantum "
          "programs. These are not standalone startups, so they are listed separately from the sector tables above.\n\n")
        w(big_tech_table(big))
        w("\n\n[⬆ Back to top](#contents)\n\n")

    # Public companies
    if public:
        w("## Publicly Traded Pure-Play Quantum Companies\n\n")
        w("Quantum-first companies that trade on public markets (also listed within their sector above).\n\n")
        w(public_table(public))
        w("\n\n[⬆ Back to top](#contents)\n\n")

    # Stats
    w("## Statistics\n\n")
    w(f"- **Total organizations:** {total}\n")
    w(f"- **Listed in sector tables:** {listed}\n")
    if big:
        w(f"- **Big-tech / enterprise divisions:** {len(big)}\n")
    if public:
        w(f"- **Publicly traded pure-plays:** {len(public)}\n")
    w("\n**By sector:**\n\n")
    w("| Sector | Count |\n| --- | --- |\n")
    for cat in CATEGORIES:
        w(f"| {cat} | {len(by_cat[cat])} |\n")
    w("\n**Top countries / regions:**\n\n")
    w("| Country | Count |\n| --- | --- |\n")
    for country, n in top_countries:
        w(f"| {country} | {n} |\n")
    w("\n[⬆ Back to top](#contents)\n\n")

    # Related
    w("## Related Lists & Resources\n\n")
    w("- [The Quantum Insider](https://thequantuminsider.com/): quantum industry news and company intelligence.\n")
    w("- [Quantum Computing Report](https://quantumcomputingreport.com/): news, players, and market tracking.\n")
    w("- [QED-C](https://quantumconsortium.org/): the US Quantum Economic Development Consortium.\n")
    w("- [toptierstartups: The Ultimate List of Quantum Computing Startups](https://www.toptierstartups.com/the-ultimate-list-of-quantum-computing-startups/)\n")
    w("- [Wikipedia: Companies involved in quantum computing or communication](https://en.wikipedia.org/wiki/List_of_companies_involved_in_quantum_computing_or_communication)\n")
    w("\n[⬆ Back to top](#contents)\n\n")

    # Contributing
    w("## Contributing\n\n")
    w("Contributions are very welcome! To add, update, or remove a company, edit "
      "[`data/startups.json`](data/startups.json) and run `python3 scripts/generate.py` to "
      "regenerate this README and the CSV, then open a pull request. See "
      "[CONTRIBUTING.md](CONTRIBUTING.md) for the entry schema and guidelines. "
      "You can also just [open an issue](../../issues/new/choose) and we'll add it.\n\n")

    # Disclaimer
    w("## Disclaimer\n\n")
    w("This directory is compiled from public sources for informational purposes only. "
      "Founding years, locations, categorizations, and funding/listing status may be incomplete or out of date, "
      "and inclusion here is not an endorsement. Found an error? Please open an issue or PR. "
      "Company names and trademarks belong to their respective owners.\n\n")

    # License
    w("## License\n\n")
    w("To the extent possible under law, the contributors have waived all copyright and related or neighboring "
      "rights to this dataset and list ([CC0 1.0](LICENSE)).\n")

    return out.getvalue()


def build_csv(data):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for c in sorted(data, key=lambda x: (x.get("category", ""), x["name"].lower())):
        writer.writerow({k: (c.get(k) or "") for k in CSV_FIELDS})
    return buf.getvalue()


def main():
    check = "--check" in sys.argv
    data = load()
    readme = build_readme(data)
    csv_text = build_csv(data)

    if check:
        # The "Last updated" date is regenerated from the system clock, so it
        # legitimately differs between when the README was generated and when CI
        # runs (e.g. a different UTC day). Ignore that single line when checking
        # sync, so content drift is still caught but the date never trips CI.
        def norm(s):
            return re.sub(r"Last updated: \d{4}-\d{2}-\d{2}", "Last updated: <date>", s)

        ok = True
        for path, new in ((README, readme), (DATA_CSV, csv_text)):
            cur = ""
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    cur = f.read()
            if norm(cur) != norm(new):
                ok = False
                print(f"OUT OF SYNC: {os.path.relpath(path, ROOT)} differs from generated output.", file=sys.stderr)
        if not ok:
            print("Run `python3 scripts/generate.py` and commit the result.", file=sys.stderr)
            sys.exit(1)
        print("README.md and data/startups.csv are in sync with data/startups.json.")
        return

    os.makedirs(os.path.dirname(DATA_CSV), exist_ok=True)
    with open(README, "w", encoding="utf-8") as f:
        f.write(readme)
    with open(DATA_CSV, "w", encoding="utf-8") as f:
        f.write(csv_text)
    print(f"Wrote {os.path.relpath(README, ROOT)} and {os.path.relpath(DATA_CSV, ROOT)} "
          f"from {len(data)} companies.")


if __name__ == "__main__":
    main()
