"""Gateway settings.

Read from the environment (names match .env.example) but injectable via
``create_app(settings=...)`` so tests never touch ``os.environ``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    auth_service_url: str
    orchestrator_url: str
    content_service_url: str
    jwt_secret: str
    jwt_algorithm: str
    frontend_origin: str
    student_profile_service_url: str = "http://student_profile_service:9008"
    chat_rate_limit: int = 20
    chat_rate_window_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            auth_service_url=os.environ.get("AUTH_SERVICE_URL", "http://auth_service:9002").rstrip("/"),
            orchestrator_url=os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:9001").rstrip("/"),
            content_service_url=os.environ.get("CONTENT_SERVICE_URL", "http://content_service:9003").rstrip("/"),
            student_profile_service_url=(
                os.environ.get("STUDENT_PROFILE_SERVICE_URL")
                or os.environ.get("PROFILE_SERVICE_URL")
                or "http://student_profile_service:9008"
            ).rstrip("/"),
            jwt_secret=os.environ.get("JWT_SECRET", ""),
            jwt_algorithm=os.environ.get("JWT_ALGORITHM", "HS256").strip() or "HS256",
            frontend_origin=os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000"),
        )
