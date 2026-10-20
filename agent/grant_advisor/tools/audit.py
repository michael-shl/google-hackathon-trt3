from . import data


def equity_audit(funded_ids: list[str]) -> dict:
    """Audits who the money reaches: compares the funded businesses' industries and census
    tracts with the whole corridor, to expose the known bias toward input-heavy industries.

    Args:
        funded_ids: business_ids the officer intends to fund.

    Returns:
        dict with 'status', 'industry_mix' (funded vs corridor share per 4-digit NAICS),
        'poverty' and 'no_vehicle' (funded average vs corridor average) and a plain 'finding'.
    """
    if not funded_ids:
        return {"status": "error", "error_message": "funded_ids is empty."}
    try:
        businesses = data.get_businesses_all()
        profile = data.corridor_profile()
    except data.DataUnavailable as exc:
        return {"status": "error", "error_message": str(exc)}

    unknown = [b for b in funded_ids if b not in businesses]
    funded = [b for b in funded_ids if b in businesses]
    if not funded:
        return {"status": "error", "error_message": f"Unknown business_ids: {unknown}"}

    funded_share: dict[str, float] = {}
    for bid in funded:
        naics = businesses[bid]["naics4"]
        funded_share[naics] = funded_share.get(naics, 0) + 1 / len(funded)
    industry_mix = sorted(
        ({"naics4": n, "funded_share": round(s, 3),
          "corridor_share": round(profile["industry_share"].get(n, 0.0), 3),
          "ratio": round(s / profile["industry_share"][n], 1) if profile["industry_share"].get(n) else None}
         for n, s in funded_share.items()),
        key=lambda r: -(r["ratio"] or 0))

    hoods = [data.neighborhood(b) for b in funded]
    hoods = [h for h in hoods if h]

    def avg(key):
        values = [h[key] for h in hoods if h.get(key) is not None]
        return round(sum(values) / len(values), 3) if values else None

    poverty = {"funded_avg": avg("poverty_rate"),
               "corridor_avg": round(profile["poverty_avg"], 3) if profile["poverty_avg"] is not None else None}
    no_vehicle = {"funded_avg": avg("no_vehicle_rate"),
                  "corridor_avg": round(profile["no_vehicle_avg"], 3) if profile["no_vehicle_avg"] is not None else None}

    findings = []
    over = [r for r in industry_mix if r["ratio"] and r["ratio"] >= 2]
    if over:
        findings.append("Over-represented industries vs corridor: " +
                        ", ".join(f"NAICS {r['naics4']} ({r['ratio']}x)" for r in over) +
                        ". Supply edges favor input-heavy industries (restaurants, food, light "
                        "manufacturing); personal services get few edges, so check this is need, not data visibility.")
    if poverty["funded_avg"] is not None and poverty["corridor_avg"] is not None:
        direction = "higher" if poverty["funded_avg"] >= poverty["corridor_avg"] else "lower"
        findings.append(f"Funded businesses sit in tracts with {direction} poverty "
                        f"({poverty['funded_avg']:.0%}) than the corridor average ({poverty['corridor_avg']:.0%}).")
    else:
        findings.append("Tract demographics unavailable (business_tract table missing); poverty comparison skipped.")

    result = {"status": "success", "funded_count": len(funded), "industry_mix": industry_mix,
              "poverty": poverty, "no_vehicle": no_vehicle, "finding": " ".join(findings)}
    if unknown:
        result["ignored_unknown_ids"] = unknown
    return result
