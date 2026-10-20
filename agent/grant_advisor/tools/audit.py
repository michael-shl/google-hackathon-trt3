from . import data

# Flag a sector as over-funded only with at least this many funded businesses in it: with a
# handful of grants, one business alone always looks "over-represented".
MIN_FUNDED_FOR_FLAG = 2
OVER_RATIO = 2.0
# Sectors this large in the corridor that receive nothing are reported as possibly missed.
LARGE_SECTOR_SHARE = 0.10
# Poverty gaps smaller than this are reported as "about the same".
POVERTY_TOLERANCE = 0.01


def _pct(value):
    return f"{value:.0%}"


def equity_audit(funded_ids: list[str]) -> dict:
    """Audits who the money reaches: compares the funded businesses' industry sectors and census
    tracts with the whole corridor, to expose the known bias toward input-heavy industries.

    Args:
        funded_ids: business_ids the officer intends to fund.

    Returns:
        dict with 'status', 'sector_mix' (funded vs corridor share per NAICS sector),
        'unfunded_large_sectors', 'poverty' and 'no_vehicle' (funded vs corridor average)
        and a plain-language 'finding'.
    """
    if not funded_ids:
        return {"status": "error", "error_message": "funded_ids is empty."}
    try:
        businesses = data.get_businesses_all()
        profile = data.corridor_profile()
    except data.DataUnavailable as exc:
        return {"status": "error", "error_message": str(exc)}

    unknown = [b for b in funded_ids if b not in businesses]
    funded = list(dict.fromkeys(b for b in funded_ids if b in businesses))
    if not funded:
        return {"status": "error", "error_message": f"Unknown business_ids: {unknown}"}

    counts: dict[str, int] = {}
    for bid in funded:
        key = data.sector(businesses[bid]["naics4"])
        counts[key] = counts.get(key, 0) + 1
    corridor = profile["sector_share"]
    sector_mix = sorted(
        ({"sector": s, "sector_name": data.SECTOR_NAMES.get(s, s), "funded_count": n,
          "funded_share": round(n / len(funded), 3), "corridor_share": round(corridor.get(s, 0.0), 3),
          "ratio": round(n / len(funded) / corridor[s], 1) if corridor.get(s) else None}
         for s, n in counts.items()),
        key=lambda r: -(r["ratio"] or 0))
    unfunded_large = sorted(
        ({"sector": s, "sector_name": data.SECTOR_NAMES.get(s, s), "corridor_share": round(share, 3)}
         for s, share in corridor.items() if share >= LARGE_SECTOR_SHARE and s not in counts),
        key=lambda r: -r["corridor_share"])

    hoods = [h for h in (data.neighborhood(b) for b in funded) if h]

    def avg(key):
        values = [h[key] for h in hoods if h.get(key) is not None]
        return round(sum(values) / len(values), 3) if values else None

    def corridor_avg(key):
        return round(profile[key], 3) if profile[key] is not None else None

    poverty = {"funded_avg": avg("poverty_rate"), "corridor_avg": corridor_avg("poverty_avg")}
    no_vehicle = {"funded_avg": avg("no_vehicle_rate"), "corridor_avg": corridor_avg("no_vehicle_avg")}

    findings = []
    over = [r for r in sector_mix
            if r["ratio"] and r["ratio"] >= OVER_RATIO and r["funded_count"] >= MIN_FUNDED_FOR_FLAG]
    if over:
        findings.append("Over-represented vs the corridor: " +
                        ", ".join(f"{r['sector_name']} ({r['funded_count']} funded, {r['ratio']}x its share)" for r in over) +
                        ". Supply edges favor input-heavy industries, so check this reflects need, not data visibility.")
    if unfunded_large:
        findings.append("Nothing funded in: " +
                        ", ".join(f"{r['sector_name']} ({_pct(r['corridor_share'])} of corridor businesses)" for r in unfunded_large) +
                        ". These may have few supply edges rather than little need.")
    if not over and not unfunded_large:
        findings.append("Funded sectors are broadly in line with the corridor mix.")
    if poverty["funded_avg"] is not None and poverty["corridor_avg"] is not None:
        gap = poverty["funded_avg"] - poverty["corridor_avg"]
        if abs(gap) < POVERTY_TOLERANCE:
            findings.append(f"Funded businesses sit in tracts with about the same poverty rate as the corridor "
                            f"({_pct(poverty['funded_avg'])} vs {_pct(poverty['corridor_avg'])}).")
        else:
            findings.append(f"Funded businesses sit in tracts with {'higher' if gap > 0 else 'lower'} poverty "
                            f"({_pct(poverty['funded_avg'])}) than the corridor average ({_pct(poverty['corridor_avg'])}).")
    else:
        findings.append("Neighborhood data unavailable (business_need table missing, see sql/02_business_need.sql); poverty comparison skipped.")

    result = {"status": "success", "funded_count": len(funded), "sector_mix": sector_mix,
              "unfunded_large_sectors": unfunded_large, "poverty": poverty, "no_vehicle": no_vehicle,
              "finding": " ".join(findings)}
    if unknown:
        result["ignored_unknown_ids"] = unknown
    return result
