"""Pure helpers that turn the agent's tool responses into tables and Graphviz pictures."""

import re

HOP_COLORS = {1: "#ffcc80", 2: "#fff59d", 3: "#e6ee9c"}
MAX_PATHS_IN_PICTURE = 10


def _quote(name: str) -> str:
    return '"' + str(name).replace('"', "'") + '"'


def cascade_dot(cascade: dict, limit: int = MAX_PATHS_IN_PICTURE) -> str:
    """Graphviz DOT for one cascade (get_cascade response): seed in blue, exposed by hop distance."""
    seed = (cascade.get("seed") or {}).get("name", "seed")
    exposed = (cascade.get("exposed") or [])[:limit]
    lines = ["digraph cascade {", "  rankdir=LR;", '  node [shape=box, style="rounded,filled", fontname="Helvetica"];',
             f'  {_quote(seed)} [fillcolor="#90caf9"];']
    hops: dict[str, int] = {}
    edges: set[tuple[str, str]] = set()
    for row in exposed:
        names = row.get("path_names") or [seed, row["name"]]
        for i, name in enumerate(names[1:], start=1):
            hops[name] = min(hops.get(name, i), i)
        edges.update(zip(names, names[1:]))
    for name, hop in sorted(hops.items()):
        if name != seed:
            lines.append(f'  {_quote(name)} [fillcolor="{HOP_COLORS.get(hop, "#eeeeee")}"];')
    lines += [f"  {_quote(a)} -> {_quote(b)};" for a, b in sorted(edges)]
    lines.append("}")
    return "\n".join(lines)


def ranking_rows(ranking: dict) -> list[dict]:
    """Display rows for the funding queue (rank_applicants response)."""
    rec = (ranking.get("recommendation") or {}).get("business_id")
    runner = (ranking.get("runner_up") or {}).get("business_id")
    rows = []
    for r in ranking.get("ranking") or []:
        badge = "★ pick" if r["business_id"] == rec else ("runner-up" if r["business_id"] == runner else "")
        if r.get("partial"):
            badge = (badge + " · partial").strip(" ·")
        poverty = r.get("tract_poverty")
        rows.append({
            "": badge,
            "Business": r.get("name"),
            "Requested": r.get("requested"),
            "Funded": r.get("funded_amount"),
            "Reach (1 hop / 2 hops)": f"{r.get('reach_hop1', 0)} / {r.get('reach_hop2', 0)}",
            "Hub": "yes" if r.get("is_hub") else "",
            "Tract poverty": f"{poverty:.0%}" if poverty is not None else "n/a",
            "Score per $10k": r.get("score_per_10k"),
            "business_id": r.get("business_id"),
        })
    return rows


def path_rows(cascade: dict) -> list[dict]:
    return [{"Exposed business": r.get("name"), "Hops": r.get("hops"),
             "Path": " → ".join(r.get("path_names") or []),
             "Strength": r.get("path_strength"), "Weakest link": r.get("weakest_link")}
            for r in cascade.get("exposed") or []]


_SOURCE_RE = re.compile(r'"data_source"\s*:\s*"([^"]+)"')


def find_data_source(obj) -> str | None:
    """Finds a data_source label in tool responses (dicts, lists, or MCP text payloads)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("data_source"), str):
            return obj["data_source"]
        values = obj.values()
    elif isinstance(obj, (list, tuple)):
        values = obj
    elif isinstance(obj, str):
        match = _SOURCE_RE.search(obj)
        return match.group(1) if match else None
    else:
        return None
    for value in reversed(list(values)):
        found = find_data_source(value)
        if found:
            return found
    return None


def data_source_badge(label: str | None) -> tuple[str, str]:
    """(streamlit element, text): green for real BigQuery, orange for the mock corridor."""
    if not label:
        return "info", "⚪ Data source: shown after the first query"
    if label.startswith("MOCK"):
        return "warning", f"🟠 Data: {label}"
    return "success", f"🟢 Data: {label}"
