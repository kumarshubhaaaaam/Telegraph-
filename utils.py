"""
Per-user session management and temp-file bookkeeping.

Each Telegram user gets an independent UserSession, so multiple people can
build articles at the same time without interfering with each other.
"""
import os
import shutil
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from config import TEMP_DIR

os.makedirs(TEMP_DIR, exist_ok=True)


@dataclass
class UserSession:
    user_id: int
    active: bool = False
    processing: bool = False
    images: List[str] = field(default_factory=list)  # ordered local file paths
    order_counter: int = 0
    session_dir: str = ""

    def start(self) -> None:
        """Begin a fresh /newarticle session, wiping any previous state."""
        self.cleanup()
        self.active = True
        self.processing = False
        self.images = []
        self.order_counter = 0
        self.session_dir = os.path.join(TEMP_DIR, f"{self.user_id}_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.session_dir, exist_ok=True)

    def next_path(self, ext: str = "jpg") -> str:
        """Return the next sequential file path, preserving upload order."""
        self.order_counter += 1
        return os.path.join(self.session_dir, f"img_{self.order_counter:04d}.{ext}")

    def cleanup(self) -> None:
        if self.session_dir and os.path.isdir(self.session_dir):
            shutil.rmtree(self.session_dir, ignore_errors=True)

    def reset(self) -> None:
        self.cleanup()
        self.active = False
        self.processing = False
        self.images = []
        self.order_counter = 0
        self.session_dir = ""


class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
        return self._sessions[user_id]

    def clear(self, user_id: int) -> None:
        if user_id in self._sessions:
            self._sessions[user_id].cleanup()
            del self._sessions[user_id]


# Single shared instance used across all handlers
sessions = SessionManager()
