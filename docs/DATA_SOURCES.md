# Data sources — where the Challenge 3 data lives

**Project:** `qwiklabs-gcp-04-7254cc802c4d` · **BigQuery dataset:** `a4i_econ` (location `US`) · **Corridor:** `central-market`
Owners: **P2** (load + graph) and **P3** (cascade + scoring). See [TEAM_PLAN.md](TEAM_PLAN.md) §7.

There are three sources. **Most of the data is not in the repo**: it is a pre-built snapshot that
[`scripts/load.sh`](../scripts/load.sh) loads into BigQuery.

---

## 1. Core tables: Cloud Storage snapshot → BigQuery (what we use)

**Location:** `gs://class-demo/a4i-2026/challenge-3-micro-grants/<corridor>/<table>/*.parquet`

> Not readable anonymously; read it from **Cloud Shell signed in as the Qwiklabs student account**.

`load.sh` loads it into dataset **`a4i_econ`** and also creates the Enterprise reservation (`a4i-graph`)
that graph (GQL) queries require.

| Table | Role | Main columns (as built by the notebook) | Real or modeled |
|---|---|---|---|
| `businesses` | node | `business_id, name, legal_name, address, zip, naics, naics4, corridor, latitude, longitude` | **Real** (SF registry) |
| `employer_blocks` | node | `block_id, tract, jobs, lat, lon` | **Real** job counts (LEHD) |
| `supplies` | edge, supplier → buyer | `edge_id, supplier_id, buyer_id, intensity, metres` | **Modeled** (BEA industry rates + walking distance) |
| `draws_footfall_from` | edge, block → business | `edge_id, block_id, business_id, worker_share, metres` | **Modeled** (how LEHD jobs are allocated to nearby businesses) |
| `borrowed_from` | edge, business → bank | `business_id, bank_name, gross_approval, approval_date, loan_status, charged_off` | **Real** (SBA 7(a) FOIA; sparse, may be empty) |
| `tract_demographics` | attributes | `geo_id, total_pop, median_income, poverty_rate, no_vehicle_rate, assistance_rate` | **Real** (ACS 5-year) |

### Load it (Cloud Shell, repo root; P2 only, since everyone shares one project)

```bash
gcloud config set project qwiklabs-gcp-04-7254cc802c4d
bash scripts/load.sh --list            # corridors available in the snapshot
bash scripts/load.sh central-market    # 6 tables + graph reservation; safe to re-run
bq ls a4i_econ
bq show --schema --format=prettyjson a4i_econ.supplies   # confirm exact column names
```

The script ends with row counts and a **"reach"** check (businesses with something two hops downstream).
Central Market should show **~230 businesses** and **~86 with two-hop reach**. Paste the output in the team channel.

---

## 2. In the repo: `data/`

| File | Contents | Use |
|---|---|---|
| [`bea_direct_requirements.csv`](../data/bea_direct_requirements.csv) | 44,867 rows: `buyer_naics4, supplier_naics4, coefficient` | Federal rates behind every supply edge |
| [`bea_naics_concordance.csv`](../data/bea_naics_concordance.csv) | BEA industry code → 4-digit NAICS | Auditable code translation |

Only needed to **inspect or improve the supply-edge generator**, a high-value differentiator. Details: [`data/README.md`](../data/README.md).

---

## 3. Live upstream sources (what the notebook pulls)

| Data | Source | License |
|---|---|---|
| SF registered business locations | https://data.sf.gov/resource/g8m3-pdis.json | PDDL (public domain) |
| SBA 7(a) loans + charge-offs | https://data.sba.gov/dataset/7a-504-foia | US Government work |
| Workplace job counts (LEHD LODES 8) | https://lehd.ces.census.gov/data/lodes/LODES8/ | US Government work |
| Census tract geometry | `bigquery-public-data.geo_census_tracts.us_census_tracts_national` | Public |
| Tract demographics (ACS) | `bigquery-public-data.census_bureau_acs.*` (newest census-tract table) | Public |
| BEA Input-Output accounts | https://www.bea.gov/industry/input-output-accounts-data | Public domain |

To rebuild from these, import [`notebooks/c3_01_load_explore.ipynb`](../notebooks/c3_01_load_explore.ipynb) into
**Colab Enterprise** (README Step 4). **Don't re-run its Section 11 (load) without telling P2**: it overwrites the shared tables.

---

## 4. Tables built on top (created 2026-10-20; re-run in order after every `load.sh`)

| Object | File | Result | Why |
|---|---|---|---|
| `a4i_econ.LocalEconomy` (property graph) | [`sql/01_property_graph.sql`](../sql/01_property_graph.sql) | Business + Employer nodes; Supplies + DrawsFootfall edges; 0 duplicate keys | Required multi-hop GQL traversal |
| `a4i_econ.business_tract`, `a4i_econ.business_need` | [`sql/02_business_need.sql`](../sql/02_business_need.sql) | 230/230 businesses with need data (2 exact tract matches, 228 via split-tract method) | `businesses` has no tract; `tract_demographics` covers only 2 of 230 businesses |
| `a4i_econ.applicants` | [`sql/03_applicants.sql`](../sql/03_applicants.sql) | 11 simulated applications, $134,500 requested | Queue for the Main Street track |

Run them with the BigQuery console, or `bq query --use_legacy_sql=false < sql/0N_….sql`.

**Census-vintage gotcha (say it in the deck as a limitation):** the newest ACS (`censustract_2020_5yr`)
uses **2020** tract IDs, but BigQuery's public tract *shapes* are **2010** vintage, and San Francisco
split several corridor tracts in 2020 (e.g. 0176.01 → 0176.02/.03/.04). `business_need` therefore
combines the 2020 tracts that replaced each 2010 tract (same 4-digit base, ratio of summed ACS
counts). For split tracts, the need signal is the average over the old tract's area.

DDL and queries for each are in [TEAM_PLAN.md](TEAM_PLAN.md) §7 (P2 and P3).

---

## Say this in the deck (judges check)

- **Real:** the businesses, the corridor boundary, SBA loans (incl. charge-offs), LEHD job counts, ACS demographics.
- **Modeled:** *which* business supplies *which* (BEA industry-average rates assigned by industry match + walking distance),
  and which shops a block's workers patronize. *"The relationship types and their industry-level average intensities are
  measured and published by the federal government. The assignment of those averages to specific pairs of businesses is
  ours: a modeling choice, not a measurement."*
- **Filtered out:** sole proprietors and home-address registrations (privacy).
