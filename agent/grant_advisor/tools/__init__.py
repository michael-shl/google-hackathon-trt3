from functools import wraps

from . import data
from .audit import equity_audit
from .cascade import get_cascade
from .lookup import find_business, get_loan_history, get_neighborhood, list_applicants
from .memo import build_grant_memo
from .scoring import rank_applicants


def labeled(tool):
    """Adds 'data_source' (real BigQuery vs MOCK corridor) to every tool response.

    functools.wraps keeps the name, docstring and signature ADK uses for the function declaration.
    """

    @wraps(tool)
    def wrapper(*args, **kwargs):
        result = tool(*args, **kwargs)
        if isinstance(result, dict):
            result["data_source"] = data.data_source_label()
        return result

    return wrapper


CUSTOM_TOOLS = [labeled(t) for t in (get_cascade, rank_applicants, equity_audit, build_grant_memo)]
LOCAL_LOOKUP_TOOLS = [labeled(t) for t in (find_business, list_applicants, get_neighborhood, get_loan_history)]
