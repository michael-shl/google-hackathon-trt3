"""Data access for the agent's tools: mock corridor or BigQuery (USE_MOCK_DATA).

Every tool goes through these functions, so switching to real data is one env var.
Results are cached per process; the corridor does not change during a session.
"""

import json
import os
import re
from functools import lru_cache

from . import mock_data

MAX_HOPS_LIMIT = 3
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DataUnavailable(RuntimeError):
    """A table the tool needs does not exist yet (or the query failed)."""


def use_mock() -> bool:
    """Mock corridor only when USE_MOCK_DATA is explicitly true (deployments default to BigQuery)."""
    return os.getenv("USE_MOCK_DATA", "false").strip().lower() in ("1", "true", "yes")


def _dataset() -> str:
    name = os.getenv("BQ_DATASET", "a4i_econ")
    if not _IDENT.match(name):
        raise ValueError(f"Invalid BQ_DATASET: {name!r}")
    return name


def _graph() -> str:
    name = os.getenv("BQ_GRAPH", "LocalEconomy")
    if not _IDENT.match(name):
        raise ValueError(f"Invalid BQ_GRAPH: {name!r}")
    return f"{_dataset()}.{name}"


def _run(sql: str, **params) -> list[dict]:
    from . import bq

    try:
        return bq.run(sql, **params)
    except Exception as exc:  # surfaced to the LLM as a status=error message
        raise DataUnavailable(f"BigQuery query failed: {exc}") from exc


def clear_cache() -> None:
    for fn in (get_businesses_all, cascade_paths, applicants, out_degrees, neighborhoods_all,
               corridor_profile, loans_all):
        fn.cache_clear()


# ---------------------------------------------------------------- businesses


@lru_cache(maxsize=1)
def get_businesses_all() -> dict:
    if use_mock():
        return {k: dict(v, business_id=k) for k, v in mock_data.BUSINESSES.items()}
    rows = _run(f"SELECT business_id, name, address, naics4 FROM {_dataset()}.businesses")
    return {r["business_id"]: r for r in rows}


def get_business(business_id: str) -> dict | None:
    return get_businesses_all().get(business_id)


# ---------------------------------------------------------------- cascade (multi-hop GQL)

_CASCADE_GQL = """
GRAPH {graph}
MATCH p = (seed:Business WHERE seed.business_id = @seed_id)
          -[e:Supplies]->{{1,{max_hops}}}(exposed:Business)
WHERE exposed.business_id != seed.business_id
LET hops = ARRAY_LENGTH(e),
    path_strength = EXP(SUM(LN(e.intensity))),
    weakest_link = MIN(e.intensity)
RETURN exposed.business_id AS business_id, exposed.name AS name, exposed.naics4 AS naics4,
       hops, path_strength, weakest_link, TO_JSON(p) AS path_json
"""


def _names_from_path_json(path_json) -> list[str]:
    """Extracts node names, in order, from TO_JSON(path). Tolerant of format differences."""
    try:
        data = json.loads(path_json) if isinstance(path_json, str) else path_json
    except (TypeError, ValueError):
        return []
    names: list[str] = []

    def walk(obj):
        if isinstance(obj, dict):
            props = obj.get("properties")
            if obj.get("kind") == "node" and isinstance(props, dict) and "name" in props:
                names.append(str(props["name"]))
                return
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)
    return names


def _mock_paths(seed_id: str, max_hops: int) -> list[dict]:
    out_edges: dict[str, list[tuple[str, float]]] = {}
    for supplier, buyer, intensity in mock_data.SUPPLIES:
        out_edges.setdefault(supplier, []).append((buyer, intensity))
    names = {k: v["name"] for k, v in mock_data.BUSINESSES.items()}
    rows: list[dict] = []

    def dfs(node, path, intensities):
        if intensities and node != seed_id:
            strength = 1.0
            for value in intensities:
                strength *= value
            rows.append({
                "business_id": node,
                "name": names[node],
                "naics4": mock_data.BUSINESSES[node]["naics4"],
                "hops": len(intensities),
                "path_strength": strength,
                "weakest_link": min(intensities),
                "path_names": [names[n] for n in path],
            })
        if len(intensities) == max_hops:
            return
        for nxt, intensity in out_edges.get(node, []):
            if nxt not in path:
                dfs(nxt, path + [nxt], intensities + [intensity])

    dfs(seed_id, [seed_id], [])
    return rows


@lru_cache(maxsize=256)
def cascade_paths(seed_id: str, max_hops: int = 2) -> tuple:
    """Every Supplies path from seed_id of 1..max_hops edges (one row per path)."""
    if not 1 <= max_hops <= MAX_HOPS_LIMIT:
        raise ValueError(f"max_hops must be between 1 and {MAX_HOPS_LIMIT}")
    if use_mock():
        return tuple(_mock_paths(seed_id, max_hops))
    rows = _run(_CASCADE_GQL.format(graph=_graph(), max_hops=int(max_hops)), seed_id=seed_id)
    for row in rows:
        row["path_names"] = _names_from_path_json(row.pop("path_json", None))
    return tuple(rows)


@lru_cache(maxsize=1)
def out_degrees() -> dict:
    """Distinct direct buyers per supplier (used for the hub rule, not for ranking)."""
    if use_mock():
        degrees: dict[str, set] = {}
        for supplier, buyer, _ in mock_data.SUPPLIES:
            degrees.setdefault(supplier, set()).add(buyer)
        return {k: len(v) for k, v in degrees.items()}
    rows = _run(f"SELECT supplier_id, COUNT(DISTINCT buyer_id) AS n "
                f"FROM {_dataset()}.supplies GROUP BY supplier_id")
    return {r["supplier_id"]: int(r["n"]) for r in rows}


# ---------------------------------------------------------------- applicants & neighborhoods


@lru_cache(maxsize=1)
def applicants() -> tuple:
    if use_mock():
        businesses = get_businesses_all()
        return tuple(dict(a, **{k: businesses[a["business_id"]][k] for k in ("name", "address", "naics4")})
                     for a in mock_data.APPLICANTS)
    return tuple(_run(
        f"SELECT a.business_id, b.name, b.address, b.naics4, a.requested_amount, a.stated_need "
        f"FROM {_dataset()}.applicants a JOIN {_dataset()}.businesses b USING (business_id)"))


@lru_cache(maxsize=1)
def loans_all() -> tuple:
    """REAL SBA 7(a) loan records (a4i_econ.borrowed_from); often sparse or empty."""
    if use_mock():
        return tuple(mock_data.LOANS)
    return tuple(_run(
        f"SELECT business_id, bank_name, gross_approval, CAST(approval_date AS STRING) AS approval_date, "
        f"loan_status, charged_off FROM {_dataset()}.borrowed_from"))


@lru_cache(maxsize=1)
def neighborhoods_all() -> dict:
    """business_id -> tract demographics. Needs a4i_econ.business_tract (sql/02)."""
    if use_mock():
        return {b: dict(mock_data.TRACTS[t], tract=t) for b, t in mock_data.BUSINESS_TRACT.items()}
    rows = _run(
        f"SELECT bt.business_id, bt.tract, d.total_pop, d.median_income, d.poverty_rate, "
        f"d.no_vehicle_rate, d.assistance_rate "
        f"FROM {_dataset()}.business_tract bt "
        f"JOIN {_dataset()}.tract_demographics d ON d.geo_id = bt.tract")
    return {r.pop("business_id"): r for r in rows}


def neighborhood(business_id: str) -> dict | None:
    return _safe_neighborhoods().get(business_id)


def _safe_neighborhoods() -> dict:
    """Tract data is optional: until sql/02 exists, tools still work without the need signal."""
    try:
        return neighborhoods_all()
    except DataUnavailable:
        return {}


_SECTOR_GROUPS = {"31": "31-33", "32": "31-33", "33": "31-33", "44": "44-45", "45": "44-45",
                  "48": "48-49", "49": "48-49"}
SECTOR_NAMES = {
    "11": "Agriculture", "21": "Mining", "22": "Utilities", "23": "Construction",
    "31-33": "Manufacturing", "42": "Wholesale trade", "44-45": "Retail trade",
    "48-49": "Transportation & warehousing", "51": "Information", "52": "Finance & insurance",
    "53": "Real estate", "54": "Professional services", "55": "Management of companies",
    "56": "Administrative & support", "61": "Education", "62": "Health care & social assistance",
    "71": "Arts & recreation", "72": "Accommodation & food services",
    "81": "Other services (incl. personal services)", "92": "Public administration",
}


def sector(naics4) -> str:
    """2-digit NAICS sector (with the official 31-33 / 44-45 / 48-49 groupings)."""
    two = str(naics4 or "")[:2]
    return _SECTOR_GROUPS.get(two, two or "unknown")


@lru_cache(maxsize=1)
def corridor_profile() -> dict:
    """Corridor baseline for the equity audit: sector shares and business-weighted need."""
    businesses = get_businesses_all()
    total = len(businesses) or 1
    shares: dict[str, float] = {}
    for b in businesses.values():
        key = sector(b["naics4"])
        shares[key] = shares.get(key, 0) + 1 / total
    hoods = _safe_neighborhoods()
    with_hood = [hoods[b] for b in businesses if b in hoods]

    def avg(key):
        values = [h[key] for h in with_hood if h.get(key) is not None]
        return sum(values) / len(values) if values else None

    return {
        "business_count": len(businesses),
        "sector_share": shares,
        "poverty_avg": avg("poverty_rate"),
        "no_vehicle_avg": avg("no_vehicle_rate"),
    }
