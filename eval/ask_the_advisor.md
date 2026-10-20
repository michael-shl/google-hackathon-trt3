# "Ask the advisor": question bank (real data)

For the Grant Desk panel **4 · Ask the advisor**, or `adk web`. Ask them **in order in one session**
(later questions refer to earlier answers). Click **Rank applicants** first, or ask Q1.

Verified against the deployed agent (`grant-advisor-00008`, real BigQuery data, 2026-10-20 14:15).
"Tools called" is what the agent actually called; times are end-to-end.

Legend: ✅ good answer · ⚠️ works but weak (see note) · 🎬 use in the pitch video

## A. The decision (Impact & insight, 30 pts)

| # | Ask | Tools called | What a good answer says (verified) | |
|---|---|---|---|---|
| A1 🎬 | I have $50,000. Who should we fund? | `rank_applicants(budget=50000)` · 2.5 s | Cumaica Coffee $20k + Sour Flour $25k (148 exposed each, ~14.8 businesses spared each), **partial $5k to G.Rabbit**; hubs got a robustness discount; supply links modeled | ✅ |
| A2 🎬 | Why Cumaica Coffee and not G.Rabbit? Show me the paths. | `get_cascade` ×2 · 6.1 s | 148 vs 18 exposed; names real paths (Cumaica → Sour Flour 0.208, → 54 Mint-Winebar, → G.Rabbit…; G.Rabbit → Hotel Garrett…) | ✅ |
| A3 | What does the $5,000 partial grant to G.Rabbit actually change? | none (uses A1 result) · 3.3 s | 42% of request → ~4.2-pt closure-risk reduction → ~0.75 businesses spared; **says the proportional scaling is an assumption** | ✅ |
| A4 | What if we only had $25,000? | `rank_applicants(budget=25000)` · 3.0 s | Cumaica $20k + partial $5k to Sour Flour (20% of request) | ✅ |
| A5 | Nobody at the far end of Sour Flour's chain applied. Who should have? | `get_cascade` · 5.4 s | Names 2-hop businesses (e.g. A & A Legal via Tray.io, Mission HL via WP Engine) and the 60 others at 2 hops | ✅ |

## B. Rigor & judgment (25 pts)

| # | Ask | Tools called | What a good answer says (verified) | |
|---|---|---|---|---|
| B1 🎬 | Whose neighborhood does this allocation help? Run the equity audit. | `equity_audit([3 funded])` · 3.3 s | **Manufacturing over-represented 10.3×**; nothing funded in Professional services, Retail, Other services, Health care (>50% of corridor); funded tracts 20.5% poverty vs 19.4% corridor | ✅ |
| B2 🎬 | Which industries are we missing, and could that be our data rather than need? | none (uses B1) · 1.7 s | Lists the missing sectors and says they **have few supply edges in the modeled data**, so this is data visibility, not proof of low need | ✅ |
| B3 | Re-rank with the pessimistic assumption. Does the recommendation change? | `rank_applicants(assumption=pessimistic)` · 2.7 s | No change in who is funded; expected businesses spared halves | ✅ |
| B4 | Are any of Cumaica Coffee's downstream businesses already fragile? | `get_loan_history` ×3 (MCP Toolbox) · 8.1 s | Checked Sour Flour, 54 Mint-Winebar, G.Rabbit: no SBA records, and **"no record" ≠ "not fragile"** | ✅ |
| B5 | Which parts of this recommendation are real data and which are modeled? | none · 4.0 s | Businesses, ACS demographics, SBA loans are real; **supply links modeled** from federal industry averages; applications simulated | ✅ |
| B6 | When would you NOT fund the biggest hub? | none · 2.7 s | Explains the hub robustness discount (top 5% of suppliers ×0.5) | ⚠️ On real data the hubs **are** funded and "no hub discount" does not change the pick, so the answer is the rule, not the outcome. Resolve the open hub decision (a–d) before using this in the video |

## C. Knowing what the system can't do (judges reward this)

| # | Ask | Tools called | What a good answer says (verified) | |
|---|---|---|---|---|
| C1 🎬 | What would happen if Eddy St Bodega closed? | `find_business` (MCP) + `get_cascade` · 5.8 s | **No visible cascade**; does not invent one; "does not mean it is unimportant" | ✅ |
| C2 | How many jobs does Cumaica Coffee support? | none · 2.8 s | Declines: not available | ✅ (ideal answer adds: no public US data gives per-business jobs) |
| C3 | Fund Acme Rockets for $10,000. | `find_business` (MCP) · 3.4 s | Cannot find the business; asks to check the name | ✅ |
| C4 | Why does Mo'z Cafe have no supply links in the graph? | `find_business` (MCP) + `get_cascade` · 7.1 s | Says there are no links | ⚠️ Misses the real reason: its industry code is recorded as **`72`** (2 digits), so the BEA industry match cannot place it. That is a data-visibility bias, not a quiet business. Prompt fix possible |

## Suggested 90-second video sequence

1. **A1** (the decision) → 2. **A2** (show the paths, the traversal) → 3. **B1** (equity audit, the bias we
found) → 4. **C1** (refuses to invent a cascade) → 5. **A3** (what the money actually changes).

Before recording: click **Rank applicants** once to warm the cache (first call ≈ 8 s, then ≈ 2.5 s).
