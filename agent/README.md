# `grant_advisor`: Team TRT3's ADK agent

A grant advisor for a city economic-development officer: corridor + budget + applicant queue in,
a defended **Grant Memo** out, with the multi-hop cascade it protects shown.

```
agent/grant_advisor/
  agent.py        root_agent (Gemini + tools)            owner P1
  prompts.py      system instruction                     owner P1 (+P6)
  tools/
    data.py       data access: mock corridor OR BigQuery (multi-hop GQL lives here)   P2/P3/P4
    cascade.py    get_cascade        custom tool: downstream exposure                 P4
    scoring.py    rank_applicants    custom tool: judgment + allocation + sensitivity P3
    audit.py      equity_audit       custom tool: industry + tract comparison         P3
    memo.py       build_grant_memo   custom tool: 7-section memo + Graphviz DOT       P4
    lookup.py     local stand-ins for the MCP Toolbox tools (used only if TOOLBOX_URL is empty)
    mock_data.py  14-business mock corridor (illustrative names)
```

## Run locally (mock data, no cloud needed for the tools)

```bash
cd agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r grant_advisor/requirements.txt pytest
cp grant_advisor/.env.example grant_advisor/.env     # USE_MOCK_DATA=true by default
gcloud auth application-default login                 # Gemini via Vertex AI (lab account)
adk web                                               # http://localhost:8000 → grant_advisor
```
Try: *"I have $50,000. Who should we fund?"* → *"Why Bayside Roasters and not Golden Produce Wholesale?"* → *"Write it up."*

Tests (offline, mock corridor): `pytest ../tests -q` from `agent/`, or `pytest tests -q` from the repo root.

## Switch to real data

When P2 has loaded `a4i_econ` and created the `LocalEconomy` graph (`business_tract` and
`applicants` too), set `USE_MOCK_DATA=false` in `.env`. Set `TOOLBOX_URL` to use MCP Toolbox.

## Deploy

`bash scripts/deploy_agent.sh mock|real` from the repo root (see [terraform/README.md](../terraform/README.md)).
The local `.env` is excluded from deploys by `grant_advisor/.gcloudignore`. ADK would otherwise
load it with override=True and replace the Cloud Run settings.

---

# Your agent goes here (original challenge brief)

This folder is empty on purpose.

We built the on-ramp: a real commercial corridor, real businesses, one fully real
business-to-business relationship, two modeled ones built on published federal rates, a
neighborhood need signal, and a validation suite that tells you plainly whether any of it is
wrong. We did not build the vehicle. The design decisions in your agent are what you are judged
on.

## What has to be true of what you build here

- **An ADK agent**, in Python.
- **At least one tool you built yourself.** A Python function tool, or one you defined in MCP
  Toolbox—either counts. The obvious candidate wraps your cascade query. The more valuable one
  holds the logic that is not a single query: deciding what counts as exposure, weighting a path,
  turning a set of paths into a funding recommendation with an amount attached. Consuming only
  prebuilt generic tools and calling that your design does not count.
- **At least one Google-managed MCP server, consumed.** Do not author your own—use BigQuery's
  built-in server or the [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox).
- **Deployed to Google Cloud**—Agent Runtime or Cloud Run, your choice.
- **Your required differentiator: a BigQuery property graph, genuinely traversed.** Your agent
  must run a real multi-hop `MATCH`. A single-hop query, or a `JOIN` with the word "graph" in the
  variable name, does not count—and it is the most common way a team misses the point while
  appearing to hit it.

## The thing worth remembering while you build

**A graph makes a consequence visible. It does not make the decision.**

The most connected business in your corridor is not automatically the best investment—it may
simply be the most robust one. A business three hops downstream with a weak coefficient is barely
affected by anything. And two of your three edge types are modeled by us, which should change
how much weight a recommendation carries.

An agent that ranks by centrality and funds the top of the list has rebuilt Section 2's wrong
answer with extra steps. What you do *after* the traversal—deciding what exposure means,
what the money actually changes, and what you are assuming—is where this becomes useful instead
of merely clever.

See Section 13 of the notebook for the DDL shape and the seven traps.
