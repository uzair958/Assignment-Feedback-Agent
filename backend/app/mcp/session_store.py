from threading import Lock
from typing import Any


class MCPChatSessionStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._store.get(session_id, {}))

    def upsert(self, session_id: str, state: dict[str, Any]) -> None:
        with self._lock:
            self._store[session_id] = dict(state)


session_store = MCPChatSessionStore()
