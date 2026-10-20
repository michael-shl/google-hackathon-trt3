"""Offline tests on the mock corridor (USE_MOCK_DATA=true). Run: pytest tests -q"""

from grant_advisor.tools import (build_grant_memo, equity_audit, find_business, get_cascade,
                                 get_loan_history, get_neighborhood, list_applicants, rank_applicants)
from grant_advisor.tools.data import _names_from_path_json


def test_cascade_is_multi_hop_and_shows_the_path():
    result = get_cascade("B01")
    assert result["status"] == "success"
    hall = next(r for r in result["exposed"] if r["name"] == "Larkin Event Hall")
    assert hall["hops"] == 2
    assert hall["path_names"] == ["Bayside Roasters", "Kearny Kitchen", "Larkin Event Hall"]
    assert result["counts"] == {"hop1": 5, "hop2": 1, "hop3": 0, "total": 6}
    assert "MODELED" in result["edge_basis"]


def test_one_hop_only_drops_second_hop():
    assert get_cascade("B01", max_hops=1)["counts"]["hop2"] == 0


def test_leaf_has_no_cascade_and_says_so():
    result = get_cascade("B06")
    assert result["status"] == "success"
    assert result["exposed"] == []
    assert "cannot show a cascade" in result["note"]


def test_bad_inputs_return_errors_not_exceptions():
    assert get_cascade("NOPE")["status"] == "error"
    assert get_cascade("B01", max_hops=9)["status"] == "error"
    assert rank_applicants(assumption="wild")["status"] == "error"


def test_ranking_does_not_simply_fund_the_hub():
    result = rank_applicants(budget=50000)
    assert result["status"] == "success"
    by_id = {r["business_id"]: r for r in result["ranking"]}
    assert by_id["B07"]["is_hub"] is True
    assert result["recommendation"]["business_id"] == "B01"
    assert result["recommendation"]["business_id"] != "B07"
    no_discount = next(s for s in result["sensitivity"] if s["variant"] == "no_hub_discount")
    assert no_discount["top_pick"] == "Golden Produce Wholesale"
    assert no_discount["changes_recommendation"] is True


def test_allocation_respects_budget_and_skips_leaves():
    result = rank_applicants(budget=50000)
    funded = sum(r["funded_amount"] for r in result["ranking"])
    assert funded <= 50000
    assert result["unfunded_budget"] == 50000 - funded
    for leaf in ("B06", "B12"):
        row = next(r for r in result["ranking"] if r["business_id"] == leaf)
        assert row["funded_amount"] == 0 and "No downstream supply links" in row["reason"]


def test_assumption_changes_expected_effect_not_order():
    base = rank_applicants(assumption="base")
    pessimistic = rank_applicants(assumption="pessimistic")
    assert [r["business_id"] for r in base["ranking"]] == [r["business_id"] for r in pessimistic["ranking"]]
    assert base["recommendation"]["expected_businesses_spared"] == 2 * pessimistic["recommendation"]["expected_businesses_spared"]


def test_ranking_subset():
    result = rank_applicants(applicant_ids=["B09", "B13"])
    assert {r["business_id"] for r in result["ranking"]} == {"B09", "B13"}


def test_equity_audit_compares_with_corridor():
    result = equity_audit(["B01", "B04", "B09"])
    assert result["status"] == "success"
    assert result["poverty"]["funded_avg"] is not None and result["poverty"]["corridor_avg"] is not None
    by_sector = {r["sector"]: r for r in result["sector_mix"]}
    assert set(by_sector) == {"31-33", "72"}
    assert by_sector["31-33"]["funded_count"] == 2
    assert "Manufacturing (2 funded" in result["finding"]
    assert "Accommodation" not in result["finding"].split("Nothing funded in")[0]
    assert any(r["sector"] == "81" for r in result["unfunded_large_sectors"])
    assert equity_audit([])["status"] == "error"


def test_equity_audit_single_business_per_sector_is_not_flagged():
    result = equity_audit(["B01", "B04", "B13"])
    assert "Over-represented" not in result["finding"]


def test_equity_audit_near_equal_poverty_reads_about_the_same():
    result = equity_audit(["B01", "B04", "B09", "B13"])
    assert "about the same poverty rate" in result["finding"]
    assert "lower poverty" not in result["finding"]


def test_memo_has_all_seven_sections_and_a_picture():
    result = build_grant_memo("B01", 15000, runner_up_id="B04")
    assert result["status"] == "success"
    memo = result["memo_markdown"]
    for heading in ("## 1. Recommendation", "## 2. What it protects", "## 3. The traversal",
                    "## 4. Why this one and not the runner-up", "## 5. What we are assuming",
                    "## 6. Which evidence is modeled", "## 7. Who the neighborhood is"):
        assert heading in memo
    assert "Bayside Roasters → Kearny Kitchen → Larkin Event Hall" in memo
    assert '"Kearny Kitchen" -> "Larkin Event Hall"' in result["cascade_dot"]


def test_local_lookup_tools():
    assert find_business("roast")["matches"][0]["business_id"] == "B01"
    assert len(list_applicants()["applicants"]) == 7
    assert get_neighborhood("B07")["poverty_rate"] == 0.31
    assert get_loan_history("B09")["loans"][0]["charged_off"] is True
    assert get_loan_history("B01")["loans"] == []


def test_path_json_parser_handles_bigquery_shape():
    path = [
        {"identifier": "a", "kind": "node", "labels": ["Business"], "properties": {"name": "Roaster"}},
        {"identifier": "e", "kind": "edge", "labels": ["Supplies"], "properties": {"intensity": 0.1}},
        {"identifier": "b", "kind": "node", "labels": ["Business"], "properties": {"name": "Cafe"}},
    ]
    assert _names_from_path_json(path) == ["Roaster", "Cafe"]
    assert _names_from_path_json('[{"kind": "node", "properties": {"name": "X"}}]') == ["X"]
    assert _names_from_path_json("not json") == []


def test_cascades_for_many_seeds_use_one_batched_query(monkeypatch):
    from grant_advisor.tools import data

    calls = []

    def fake_run(sql, **params):
        calls.append((sql, params))
        return [
            {"seed_id": "A", "business_id": "X", "name": "X", "naics4": "7225", "hops": 1,
             "path_strength": 0.1, "weakest_link": 0.1, "path_json": None},
            {"seed_id": "A", "business_id": "Y", "name": "Y", "naics4": "7225", "hops": 2,
             "path_strength": 0.01, "weakest_link": 0.1, "path_json": None},
        ]

    monkeypatch.setattr(data, "use_mock", lambda: False)
    monkeypatch.setattr(data, "_run", fake_run)
    data.prefetch_cascades(["A", "B"], 2)
    assert len(calls) == 1
    assert "IN UNNEST(@seed_ids)" in calls[0][0] and "{1,2}" in calls[0][0]
    assert calls[0][1] == {"seed_ids": ["A", "B"]}
    assert [r["business_id"] for r in data.cascade_paths("A", 1)] == ["X"]
    assert len(data.cascade_paths("A", 2)) == 2
    assert data.cascade_paths("B", 2) == ()
    assert len(calls) == 1


def test_data_cache_expires_after_ttl(monkeypatch):
    from grant_advisor.tools import data

    calls = []
    monkeypatch.setattr(data, "use_mock", lambda: False)
    monkeypatch.setattr(data, "_run", lambda sql, **p: calls.append(sql) or [
        {"business_id": "X", "name": "X", "address": "a", "naics4": "7225"}])
    monkeypatch.setenv("DATA_CACHE_TTL", "600")
    data.get_businesses_all()
    data.get_businesses_all()
    assert len(calls) == 1
    monkeypatch.setenv("DATA_CACHE_TTL", "0")
    data.get_businesses_all()
    assert len(calls) == 2


def test_every_tool_response_carries_the_data_source(monkeypatch):
    from grant_advisor.tools import CUSTOM_TOOLS, LOCAL_LOOKUP_TOOLS, data

    by_name = {t.__name__: t for t in [*CUSTOM_TOOLS, *LOCAL_LOOKUP_TOOLS]}
    responses = [
        by_name["get_cascade"]("B01"), by_name["get_cascade"]("NOPE"),
        by_name["rank_applicants"](), by_name["equity_audit"](["B01"]),
        by_name["build_grant_memo"]("B01", 15000, "B04"),
        by_name["find_business"]("roast"), by_name["list_applicants"](),
        by_name["get_neighborhood"]("B01"), by_name["get_loan_history"]("B09"),
    ]
    for resp in responses:
        assert resp["data_source"].startswith("MOCK corridor")
    assert "**Data source:** MOCK corridor" in responses[4]["memo_markdown"]

    monkeypatch.setenv("USE_MOCK_DATA", "false")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proj")
    assert data.data_source_label() == "BigQuery proj.a4i_econ · real"


def test_leftover_budget_goes_to_next_best_as_partial_award():
    result = rank_applicants(budget=50000)
    funded = sum(r["funded_amount"] for r in result["ranking"])
    assert funded == 50000 and result["unfunded_budget"] == 0
    partial = result["partial_award"]
    row = next(r for r in result["ranking"] if r["business_id"] == partial["business_id"])
    assert row["partial"] is True and 0 < row["funded_amount"] < row["requested"]
    assert row["reach_total"] > 0
    full = [r for r in result["ranking"] if r["funded_amount"] and not r["partial"]]
    assert all(r["funded_amount"] == r["requested"] for r in full)
    assert row["expected_businesses_spared"] == round(0.10 * partial["share_of_request"] * row["reach_total"], 2)
    assert "PARTIAL award" in row["reason"]


def test_tiny_leftover_stays_unallocated():
    result = rank_applicants(budget=47500)
    assert result["partial_award"] is None
    assert result["unfunded_budget"] == 500
