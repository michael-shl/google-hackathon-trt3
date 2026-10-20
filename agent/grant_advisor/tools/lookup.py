"""Local stand-ins for the MCP Toolbox lookup tools (same names as toolbox/tools.yaml).

agent.py registers these ONLY when TOOLBOX_URL is unset, so the agent works offline / on mock data.
In the deployed demo the MCP Toolbox versions are used (that is the required managed MCP server).
"""

from . import data


def _error(exc):
    return {"status": "error", "error_message": str(exc)}


def find_business(name_query: str) -> dict:
    """Find corridor businesses by (partial) name. Returns business_id, name, address and NAICS.

    Args:
        name_query: Part of the business name, e.g. "roasters".
    """
    try:
        needle = name_query.strip().lower()
        matches = [b for b in data.get_businesses_all().values() if needle in str(b["name"]).lower()]
    except data.DataUnavailable as exc:
        return _error(exc)
    return {"status": "success", "matches": matches[:10]}


def list_applicants() -> dict:
    """The grant application queue (simulated applications from real corridor businesses)."""
    try:
        return {"status": "success", "applicants": list(data.applicants())}
    except data.DataUnavailable as exc:
        return _error(exc)


def get_neighborhood(business_id: str) -> dict:
    """Census tract demographics (poverty, no-vehicle, public-assistance rates) for a business.

    Args:
        business_id: The business_id from find_business or list_applicants.
    """
    hood = data.neighborhood(business_id)
    if hood is None:
        return {"status": "error", "error_message": "No neighborhood data for this business (business_need may be missing)."}
    return {"status": "success", "business_id": business_id, **hood}


def get_loan_history(business_id: str) -> dict:
    """REAL SBA 7(a) loan records for a business, including whether a loan was charged off
    (the business failed). An empty list means no SBA record, not "no debt".

    Args:
        business_id: The business_id from find_business or list_applicants.
    """
    try:
        loans = [loan for loan in data.loans_all() if loan["business_id"] == business_id]
    except data.DataUnavailable as exc:
        return _error(exc)
    return {"status": "success", "business_id": business_id, "loans": loans}
