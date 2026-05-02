from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_SESSION_STATE: Dict[str, Any] = {
    "messages": [],
    "intent": {},
    "references": [],
    "retrievals": [],
    "generation": {},
}


class TeacherSessionStore:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def create_session(self, user_id: int) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir.parent / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        exports_dir = session_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        session = {
            "session_id": session_id,
            "user_id": user_id,
            **DEFAULT_SESSION_STATE,
            "files_dir": str(session_dir),
            "exports_dir": str(exports_dir),
        }
        self._session_path(session_id).write_text(
            json.dumps(session, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return session

    def get_session(self, session_id: str) -> Dict[str, Any]:
        path = self._session_path(session_id)
        if not path.exists():
            raise KeyError(f"Session not found: {session_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def update_session(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_session(session_id)
        for key, value in payload.items():
            if isinstance(current.get(key), dict) and isinstance(value, dict):
                merged = dict(current[key])
                merged.update(value)
                current[key] = merged
            else:
                current[key] = value
        self._session_path(session_id).write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return current

    def append_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        current = self.get_session(session_id)
        messages = list(current.get("messages", []))
        messages.append({"role": role, "content": content})
        current["messages"] = messages
        self._session_path(session_id).write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return current


_STORE: Optional[TeacherSessionStore] = None


def get_teacher_session_store(base_dir: Optional[Path] = None) -> TeacherSessionStore:
    global _STORE
    if base_dir is not None:
        return TeacherSessionStore(base_dir)
    if _STORE is None:
        teacher_root = Path(__file__).resolve().parents[2]
        _STORE = TeacherSessionStore(teacher_root / "uploads" / "sessions")
    return _STORE
