# Contributing to Awesome Quantum Startups

Thanks for helping keep this directory complete and accurate! Contributions of new
companies, corrections, and removals are all welcome.

## How the repo works

The **single source of truth** is [`data/startups.json`](data/startups.json): a JSON array of
company objects. Both [`README.md`](README.md) and [`data/startups.csv`](data/startups.csv) are
**auto-generated** from it:

```bash
python3 scripts/generate.py        # regenerate README.md and data/startups.csv
python3 scripts/generate.py --check # verify they are in sync (used in CI)
```

> ⚠️ Do **not** edit `README.md` or `data/startups.csv` by hand. Your changes will be
> overwritten the next time the generator runs. Edit `data/startups.json` instead.

## Adding or updating a company

1. Edit [`data/startups.json`](data/startups.json) and add (or modify) an object. Keep the
   array roughly alphabetical within reason; the generator sorts output anyway.
2. Run `python3 scripts/generate.py`.
3. Commit `data/startups.json`, `data/startups.csv`, and `README.md` together.
4. Open a pull request describing the change and your source.

If you'd rather not edit JSON, just [open an issue](../../issues/new/choose) with the
company details and a maintainer will add it.

## Entry schema

```json
{
  "name": "Example Quantum",
  "website": "https://example.com",
  "hq_country": "United States",
  "hq_city": "Boston",
  "founded": "2021",
  "category": "Quantum Computing Hardware",
  "subsector": "full-stack",
  "modality": "trapped-ion",
  "company_type": "startup",
  "status": "active",
  "description": "Builds trapped-ion quantum computers for chemistry simulation.",
  "notes": ""
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `name` | ✅ | Official company name. |
| `website` | ✅ | Canonical homepage (`https://…`). Leave `""` if genuinely unknown: never guess. |
| `hq_country` | ✅ | Headquarters country (full name, e.g. `"United Kingdom"`). |
| `hq_city` |  | Headquarters city. |
| `founded` |  | Four-digit year as a string, or `""` if unknown. Do not guess. |
| `category` | ✅ | Exactly one of the categories below. |
| `subsector` |  | Short free-form focus, e.g. `"QKD"`, `"compilers"`, `"cryogenics"`. |
| `modality` |  | Hardware only: `superconducting`, `trapped-ion`, `photonic`, `neutral-atom`, `spin/silicon`, `annealing`, `topological`, `NV-center/diamond`, … |
| `company_type` | ✅ | `startup`, `scaleup`, `public-company`, `big-tech-division`, `national-lab-or-spinout`, or `other`. |
| `status` |  | `active`, `acquired`, `merged`, `defunct`, or `uncertain`. Defaults to active. `uncertain` renders as *(unverified)* and means we could not confirm the company is a real, operating quantum business; use it sparingly. |
| `acquired_by` |  | Acquirer name. Set when `status` is `acquired` or `merged` (renders as *(acquired by X, YYYY)*). |
| `acquired_year` |  | Four-digit year of the acquisition/merger, if known. |
| `description` | ✅ | One concise line (≤ 140 chars). |
| `notes` |  | Anything else worth flagging. |

### Categories (pick exactly one)

- **Quantum Computing Hardware**: builders of quantum processors / full-stack computers (any modality).
- **Software, Algorithms & Error Correction**: SDKs, compilers, simulators, error-correction, middleware (hardware-agnostic).
- **Cloud & Access Platforms**: cloud aggregators, orchestration, access/marketplace platforms.
- **Quantum Sensing & Metrology**: sensors, magnetometers, gravimeters, atomic clocks, imaging, timing.
- **Quantum Communication & Networking**: QKD, quantum internet, entanglement distribution, repeaters.
- **Quantum Security & Post-Quantum Cryptography**: PQC, quantum-safe security, QRNG.
- **Components & Enabling Technologies**: cryogenics, control electronics, lasers/photonics, materials, fabrication, packaging, test.
- **Applications, Consulting & Services**: end-use applications, consulting, education/talent, advisory/investment.

Choose the company's **primary** identity. A QRNG vendor goes under *Security*; a full-stack
ion-trap computer maker goes under *Hardware*, even if it also sells cloud access.

## Inclusion criteria

- The company's core business (or a clearly dedicated division) must be quantum technology.
- Real, verifiable companies only: include a source. No fabricated entries or placeholder sites.
- Big-tech and large-enterprise quantum programs belong under `company_type: "big-tech-division"`
  and appear in their own section, not the startup sector tables.

## Quality bar

- Verify the website resolves and matches the company.
- Prefer primary sources (company site, official announcements) over aggregators for facts.
- Keep descriptions neutral and factual: this is a directory, not marketing copy.

By contributing you agree that your contributions are released under [CC0 1.0](LICENSE).
