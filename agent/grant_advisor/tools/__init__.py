from .audit import equity_audit
from .cascade import get_cascade
from .lookup import find_business, get_loan_history, get_neighborhood, list_applicants
from .memo import build_grant_memo
from .scoring import rank_applicants

CUSTOM_TOOLS = [get_cascade, rank_applicants, equity_audit, build_grant_memo]
LOCAL_LOOKUP_TOOLS = [find_business, list_applicants, get_neighborhood, get_loan_history]
