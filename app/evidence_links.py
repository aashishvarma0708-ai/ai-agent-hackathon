import hashlib
import os
import secrets
import sqlite3

from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvidenceLinkError(RuntimeError):
    pass


def _database_path() -> Path:
    configured = os.getenv(
        "EVIDENCE_TOKEN_DB",
        "",
    ).strip()

    if configured:
        path = Path(configured).expanduser()

        if not path.is_absolute():
            path = ROOT / path

        return path

    return ROOT / "runtime" / "evidence_links.db"


def _token_hash(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


class EvidenceLinkStore:
    def __init__(
        self,
        ttl_minutes: int | None = None,
    ):
        if ttl_minutes is None:
            try:
                ttl_minutes = int(
                    os.getenv(
                        "EVIDENCE_LINK_TTL_MINUTES",
                        "30",
                    )
                )
            except ValueError:
                ttl_minutes = 30

        self.ttl_minutes = max(
            5,
            ttl_minutes,
        )

        self.db_path = _database_path()

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._init_db()


    def _connect(self):
        connection = sqlite3.connect(
            self.db_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection


    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_links (
                    token_hash TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT
                )
                """
            )

            conn.commit()


    def issue(
        self,
        complaint_id: str,
    ) -> str:
        complaint_id = (
            complaint_id or ""
        ).strip().upper()

        if not complaint_id:
            raise EvidenceLinkError(
                "Complaint ID is required."
            )

        token = secrets.token_urlsafe(
            32
        )

        now = datetime.now(
            timezone.utc
        )

        expires_at = now + timedelta(
            minutes=self.ttl_minutes
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_links (
                    token_hash,
                    complaint_id,
                    created_at,
                    expires_at,
                    used_at
                )
                VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    _token_hash(token),
                    complaint_id,
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )

            conn.commit()

        return token


    def resolve(
        self,
        token: str,
    ) -> dict:
        token = (
            token or ""
        ).strip()

        if not token:
            raise EvidenceLinkError(
                "Evidence link is invalid."
            )

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM evidence_links
                WHERE token_hash = ?
                """,
                (
                    _token_hash(token),
                ),
            ).fetchone()

        if row is None:
            raise EvidenceLinkError(
                "Evidence link is invalid."
            )

        if row["used_at"]:
            raise EvidenceLinkError(
                "This evidence link has already been used."
            )

        expires_at = datetime.fromisoformat(
            row["expires_at"]
        )

        if datetime.now(timezone.utc) > expires_at:
            raise EvidenceLinkError(
                "This evidence link has expired."
            )

        return {
            "complaint_id":
                row["complaint_id"],
            "created_at":
                row["created_at"],
            "expires_at":
                row["expires_at"],
        }


    def mark_used(
        self,
        token: str,
    ):
        now = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE evidence_links
                SET used_at = ?
                WHERE token_hash = ?
                  AND used_at IS NULL
                """,
                (
                    now,
                    _token_hash(token),
                ),
            )

            conn.commit()


    def revoke(
        self,
        token: str,
    ):
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM evidence_links
                WHERE token_hash = ?
                """,
                (
                    _token_hash(token),
                ),
            )

            conn.commit()
