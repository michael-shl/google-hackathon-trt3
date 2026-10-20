# Officer questions: UI test checklist (owners: P4 + P6)

Run these **in order, in one session**, after every deploy and before recording the video.
Rerun with real data once `USE_MOCK_DATA=false` (business names will differ from the mock run).

## How to open the UI

| Where | Command | URL |
|---|---|---|
| Deployed (Cloud Run, private) | `gcloud run services proxy grant-advisor --region us-central1 --port 8080` | http://localhost:8080/dev-ui/ |
| Local | `cd agent && source .venv/bin/activate && adk web` | http://localhost:8000/dev-ui/ |

On a laptop, first `export CLOUDSDK_CONFIG=~/.config/gcloud-hackathon` (lab student login). In the UI:
select **grant_advisor** (top-left), click **No Thanks** on the telemetry pop-up, and use **+** for a fresh session.

## For every answer, check three things

1. **Tool chips** (⚡ under the robot icon): the expected tool was called. Click a chip for its args and response.
2. **Content**: numbers come from the tool response, not invented; assumptions and "modeled" caveat stated.
3. **Events / Traces tab** (left panel): no red errors, and latency is OK for the demo.

## The questions

| # | Ask | Expected tools | Pass if |
|---|---|---|---|
| Q1 | I have $50,000. Who should we fund? | `rank_applicants` | Allocation within budget; top pick ≠ biggest hub, with the hub rule explained; leaves not funded on cascade grounds; 10-pt assumption + "supply links are modeled" stated |
| Q2 | Why ⟨#1⟩ and not ⟨biggest hub⟩? Show me the paths. | `get_cascade` ×2 | Both cascades listed with hops, path strength, and the 2-hop path *via* a named business |
| Q3 | Are any of ⟨#1⟩'s downstream businesses already fragile? | `get_cascade`, `get_loan_history` | Uses SBA loan records; says "no SBA record" rather than "no debt" when empty |
| Q4 | Nobody at the far end of that chain applied. Should they have? | `get_cascade` (+ `list_applicants`) | Names exposed businesses that are not in the queue |
| Q5 | What does a $8,000 grant actually change? | none or `rank_applicants` | Probability, not outcome; proportional-scaling arithmetic shown and labeled an assumption |
| Q6 | Whose neighborhood does funding ⟨#1⟩ help? | `get_neighborhood` (+ `equity_audit`) | Tract poverty / no-vehicle / assistance rates |
| Q7 | Write it up for Friday: fund ⟨#1⟩, runner-up ⟨#2⟩. | `build_grant_memo` | All 7 sections; traversal table with arrows; sensitivity list; equity finding |
| R1 | What would happen if ⟨a leaf, e.g. Mint Plaza Parking⟩ closed? | `find_business`, `get_cascade` | "Graph cannot show a cascade"; no invented exposure |
| R2 | Fund ⟨unknown name, e.g. Acme Rockets⟩. | `find_business` | Says it can't find the business; asks to clarify |

## Results log

| Date / revision | Data | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | R1 | R2 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 / grant-advisor-00002 | mock | ✅ | ✅ | – | – | ⚠️ | ✅ | ⚠️ | ✅ | – | Q5 vague about $8k (fixed in prompt); Q7 equity line said "lower poverty (24% vs 24%)" and flagged every single-business industry (fixed: sector-level audit, 1-pt tolerance) |
| 2026-10-20 / grant-advisor-00003 | mock | | | | | ✅ | | | | | Q5 now: 8,000/15,000 × 10 pts ≈ 5.3 pts, ~0.3 of 6 exposed businesses, labeled an assumption |
