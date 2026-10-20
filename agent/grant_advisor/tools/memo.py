from . import data
from .audit import equity_audit
from .cascade import EDGE_BASIS, get_cascade
from .scoring import CLOSURE_RISK_REDUCTION, rank_applicants

TOP_PATHS_IN_PICTURE = 8


def _dot(seed: dict, exposed: list[dict]) -> str:
    """Graphviz DOT of the strongest paths: one legible cascade, not the whole corridor."""
    lines = ["digraph cascade {", "  rankdir=LR;", '  node [shape=box, style="rounded,filled", fillcolor="#eeeeee"];',
             f'  "{seed["name"]}" [fillcolor="#90caf9"];']
    edges = set()
    for row in exposed[:TOP_PATHS_IN_PICTURE]:
        names = row.get("path_names") or [seed["name"], row["name"]]
        for a, b in zip(names, names[1:]):
            edges.add((a, b))
    lines += [f'  "{a}" -> "{b}";' for a, b in sorted(edges)]
    lines.append("}")
    return "\n".join(lines)


def _path_table(exposed: list[dict], limit: int = 10) -> str:
    if not exposed:
        return "_No downstream supply links: the graph cannot show a cascade._"
    rows = ["| Exposed business | Hops | Path | Strength (product) | Weakest link |", "|---|---:|---|---:|---:|"]
    for r in exposed[:limit]:
        path = " → ".join(r.get("path_names") or [r["name"]])
        rows.append(f"| {r['name']} | {r['hops']} | {path} | {r['path_strength']:.4f} | {r['weakest_link']:.3f} |")
    return "\n".join(rows)


def _pct(value):
    return f"{value:.0%}" if value is not None else "n/a"


def build_grant_memo(business_id: str, amount: int, runner_up_id: str = "",
                     assumption: str = "base") -> dict:
    """Writes the Grant Memo an officer can take into Friday's meeting: who, how much, the cascade
    it protects (with the traversal shown), why not the runner-up, assumptions, modeled evidence,
    and who the neighborhood is.

    Args:
        business_id: The business recommended for funding.
        amount: Grant amount in USD.
        runner_up_id: The next-best applicant to compare against (optional).
        assumption: "base", "pessimistic" or "optimistic" closure-risk reduction.

    Returns:
        dict with 'status', 'memo_markdown' (return it to the officer unchanged) and 'cascade_dot'
        (Graphviz picture of the strongest paths).
    """
    pick = get_cascade(business_id)
    if pick["status"] != "success":
        return pick
    runner = get_cascade(runner_up_id) if runner_up_id else None
    if runner is not None and runner["status"] != "success":
        runner = None
    ranking = rank_applicants(assumption=assumption)
    by_id = {r["business_id"]: r for r in ranking.get("ranking", [])} if ranking["status"] == "success" else {}
    funded_ids = [r["business_id"] for r in by_id.values() if r.get("funded_amount")]
    if business_id not in funded_ids:
        funded_ids.append(business_id)
    audit = equity_audit(funded_ids)
    hood = data.neighborhood(business_id) or {}
    seed = pick["seed"]
    risk_drop = CLOSURE_RISK_REDUCTION.get(assumption, CLOSURE_RISK_REDUCTION["base"])
    reach = pick["counts"]["total"]

    if runner:
        mine, theirs = by_id.get(business_id, {}), by_id.get(runner_up_id, {})
        comparison = (
            f"**{runner['seed']['name']}** protects {runner['counts']['total']} businesses "
            f"(exposure score {runner['exposure_score']:.3f}) vs **{seed['name']}** "
            f"{reach} (score {pick['exposure_score']:.3f})."
        )
        if mine and theirs:
            comparison += (f" Per $10k requested: {mine['score_per_10k']:.4f} vs {theirs['score_per_10k']:.4f}."
                           + (" The runner-up is a hub, so we assume it is likelier to survive unaided." if theirs.get("is_hub") else ""))
        if ranking.get("indistinguishable"):
            comparison += (" **On this evidence the two are nearly indistinguishable (<10% apart)**; real supplier "
                           "relationships (an intake interview) would separate them.")
    else:
        comparison = "_No runner-up provided._"

    sensitivity = "\n".join(
        f"- {s['variant'].replace('_', ' ')}: top pick **{s['top_pick']}**"
        + (" ⚠️ changes the recommendation" if s["changes_recommendation"] else " (unchanged)")
        for s in ranking.get("sensitivity", []))

    memo = f"""# Grant Memo: {seed['name']}

## 1. Recommendation
Fund **{seed['name']}**, {seed.get('address') or 'address n/a'} (NAICS {seed.get('naics4')}), **${int(amount):,}**.

## 2. What it protects
{reach} downstream businesses ({pick['counts']['hop1']} direct buyers, {pick['counts']['hop2']} two hops out).
Under our assumption, that is about **{risk_drop * reach:.1f}** businesses spared a supply shock.

## 3. The traversal (multi-hop `MATCH (seed)-[:Supplies]->{{1,2}}(exposed)`)
{_path_table(pick['exposed'])}

## 4. Why this one and not the runner-up
{comparison}

## 5. What we are assuming
A grant changes a probability, not an outcome. We assume the full grant cuts this business's 12-month
closure risk by **{risk_drop:.0%}**. Path strength multiplies BEA purchase intensities along each path.
Robustness of the recommendation:
{sensitivity or '- (sensitivity unavailable)'}

## 6. Which evidence is modeled
{EDGE_BASIS} Businesses, SBA loans and demographics are real.

**Data source:** {data.data_source_label()}

## 7. Who the neighborhood is
Census tract {hood.get('tract', 'n/a')}: poverty {_pct(hood.get('poverty_rate'))}, households without a vehicle
{_pct(hood.get('no_vehicle_rate'))}, on public assistance {_pct(hood.get('assistance_rate'))}.
{audit.get('finding', '') if audit.get('status') == 'success' else ''}
_(Equity audit covers all {len(funded_ids)} businesses funded in this allocation.)_
"""
    return {"status": "success", "memo_markdown": memo, "cascade_dot": _dot(seed, pick["exposed"])}
