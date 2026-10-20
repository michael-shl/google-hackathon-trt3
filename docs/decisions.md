# Decision log — Team TRT3

Every design choice we make, and **why**. Judges score "Rigor & judgment" (25 pts) on whether
decisions were made on purpose. Add a row whenever we choose something; never delete rows.

| # | Time | Decision | Alternatives considered | Why | Owner |
|---|---|---|---|---|---|
| D1 | | Corridor: | | | P1 |
| D2 | | Track: | | | P1 |
| D3 | | Scenario: | | | P6 |
| D4 | | Traversal depth: **`{1,2}` on Supplies** (proposed, in `scoring.DEFAULT_HOPS`) | `{1,3}` | Notebook trap #6: 3 hops reaches ~200 of 230 businesses and stops discriminating | P3 |
| D5 | | Front end: **Grant Desk (Streamlit) over the agent API; `adk web` kept as debug view + fallback** | `adk web` only; Gemini Enterprise; React app | User is an internal grant officer working a funding queue; panels are drawn from the agent's own tool responses so the traversal is shown, not described. Streamlit fits a 1-hour build | P5/P1 |
| D6 | | MCP server: **MCP Toolbox on Cloud Run, curated read-only tools** (proposed) | BigQuery built-in MCP; free-form `execute_sql` | Lookups through the managed MCP server; judgment stays in custom tools; no arbitrary SQL from the LLM | P5 |
| D7 | | Path weighting: **product of intensities, strongest path per exposed business** (proposed v1) | product of intensities / weakest link / count | Multiplying decays naturally with distance; weakest-link is reported as a sensitivity variant | P3 |
| D8 | | What a grant changes: **full request cuts 12-month closure risk by 10 pts** (pessimistic 5, optimistic 20) | | No data answers this; we state it and show how the expected effect scales | P3 |
| D9 | | Hub rule: **top 5% of suppliers by direct buyers get a x0.5 robustness discount** (proposed v1) | no discount | The most connected business is often the most robust; "no hub discount" is reported as a sensitivity variant | P3 |
| D10 | | Ranking metric: **protected exposure per $10k requested**, tract poverty as tie-breaker; businesses with no downstream links are not funded on cascade grounds | rank by centrality | Avoids rebuilding the "fund the hub" answer; need is visible but not a hidden weight | P1/P3 |
| D11 | | Agent works on a **mock corridor** until BigQuery is ready (`USE_MOCK_DATA`) | wait for data | Agent, front end and deploy lanes are not blocked by the critical path | P1 |
| D12 | 14:05 | Allocation: **full requests in score order; the leftover goes to the next-best applicant with a cascade as a partial award** (effect assumed proportional to share of request; no award under $1,000) | all-or-nothing (left $5k idle); leftover by need to a no-cascade applicant | Uses the whole fund on the same criterion as every other award; the proportional assumption is the one the agent already states for partial amounts | P1 |
