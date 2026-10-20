"""Ranking v1 (owner: P3). Every number below is an ASSUMPTION; log changes in docs/decisions.md."""

import math

from . import data
from .cascade import summarize_cascade

# Assumed drop in 12-month closure probability when a business receives its full request.
CLOSURE_RISK_REDUCTION = {"base": 0.10, "pessimistic": 0.05, "optimistic": 0.20}
# Suppliers at or above this out-degree percentile are treated as hubs (likely robust).
HUB_PERCENTILE = 0.95
# Hubs: assume a grant moves their survival odds half as much (they have more buyers to absorb shocks).
HUB_ROBUSTNESS = 0.5
# Top two within this relative gap are reported as indistinguishable.
TIE_TOLERANCE = 0.10
DEFAULT_HOPS = 2
# Budget left after full awards goes to the next-best applicant as a partial award (D12),
# unless it is below this floor (no token grants).
MIN_PARTIAL_AWARD = 1000


def _hub_threshold(degrees: dict) -> float:
    values = sorted(v for v in degrees.values() if v > 0)
    if not values:
        return math.inf
    return values[max(0, math.ceil(HUB_PERCENTILE * len(values)) - 1)]


def _score_applicants(candidates, weighting="product", hub_robustness=HUB_ROBUSTNESS,
                      max_hops=DEFAULT_HOPS):
    degrees = data.out_degrees()
    threshold = _hub_threshold(degrees)
    scored = []
    for app in candidates:
        bid = app["business_id"]
        cascade = summarize_cascade(bid, max_hops, weighting)
        degree = degrees.get(bid, 0)
        is_hub = degree >= threshold
        requested = int(app["requested_amount"])
        effective = cascade["exposure_score"] * (hub_robustness if is_hub else 1.0)
        hood = data.neighborhood(bid) or {}
        scored.append({
            "business_id": bid,
            "name": app["name"],
            "address": app.get("address"),
            "naics4": app.get("naics4"),
            "requested": requested,
            "stated_need": app.get("stated_need"),
            "exposure_score": cascade["exposure_score"],
            "reach_total": len(cascade["exposed"]),
            "reach_hop1": cascade["hop1"],
            "reach_hop2": cascade["hop2"],
            "out_degree": degree,
            "is_hub": is_hub,
            "tract": hood.get("tract"),
            "tract_poverty": hood.get("poverty_rate"),
            "score_per_10k": effective / requested * 10_000 if requested > 0 else 0.0,
        })
    scored.sort(key=lambda r: (-r["score_per_10k"], -(r["tract_poverty"] or 0.0)))
    return scored


def _reason(row, risk_drop):
    if row["reach_total"] == 0:
        return ("No downstream supply links visible in the graph; a grant cannot be argued on "
                "cascade grounds. Consider other relief programs.")
    parts = [f"Protects {row['reach_total']} downstream businesses "
             f"({row['reach_hop1']} direct, {row['reach_hop2']} at 2 hops)",
             f"expected ~{risk_drop * row['reach_total']:.1f} businesses spared a supply shock "
             f"under a {risk_drop:.0%} closure-risk reduction"]
    if row["is_hub"]:
        parts.append(f"hub ({row['out_degree']} direct buyers): robustness discount x{HUB_ROBUSTNESS} "
                     "applied because a large supplier is likelier to survive without the grant")
    if row["tract_poverty"] is not None:
        parts.append(f"tract poverty {row['tract_poverty']:.0%}")
    return "; ".join(parts) + "."


def rank_applicants(budget: int = 50000, assumption: str = "base",
                    applicant_ids: list[str] | None = None) -> dict:
    """Ranks grant applicants by downstream exposure protected per grant dollar (not by how
    connected they are), allocates the budget, and tests how robust the top pick is.

    Args:
        budget: Total relief budget in USD.
        assumption: What a grant changes: "base" (cuts closure risk 10 points), "pessimistic" (5),
            or "optimistic" (20).
        applicant_ids: Optional subset of applicant business_ids; default is the whole queue.

    Returns:
        dict with 'status', 'assumptions', 'ranking' (with funded_amount, partial and reason),
        'recommendation', 'runner_up', 'indistinguishable', 'sensitivity', 'partial_award' and
        'unfunded_budget'.
    """
    if assumption not in CLOSURE_RISK_REDUCTION:
        return {"status": "error",
                "error_message": f"assumption must be one of {sorted(CLOSURE_RISK_REDUCTION)}"}
    try:
        queue = list(data.applicants())
        if applicant_ids:
            wanted = set(applicant_ids)
            queue = [a for a in queue if a["business_id"] in wanted]
        if not queue:
            return {"status": "error", "error_message": "No applicants found (check the applicants table or the ids)."}
        # One batched graph query for all applicants + concurrent lookups, instead of ~2 queries each.
        data.warm([a["business_id"] for a in queue], DEFAULT_HOPS)
        ranking = _score_applicants(queue)
        variants = {
            "weakest_link_weighting": _score_applicants(queue, weighting="weakest_link"),
            "no_hub_discount": _score_applicants(queue, hub_robustness=1.0),
            "one_hop_only": _score_applicants(queue, max_hops=1),
        }
    except data.DataUnavailable as exc:
        return {"status": "error", "error_message": str(exc)}

    risk_drop = CLOSURE_RISK_REDUCTION[assumption]
    remaining = int(budget)
    for row in ranking:
        row["reason"] = _reason(row, risk_drop)
        row["expected_businesses_spared"] = round(risk_drop * row["reach_total"], 2)
        row["partial"] = False
        if row["reach_total"] > 0 and row["requested"] <= remaining:
            row["funded_amount"] = row["requested"]
            remaining -= row["requested"]
        else:
            row["funded_amount"] = 0
        row["exposure_score"] = round(row["exposure_score"], 6)
        row["score_per_10k"] = round(row["score_per_10k"], 6)

    partial_award = None
    if remaining >= MIN_PARTIAL_AWARD:
        # Decision D12: the leftover goes to the best-ranked unfunded applicant that has a cascade;
        # its effect is assumed proportional to the share of the request it receives.
        nxt = next((r for r in ranking if r["reach_total"] > 0 and r["funded_amount"] == 0), None)
        if nxt:
            share = remaining / nxt["requested"]
            nxt.update(funded_amount=remaining, partial=True,
                       expected_businesses_spared=round(risk_drop * share * nxt["reach_total"], 2))
            nxt["reason"] += (f" PARTIAL award: ${remaining:,} of ${nxt['requested']:,} requested; effect "
                              f"assumed proportional ({share:.0%} of the closure-risk reduction).")
            partial_award = {"business_id": nxt["business_id"], "name": nxt["name"], "amount": remaining,
                             "requested": nxt["requested"], "share_of_request": round(share, 3)}
            remaining = 0

    eligible = [r for r in ranking if r["reach_total"] > 0]
    top = eligible[0] if eligible else None
    runner_up = eligible[1] if len(eligible) > 1 else None
    indistinguishable = bool(top and runner_up and top["score_per_10k"] > 0 and
                             (top["score_per_10k"] - runner_up["score_per_10k"]) / top["score_per_10k"] < TIE_TOLERANCE)
    sensitivity = []
    for name, variant in variants.items():
        variant_top = next((r for r in variant if r["reach_total"] > 0), None)
        sensitivity.append({
            "variant": name,
            "top_pick": variant_top["name"] if variant_top else None,
            "changes_recommendation": bool(top and variant_top and variant_top["business_id"] != top["business_id"]),
        })

    return {
        "status": "success",
        "assumptions": {
            "closure_risk_reduction": risk_drop,
            "assumption_name": assumption,
            "max_hops": DEFAULT_HOPS,
            "path_weighting": "product of supply intensities along the path; strongest path per business",
            "hub_rule": f"top {1 - HUB_PERCENTILE:.0%} of suppliers by direct buyers get x{HUB_ROBUSTNESS}",
            "edge_basis": "Supply links are MODELED (BEA industry averages); loans are REAL (SBA).",
            "allocation": ("full requests in score order; the leftover (>= "
                           f"${MIN_PARTIAL_AWARD:,}) goes to the next-best applicant with a cascade as a "
                           "partial award, effect assumed proportional to the share of its request"),
        },
        "ranking": ranking,
        "recommendation": top,
        "runner_up": runner_up,
        "indistinguishable": indistinguishable,
        "sensitivity": sensitivity,
        "budget": int(budget),
        "unfunded_budget": remaining,
        "partial_award": partial_award,
    }
