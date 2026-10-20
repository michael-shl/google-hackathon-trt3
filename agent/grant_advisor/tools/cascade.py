from . import data

EDGE_BASIS = ("MODELED: supply links assign published BEA industry-average purchase rates to "
              "specific nearby business pairs (industry match + walking distance).")


def summarize_cascade(seed_id: str, max_hops: int = 2, weighting: str = "product") -> dict:
    """Collapses per-path rows into one entry per exposed business (strongest path wins)."""
    key = "path_strength" if weighting == "product" else "weakest_link"
    best: dict[str, dict] = {}
    for row in data.cascade_paths(seed_id, max_hops):
        current = best.get(row["business_id"])
        if current is None or row[key] > current[key] or (
                row[key] == current[key] and row["hops"] < current["hops"]):
            best[row["business_id"]] = row
    exposed = sorted(best.values(), key=lambda r: r[key], reverse=True)
    return {
        "exposed": exposed,
        "exposure_score": sum(r[key] for r in exposed),
        "hop1": sum(1 for r in exposed if r["hops"] == 1),
        "hop2": sum(1 for r in exposed if r["hops"] == 2),
        "hop3": sum(1 for r in exposed if r["hops"] == 3),
    }


def get_cascade(business_id: str, max_hops: int = 2) -> dict:
    """Shows which businesses are exposed if this business closes, by walking Supplies links
    downstream in the corridor's property graph (multi-hop GQL traversal).

    Args:
        business_id: The business_id of the business that might close.
        max_hops: How many supply links to follow (1-3). Default 2; 3 hops saturates the corridor.

    Returns:
        dict with 'status', 'seed', 'exposed' (each with hops, path_strength = product of link
        intensities, weakest_link, path_names), 'counts' per hop, 'exposure_score' and 'edge_basis'.
    """
    try:
        seed = data.get_business(business_id)
        if seed is None:
            return {"status": "error", "error_message": f"Unknown business_id {business_id!r}. Use find_business first."}
        if not 1 <= int(max_hops) <= data.MAX_HOPS_LIMIT:
            return {"status": "error", "error_message": f"max_hops must be 1-{data.MAX_HOPS_LIMIT}."}
        summary = summarize_cascade(business_id, int(max_hops))
    except data.DataUnavailable as exc:
        return {"status": "error", "error_message": str(exc)}

    exposed = [
        {
            "business_id": r["business_id"],
            "name": r["name"],
            "naics4": r["naics4"],
            "hops": r["hops"],
            "path_strength": round(r["path_strength"], 6),
            "weakest_link": round(r["weakest_link"], 6),
            "path_names": r.get("path_names", []),
        }
        for r in summary["exposed"][:25]
    ]
    result = {
        "status": "success",
        "seed": {k: seed.get(k) for k in ("business_id", "name", "address", "naics4")},
        "exposed": exposed,
        "counts": {"hop1": summary["hop1"], "hop2": summary["hop2"], "hop3": summary["hop3"],
                   "total": len(summary["exposed"])},
        "exposure_score": round(summary["exposure_score"], 6),
        "edge_basis": EDGE_BASIS,
    }
    if not summary["exposed"]:
        result["note"] = ("No downstream supply links: the graph cannot show a cascade for this "
                          "business. That does not mean it is unimportant to the neighborhood.")
    elif len(summary["exposed"]) > len(exposed):
        result["note"] = f"Showing the 25 strongest of {len(summary['exposed'])} exposed businesses."
    return result
