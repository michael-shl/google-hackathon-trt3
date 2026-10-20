"""The ADK agent loads and every tool exposes a valid function declaration to Gemini."""

import importlib

from google.adk.tools import FunctionTool


def test_root_agent_loads_with_local_lookups():
    from grant_advisor import agent

    names = {getattr(t, "__name__", type(t).__name__) for t in agent.root_agent.tools}
    assert agent.root_agent.name == "grant_advisor"
    assert {"get_cascade", "rank_applicants", "equity_audit", "build_grant_memo",
            "find_business", "list_applicants", "get_neighborhood", "get_loan_history"} <= names


def test_tool_declarations_are_valid():
    from grant_advisor.tools import CUSTOM_TOOLS, LOCAL_LOOKUP_TOOLS

    for fn in [*CUSTOM_TOOLS, *LOCAL_LOOKUP_TOOLS]:
        declaration = FunctionTool(fn)._get_declaration()
        assert declaration.name == fn.__name__
        assert declaration.description


def test_toolbox_used_when_url_set(monkeypatch):
    monkeypatch.setenv("TOOLBOX_URL", "http://127.0.0.1:5000")
    from grant_advisor import agent

    try:
        reloaded = importlib.reload(agent)
        kinds = {type(t).__name__ for t in reloaded.root_agent.tools}
        assert "ToolboxToolset" in kinds
        assert "find_business" not in {getattr(t, "__name__", "") for t in reloaded.root_agent.tools}
    finally:
        monkeypatch.setenv("TOOLBOX_URL", "")
        importlib.reload(agent)
