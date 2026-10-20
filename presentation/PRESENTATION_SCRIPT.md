# 3-Minute Pitch Script: Team 3, Grant Advisor

**Challenge 3** · Track: Main Street Relief · Corridor: Central Market, San Francisco
Deck: [grant_advisor_pitch_deck.pptx](grant_advisor_pitch_deck.pptx) ·
[Google Slides source](https://docs.google.com/presentation/d/1gK3jVwMgURpqdLVLOKMxNdh6Rvl7ZQC4KFxzPrUtLtw/edit?pli=1#slide=id.h52fa8b8a4798773f_0_130) ·
Repo: https://github.com/michael-shl/google-hackathon-trt3 (branch `main`)

The app is a **private** Cloud Run service; record the demo through
`gcloud run services proxy grant-desk --region us-central1 --port 8501`.
Click **Rank applicants** once before recording to warm the cache.

| Slide | Time | Point to land |
|:-:|:-:|---|
| 1 Title | 0:00–0:20 | Businesses hold each other up |
| 2 Team | 0:20–0:30 | Who we are |
| 3 Problem | 0:30–1:00 | Ranking one by one misses the network |
| 4 Solution | 1:00–1:35 | ADK + Gemini walk a BigQuery property graph |
| 5 Demo | 1:35–2:30 | Real data: who gets funded, and why |
| 6 Architecture & rigor | 2:30–3:00 | Honest about what is modeled |

## Script (~370 words)

**1 · Title (20 s).** "A coffee roaster on Central Market closes. On paper that is one storefront. In reality
the cafés it supplies lose their beans, and the caterer they buy from loses orders. None of them was in
trouble last month. We are Team 3, and we built **Grant Advisor**."

**2 · Team (10 s).** "Five of us, covering data, the agent, the platform and the story."

**3 · Problem (30 s).** "A city has $50,000 and more applicants than money. Ranking them one by one misses
the supply chains between them, so one closure can push businesses one or two hops away into trouble.
Officers need a defensible way to fund the businesses that protect the most others."

**4 · Solution (35 s).** "Grant Advisor is a **Google ADK** agent on **Gemini 2.5 Flash**. Its tools walk a
**BigQuery property graph** with a multi-hop GQL query, `MATCH (seed)-[:Supplies]->{1,2}(exposed)`, to find
every business a closure would expose. The officer sets a budget in the Grant Desk; the agent ranks the
queue, traces the cascade and writes a **Grant Memo**: who, how much, what it protects, why not the
runner-up, and an equity audit."

**5 · Demo (55 s).** *(Rank → Trace cascade → Write memo → one suggested question.)*
"Real data: 232 Central Market businesses and 11 applications. With $50,000 it funds **Cumaica Coffee
($20k)** and **Sour Flour ($25k)**; each protects **148 businesses** within two hops. The last **$5,000**
goes to **G.Rabbit** as a partial grant, so no money sits idle. Every path on screen comes from the live
graph query. And when we ask about Eddy St Bodega, it says plainly that the graph shows no cascade.
It doesn't invent one."

**6 · Architecture & rigor (30 s).** "Everything runs as private Cloud Run services: the Grant Desk, the
agent, and a Google-managed **MCP Toolbox** for read-only lookups. We label every answer real or modeled:
businesses, SBA loans and census need are real; supply links are modeled from federal industry rates.
The equity audit shows our own bias: funding leans to manufacturing because those businesses have the
most modeled links. A grant changes a probability, not an outcome, and the memo says so. Thank you."

## Judge Q&A (short answers)

**Which data is real and which is modeled?** Real: 232 SF registered businesses, SBA 7(a) loans, Census
LEHD jobs, ACS demographics. Modeled: supply and footfall links (BEA industry rates assigned to nearby
pairs). Applications are simulated. Every answer and memo carries a data-source label.

**Why fund the two biggest hubs?** We apply a hub robustness discount (×0.5), but on this corridor
Cumaica Coffee and Sour Flour still lead: 148 businesses each, against 18 for the next applicant. We show
the trade-off instead of hiding it: the equity audit flags the skew, and the sensitivity check reports
it. Next step: diminishing returns or a cap per grant.

**What does a grant actually change?** No data can say. We assume a full grant cuts 12-month closure risk
by 10 points, show 5 and 20 as bounds, and the decision is the same across all three; only the impact
changes. See [GRANT_ASSUMPTION.md](../docs/GRANT_ASSUMPTION.md).

**Why a custom UI instead of `adk web`?** The user is a grant officer working a funding queue. The Grant
Desk draws its tables and cascade diagram from the agent's own tool responses; `adk web` stays our
debugging view.

**How do you stop arbitrary LLM queries?** Lookups go through the MCP Toolbox's fixed, parameterized,
read-only SQL. The graph traversal and scoring are tested Python tools (31 tests). Gemini routes requests
and writes the answer; it never writes SQL.
