# 3-Minute Presentation Script & Pitch Guide — Team 3

> **Project:** Grant Advisor (Challenge 3: Community Economic Resilience & Micro-Grants)  
> **Track:** Main Street Relief | **Corridor:** Central Market, San Francisco  
> **Presentation Deck (6 Slides):** [presentation/grant_advisor_pitch_deck.pptx](file:///Users/michaelli/Documents/google-hackathon-trt3/presentation/grant_advisor_pitch_deck.pptx)  
> **Google Slides Source:** [Google Slides Link](https://docs.google.com/presentation/d/1gK3jVwMgURpqdLVLOKMxNdh6Rvl7ZQC4KFxzPrUtLtw/edit?pli=1#slide=id.h52fa8b8a4798773f_0_130)  
> **Live App:** https://grant-desk-245858333498.us-central1.run.app/  
> **GitHub Integration:** https://github.com/michael-shl/google-hackathon-trt3/tree/rc/1.0.0  
> **Total Time:** 3:00 (180 Seconds) | **Target Speaking Rate:** 135–145 words/minute (~410 words total)

---

## Timing & Slide Overview

| Slide # | Slide Title | Duration | Cumulative Time | Key Takeaway / Focus |
|:---:|---|:---:|:---:|---|
| **1** | Title: Grant Advisor | **25s** | 0:00 – 0:25 | The Hook: Small businesses don't fail in isolation; they hold each other up. |
| **2** | Team Roster & Logistics | **20s** | 0:25 – 0:45 | Team 3 background, multi-disciplinary roles, and full operational readiness. |
| **3** | The Problem: Isolated Bailouts vs. Systemic Networks | **35s** | 0:45 – 1:20 | The $50k allocation dilemma; traditional spreadsheets miss multi-hop cascades. |
| **4** | The Solution: Network-Aware Autonomous Agent | **35s** | 1:20 – 1:55 | Google ADK, Gemini 2.5 Flash, BigQuery Property Graph GQL, sign-ready Grant Memo. |
| **5** | Live Demonstration & Deployment | **35s** | 1:55 – 2:30 | Live Grant Desk UI, $50k budget test, saving 4 downstream businesses via Bayside Roasters. |
| **6** | System Architecture & Engineering Rigor | **30s** | 2:30 – 3:00 | Cloud Run, MCP Toolbox, real vs modeled honesty, equity audit, and closing impact. |

---

## Word-for-Word Pitch Script

### Slide 1: Cover & Project Hook (0:00 – 0:25 | 25 Seconds)
*(Slide displays: Team 3 — Grant Advisor: Community Economic Resilience & Micro-Grants)*

> **[SPEAKER]**:  
> "A coffee roaster on Central Market closes. On a balance sheet, that’s one shuttered storefront and four lost jobs.  
> 
> But in reality, three cafes lose their primary morning supply, a local caterer misses events, and a nearby lunch counter loses daily footfall. None of those downstream businesses were in trouble last month—**they are in trouble today because of a closure nobody connected to them.**  
> 
> We are **Team 3**, and we built **Grant Advisor** for Main Street economic relief."

---

### Slide 2: Team & Operational Readiness (0:25 – 0:45 | 20 Seconds)
*(Slide displays: Team Roster table: Shihao Li, Daniel Wang, Harmeet D, Abhishek B, Jaskirat T)*

> **[SPEAKER]**:  
> "Our team unites engineering, data pipelines, agentic AI, and public sector workflow design.  
> 
> Across platform, data engineering, and product storytelling, we built an enterprise-ready system that turns raw corridor data into defensible public policy decisions—fully containerized, unit-tested, and live on Google Cloud."

---

### Slide 3: The Core Problem — Isolated Bailouts vs. Systemic Networks (0:45 – 1:20 | 35 Seconds)
*(Slide displays: Problem Statement & Systemic Impact callout)*

> **[SPEAKER]**:  
> "Here is why municipal relief is broken: a city grant officer might have **$50,000** and **40 desperate applicants**. The traditional approach ranks them by individual distress—who is nearest to bankruptcy.  
> 
> But that spreadsheet approach is blind to the only thing that makes a commercial corridor resilient: **businesses hold each other up.**  
> 
> Bailing out the most distressed leaf storefront protects only one business. Bailing out a keystone supplier **protects an entire commercial ecosystem 1 and 2 hops away**."

---

### Slide 4: The Solution — Network-Aware Autonomous Agent (1:20 – 1:55 | 35 Seconds)
*(Slide displays: The Agent, User Interaction, and Concrete Outcome)*

> **[SPEAKER]**:  
> "To solve this, we built **Grant Advisor** using the **Google Agent Development Kit (ADK)** and **Gemini 2.5 Flash**.  
> 
> Instead of writing arbitrary SQL, our agent queries a **BigQuery Property Graph** using multi-hop **GQL queries** to trace supply and footfall cascades.  
> 
> An economic development officer simply enters a relief budget and scenario in plain English. In seconds, Grant Advisor stress-tests allocations, visualizes dependency graphs, and produces a complete, sign-ready **7-section Grant Memo** with census-tract equity auditing."

---

### Slide 5: Live Demonstration & Officer Workflow (1:55 – 2:30 | 35 Seconds)
*(Slide displays: Live App URL `grant-desk-...run.app`, Git repo, and Test Scenario breakdown)*

> **[SPEAKER]**:  
> "Our application is live on Cloud Run today.  
> 
> In our Central Market scenario with a **$50,000 budget across 11 applicants**, traditional ranking would fund the most vocal applicants until the money runs out.  
> 
> Grant Advisor does something fundamentally different: it identifies **Bayside Roasters**—an $8,000 request that isn't the most connected hub, but protects **four healthy downstream storefronts** across two hops. It allocates full grants in priority order, assigns partial leftovers intelligently, and renders the exact Graphviz cascade right in the officer's **Grant Desk**."

---

### Slide 6: System Architecture & Engineering Rigor (2:30 – 3:00 | 30 Seconds)
*(Slide displays: System Architecture Diagram, Cloud Run, Vertex AI, BigQuery Graph, and Rigor notes)*

> **[SPEAKER]**:  
> "Under the hood, everything runs on Google Cloud. The **Streamlit Grant Desk**, the **ADK Agent**, and a **Google-managed MCP Toolbox server** run as private Cloud Run services with least-privilege IAM and zero cold starts.  
> 
> Most importantly, we prioritized **rigor over hype**: we distinguish measured SBA loan and Census demographics from modeled BEA supply rates; we apply a **robustness discount** so we don't blindly fund massive hubs; and we audit neighborhood poverty impact.  
> 
> Grant Advisor turns emergency relief from isolated gambles into systemic neighborhood preservation. Thank you!"

---

## Presenter Delivery Tips

1. **Energy & Pace:**
   - Speak with steady confidence. Do not rush through the numbers.
   - Pause for 1 second after *"businesses hold each other up"* on Slide 3. That is the philosophical core of Challenge 3.
2. **Emphasize the Traversal:**
   - Judges check whether you genuinely traversed a graph or just did a SQL `JOIN`. Explicitly highlight **"multi-hop GQL queries"** on Slide 4 and Slide 6.
3. **Stand by the Rigor:**
   - Mentioning that BEA supply links are *modeled* while SBA loans are *measured* proves technical maturity. Hackathon judges reward honesty about data provenance.

---

## Judge Q&A Cheat Sheet (Anticipated Questions & Defense)

### Q1: "How do you distinguish real data from modeled data in your graph?"
> **Answer:**  
> "The businesses (Google Places), employer worker counts (Census LEHD), demographic poverty tracts (ACS), and historical SBA loans (`borrowed_from`) are 100% measured public data.  
> The supply-chain links (`supplies`) and worker footfall (`draws_footfall_from`) are modeled using published federal Bureau of Economic Analysis (BEA) Input-Output direct requirements tables mapped to local business pairs. We state this explicitly in Section 6 of every Grant Memo."

### Q2: "Why shouldn't the city just fund the biggest, most connected business in the corridor?"
> **Answer:**  
> "Because the most connected business is almost always the most robust—it has diverse buyers, higher cash flow, and institutional credit access. If you rank strictly by centrality, you bail out large hubs that would have survived anyway.  
> Our agent applies a **top-5% hub robustness discount** and scores candidates on **protected exposure per dollar requested**, ensuring scarce public funds protect vulnerable keystones."

### Q3: "What does an $8,000 grant actually guarantee?"
> **Answer:**  
> "No public data can guarantee a private business won't fail. In our decision model (D8), a full grant is assumed to reduce 12-month closure risk by a baseline of **10 percentage points**.  
> Crucially, our agent runs **sensitivity analysis** at 5 points (pessimistic) and 20 points (optimistic) inside the Grant Memo, showing the officer exactly how the ranking holds up under different assumptions."

### Q4: "Why build a custom Streamlit UI instead of using the standard `adk web` interface?"
> **Answer:**  
> "Our end user is a municipal grant officer presenting to a city council or board on Friday, not a software engineer inspecting JSON event streams.  
> Streamlit allowed us to build the **Grant Desk** in one hour, rendering the applicant queue, interactive Graphviz cascade diagrams, and downloadable memos directly from the agent's tool responses—while `adk web` remains active as our technical debug view."

### Q5: "How does the architecture prevent arbitrary or dangerous LLM queries?"
> **Answer:**  
> "We split responsibilities cleanly: read-only corridor lookups run through the **Google-managed MCP Toolbox server** with fixed, parameterized SQL queries. The multi-hop graph traversal and scoring algorithms run in deterministic, unit-tested custom Python tools. Gemini 2.5 Flash acts as the orchestrator and policy synthesizer, not an unconstrained SQL generator."
