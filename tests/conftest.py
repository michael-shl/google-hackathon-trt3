import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
os.environ["USE_MOCK_DATA"] = "true"
os.environ["TOOLBOX_URL"] = ""


@pytest.fixture(autouse=True)
def _fresh_cache():
    from grant_advisor.tools import data

    data.clear_cache()
    yield
    data.clear_cache()
