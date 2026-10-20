"""Grant Desk helpers: event parsing and the views built from tool responses."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend" / "grant_desk"))

from agent_client import parse_events  # noqa: E402
from desk_views import cascade_dot, path_rows, ranking_rows  # noqa: E402

from grant_advisor.tools import get_cascade, rank_applicants  # noqa: E402


def test_parse_events_collects_text_calls_and_responses():
    events = [
        {"author": "grant_advisor", "content": {"parts": [{"functionCall": {"name": "get_cascade", "args": {"business_id": "B01"}}}]}},
        {"author": "grant_advisor", "content": {"parts": [{"functionResponse": {"name": "get_cascade", "response": {"status": "success", "x": 1}}}]}},
        {"author": "grant_advisor", "content": {"parts": [{"text": "thinking", "thought": True}, {"text": "Answer."}]}},
    ]
    turn = parse_events(events)
    assert turn.tool_calls == [{"name": "get_cascade", "args": {"business_id": "B01"}}]
    assert turn.latest("get_cascade") == {"status": "success", "x": 1}
    assert turn.latest("rank_applicants") is None
    assert turn.text == "Answer."


def test_cascade_dot_from_real_tool_response():
    dot = cascade_dot(get_cascade("B01"))
    assert '"Bayside Roasters" [fillcolor="#90caf9"]' in dot
    assert '"Kearny Kitchen" -> "Larkin Event Hall";' in dot
    assert '"Larkin Event Hall" [fillcolor="#fff59d"]' in dot


def test_cascade_dot_escapes_quotes():
    cascade = {"seed": {"name": 'Joe\'s "Best" Deli'}, "exposed": [{"name": "Cafe", "path_names": ['Joe\'s "Best" Deli', "Cafe"]}]}
    assert '"Joe\'s \'Best\' Deli" -> "Cafe";' in cascade_dot(cascade)


def test_ranking_rows_mark_recommendation_and_runner_up():
    rows = ranking_rows(rank_applicants(budget=50000))
    badges = {r["Business"]: r[""] for r in rows}
    assert badges["Bayside Roasters"] == "★ pick"
    assert list(badges.values()).count("runner-up") == 1
    assert next(r for r in rows if r["Business"] == "Golden Produce Wholesale")["Hub"] == "yes"


def test_path_rows():
    rows = path_rows(get_cascade("B01"))
    assert any(r["Path"] == "Bayside Roasters → Kearny Kitchen → Larkin Event Hall" for r in rows)
