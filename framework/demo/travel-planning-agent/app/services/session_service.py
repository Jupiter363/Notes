import uuid
from typing import Dict


class SessionService:
    """简单的内存会话管理，存储每次 invoke 后的状态。"""

    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())[:8]
        self._sessions[session_id] = {}
        return session_id

    def get_state(self, session_id: str) -> dict:
        return self._sessions.get(session_id, {})

    def update_state(self, session_id: str, state: dict) -> None:
        self._sessions[session_id] = state

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


session_service = SessionService()
