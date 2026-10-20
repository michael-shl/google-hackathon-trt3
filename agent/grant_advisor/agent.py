import os

from google.adk.agents import Agent
from google.genai import types

from .prompts import INSTRUCTION
from .tools import CUSTOM_TOOLS, LOCAL_LOOKUP_TOOLS


def _generate_config() -> types.GenerateContentConfig:
    """Low temperature for consistent tool use; the model's own thinking by default.

    THINKING_BUDGET=0 turns Gemini 2.5 thinking off (~1 s faster), but in testing the model then
    sometimes answered without calling the tools, so it is opt-in. Set a number to cap it.
    """
    budget = os.getenv("THINKING_BUDGET", "default").strip().lower()
    thinking = None if budget in ("", "default") else types.ThinkingConfig(thinking_budget=int(budget))
    return types.GenerateContentConfig(temperature=0.2, thinking_config=thinking)


def _lookup_tools():
    """MCP Toolbox (managed MCP server) when TOOLBOX_URL is set; local stand-ins otherwise."""
    toolbox_url = os.getenv("TOOLBOX_URL", "").strip()
    if not toolbox_url:
        return list(LOCAL_LOOKUP_TOOLS)
    from google.adk.tools.toolbox_toolset import ToolboxToolset

    return [ToolboxToolset(server_url=toolbox_url, toolset_name=os.getenv("TOOLBOX_TOOLSET", "grant_toolset"))]


root_agent = Agent(
    name="grant_advisor",
    model=os.getenv("GRANT_ADVISOR_MODEL", "gemini-2.5-flash"),
    description="Advises a city grant officer on micro-grant allocation using the corridor's supply network.",
    instruction=INSTRUCTION,
    tools=[*CUSTOM_TOOLS, *_lookup_tools()],
    generate_content_config=_generate_config(),
)
