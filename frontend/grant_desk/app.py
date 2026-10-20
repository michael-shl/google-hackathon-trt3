"""Grant Desk: a one-page front end for the grant_advisor agent (owner: P5).

Run locally (agent reachable via `gcloud run services proxy grant-advisor --port 8080`):
    streamlit run app.py
"""

import streamlit as st

from agent_client import AgentClient
from desk_views import cascade_dot, data_source_badge, find_data_source, path_rows, ranking_rows

st.set_page_config(page_title="Grant Desk · Central Market", page_icon="🏛️", layout="wide")
ss = st.session_state
for key, default in (("trace", []), ("chat", []), ("ranking", None), ("rank_text", ""),
                     ("cascade", None), ("cascade_text", ""), ("memo", None), ("data_source", None)):
    ss.setdefault(key, default)


@st.cache_resource
def client() -> AgentClient:
    return AgentClient()


def md(text: str) -> str:
    """Streamlit renders $...$ as LaTeX; agent text is full of dollar amounts."""
    return (text or "").replace("$", "\\$")


def ask(message: str, spinner: str, brief: bool = True):
    if "session_id" not in ss:
        ss.session_id = client().new_session()
    try:
        with st.spinner(spinner):
            turn = client().ask(ss.session_id, message, brief=brief)
    except Exception as exc:  # network/auth problems are shown, not raised
        st.error(f"Agent call failed: {exc}")
        return None
    ss.trace.append({"message": message, "calls": turn.tool_calls})
    source = find_data_source(turn.tool_responses)
    if source:
        ss.data_source = source
    for tool, key in (("rank_applicants", "ranking"), ("get_cascade", "cascade"), ("build_grant_memo", "memo")):
        resp = turn.latest(tool)
        if resp and resp.get("status") == "success":
            ss[key] = resp
    return turn


# ------------------------------------------------------------------ header + controls
st.title("🏛️ Grant Desk: Central Market micro-grants")
st.caption("Relief fund for the Central Market corridor, San Francisco. Every table and picture below is drawn "
           "from the agent's own tool calls over the corridor's supply-network property graph.")
header_source = st.empty()

with st.sidebar:
    st.header("Fund")
    sidebar_source = st.empty()
    budget = st.number_input("Budget (USD)", min_value=1000, max_value=1_000_000, value=50_000, step=5_000)
    assumption = st.selectbox("What a full grant changes", ["base", "pessimistic", "optimistic"],
                              format_func={"base": "Base: closure risk −10 pts",
                                           "pessimistic": "Pessimistic: −5 pts",
                                           "optimistic": "Optimistic: −20 pts"}.get)
    if st.button("Rank applicants", type="primary", use_container_width=True):
        turn = ask(f"I have ${budget:,}. Rank the applicants using rank_applicants with the {assumption} "
                   f"assumption and recommend who to fund.", "Ranking the queue…")
        if turn:
            ss.rank_text, ss.cascade, ss.memo = turn.text, None, None
    if st.button("New session", use_container_width=True):
        for key in ("session_id", "ranking", "cascade", "memo"):
            ss.pop(key, None)
        ss.trace, ss.chat, ss.rank_text, ss.cascade_text = [], [], "", ""
        st.rerun()
    st.divider()
    st.caption("**Evidence:** supply links are MODELED (BEA industry averages assigned to nearby business "
               "pairs). Businesses, SBA loans and census demographics are real. A grant changes a "
               "probability, not an outcome.")
    st.caption(f"Agent: `{client().base_url}`")

# ------------------------------------------------------------------ queue + cascade
left, right = st.columns([1.25, 1])

with left:
    st.subheader("1 · Funding queue")
    ranking = ss.ranking
    if not ranking:
        st.info("Set a budget and click **Rank applicants**.")
    else:
        funded = sum(r.get("funded_amount") or 0 for r in ranking.get("ranking", []))
        m1, m2, m3 = st.columns(3)
        m1.metric("Budget", f"${ranking.get('budget', 0):,}")
        m2.metric("Allocated", f"${funded:,}")
        m3.metric("Unallocated", f"${ranking.get('unfunded_budget', 0):,}")
        st.dataframe(ranking_rows(ranking), hide_index=True, use_container_width=True,
                     column_order=["", "Business", "Requested", "Funded", "Reach (1 hop / 2 hops)", "Hub",
                                   "Tract poverty", "Score per $10k"])
        if ranking.get("indistinguishable"):
            st.warning("The top two are within 10% of each other: indistinguishable on this evidence.")
        changed = [s for s in ranking.get("sensitivity", []) if s.get("changes_recommendation")]
        stable = [s for s in ranking.get("sensitivity", []) if not s.get("changes_recommendation")]
        if changed:
            st.warning("Recommendation changes under: " + ", ".join(
                f"{s['variant'].replace('_', ' ')} (→ {s['top_pick']})" for s in changed))
        if stable:
            st.caption("Stable under: " + ", ".join(s["variant"].replace("_", " ") for s in stable))
        if ss.rank_text:
            with st.expander("Agent's reasoning", expanded=True):
                st.markdown(md(ss.rank_text))

with right:
    st.subheader("2 · Cascade it protects")
    ranking = ss.ranking
    if not ranking:
        st.info("Rank the queue first.")
    else:
        options = {r["business_id"]: r["name"] for r in ranking.get("ranking", [])}
        default_id = (ranking.get("recommendation") or {}).get("business_id")
        ids = list(options)
        chosen = st.selectbox("Applicant", ids, index=ids.index(default_id) if default_id in ids else 0,
                              format_func=options.get)
        if st.button("Trace cascade (multi-hop graph traversal)", use_container_width=True):
            turn = ask(f"Show the downstream cascade for {options[chosen]} (business_id {chosen}) using "
                       f"get_cascade with 2 hops.", "Walking the supply graph…")
            if turn:
                ss.cascade_text = turn.text
        cascade = ss.cascade
        if cascade:
            counts = cascade.get("counts", {})
            st.markdown(f"**{cascade['seed']['name']}** → {counts.get('total', 0)} exposed "
                        f"({counts.get('hop1', 0)} direct, {counts.get('hop2', 0)} two hops out)")
            if cascade.get("exposed"):
                st.graphviz_chart(cascade_dot(cascade), use_container_width=True)
                st.dataframe(path_rows(cascade), hide_index=True, use_container_width=True)
            else:
                st.info(cascade.get("note", "No downstream supply links."))
            st.caption(cascade.get("edge_basis", ""))

# ------------------------------------------------------------------ memo
st.subheader("3 · Grant Memo")
rec, runner = (ss.ranking or {}).get("recommendation"), (ss.ranking or {}).get("runner_up")
if not rec:
    st.info("Rank the queue to get a recommendation, then write the memo.")
else:
    label = f"Write memo: fund {rec['name']} ${rec['requested']:,}" + (f" (runner-up {runner['name']})" if runner else "")
    if st.button(md(label), type="primary"):
        ask(f"Write it up for Friday with build_grant_memo: fund {rec['name']} (business_id {rec['business_id']}) "
            f"for ${rec['requested']}"
            + (f", runner-up {runner['name']} (business_id {runner['business_id']})" if runner else "")
            + f", {assumption} assumption.", "Writing the memo…")
    memo = ss.memo
    if memo:
        memo_col, pic_col = st.columns([1.5, 1])
        with memo_col:
            st.markdown(md(memo["memo_markdown"]))
            st.download_button("Download memo (.md)", memo["memo_markdown"], file_name="grant_memo.md")
        with pic_col:
            st.graphviz_chart(memo["cascade_dot"], use_container_width=True)

# ------------------------------------------------------------------ ask + trace
st.subheader("4 · Ask the advisor")
for question, answer in ss.chat:
    st.chat_message("user").markdown(md(question))
    st.chat_message("assistant").markdown(md(answer))
if question := st.chat_input("e.g. Are any of the downstream businesses already fragile?"):
    turn = ask(question, "Thinking…", brief=False)
    if turn:
        ss.chat.append((question, turn.text or "_(no text answer; see the panels above)_"))
        st.rerun()

with st.expander("Agent tool calls (the traversal behind this screen)"):
    for item in reversed(ss.trace):
        st.markdown(f"**{item['message']}**")
        st.code("\n".join(f"{c['name']}({c['args']})" for c in item["calls"]) or "(no tool calls)", language="text")

# ------------------------------------------------------------------ data source badge
# Filled last so it reflects the newest tool response from any button on this run.
kind, badge_text = data_source_badge(ss.data_source)
getattr(sidebar_source, kind)(badge_text)
header_source.caption(badge_text)
