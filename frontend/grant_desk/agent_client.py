"""Thin client for the ADK agent's REST API (the same API the ADK Dev UI uses).

The Grant Desk draws its tables and cascade pictures from the agent's own tool responses
(functionResponse events), so every screen is backed by the actual graph traversal.
"""

import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field

import requests

APP_NAME = "grant_advisor"
# Appended to every Grant Desk request: the desk renders tool results itself, so the agent replies
# briefly instead of re-typing tables and the memo (saves seconds of output tokens per click).
DESK_HINT = ("\n\n[Grant Desk request: first call the tool named above; the desk renders its result "
             "on screen. Then reply in at most 3 sentences without repeating tables, paths or the memo.]")
TOKEN_TTL_SECONDS = 45 * 60


@dataclass
class AgentTurn:
    text: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    tool_responses: dict[str, list[dict]] = field(default_factory=dict)

    def latest(self, tool_name: str) -> dict | None:
        responses = self.tool_responses.get(tool_name)
        return responses[-1] if responses else None


def parse_events(events: list[dict]) -> AgentTurn:
    """Collects final text, tool calls and tool responses from /run events."""
    turn = AgentTurn()
    texts = []
    for event in events or []:
        for part in (event.get("content") or {}).get("parts") or []:
            if part.get("functionCall"):
                call = part["functionCall"]
                turn.tool_calls.append({"name": call.get("name"), "args": call.get("args") or {}})
            elif part.get("functionResponse"):
                resp = part["functionResponse"]
                turn.tool_responses.setdefault(resp.get("name"), []).append(resp.get("response") or {})
            elif part.get("text") and not part.get("thought") and event.get("author") != "user":
                texts.append(part["text"])
    turn.text = "\n\n".join(t.strip() for t in texts if t.strip())
    return turn


def _identity_token(audience: str) -> str | None:
    """ID token for a private Cloud Run agent: metadata server on Cloud Run, gcloud locally."""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        return google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audience)
    except Exception:
        pass
    try:
        out = subprocess.run(["gcloud", "auth", "print-identity-token"], capture_output=True, text=True,
                             timeout=20, check=True)
        return out.stdout.strip() or None
    except Exception:
        return None


class AgentClient:
    def __init__(self, base_url: str | None = None, user_id: str = "officer", timeout: int = 180):
        # Local default: `gcloud run services proxy grant-advisor --port 8080` (handles auth).
        self.base_url = (base_url or os.getenv("AGENT_URL", "http://localhost:8080")).rstrip("/")
        self.user_id = user_id
        self.timeout = timeout
        self._needs_token = self.base_url.startswith("https://")
        self._token: str | None = None
        self._token_time = 0.0
        self._http = requests.Session()

    def _headers(self) -> dict:
        headers = {"content-type": "application/json"}
        if self._needs_token:
            if not self._token or time.time() - self._token_time > TOKEN_TTL_SECONDS:
                self._token, self._token_time = _identity_token(self.base_url), time.time()
            if self._token:
                headers["authorization"] = f"Bearer {self._token}"
        return headers

    def new_session(self) -> str:
        session_id = f"desk-{uuid.uuid4().hex[:12]}"
        url = f"{self.base_url}/apps/{APP_NAME}/users/{self.user_id}/sessions/{session_id}"
        self._http.post(url, json={}, headers=self._headers(), timeout=30).raise_for_status()
        return session_id

    def ask(self, session_id: str, message: str, brief: bool = True) -> AgentTurn:
        text = message + (DESK_HINT if brief else "")
        payload = {"app_name": APP_NAME, "user_id": self.user_id, "session_id": session_id,
                   "new_message": {"role": "user", "parts": [{"text": text}]}}
        resp = self._http.post(f"{self.base_url}/run", json=payload, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return parse_events(resp.json())
