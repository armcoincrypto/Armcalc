"""History storage service using SQLite."""

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("history_store")


@dataclass
class HistoryEntry:
    """A single history entry."""

    id: int
    user_id: int
    expression: str
    result: str
    timestamp: float
    entry_type: str = "calc"  # calc, convert, price, etc.

    @property
    def formatted_time(self) -> str:
        """Format timestamp for display."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    @property
    def formatted(self) -> str:
        """Format entry for display."""
        return f"{self.expression} = {self.result}"


class HistoryStore:
    """
    SQLite-based history storage.

    Features:
    - Per-user history
    - Configurable entry limit
    - Automatic cleanup of old entries
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        expression TEXT NOT NULL,
        result TEXT NOT NULL,
        timestamp REAL NOT NULL,
        entry_type TEXT DEFAULT 'calc',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    CREATE_INDEX_SQL = """
    CREATE INDEX IF NOT EXISTS idx_history_user_id ON history(user_id);
    CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp DESC);
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the history store."""
        settings = get_settings()
        self._db_path = db_path or settings.history_db_path
        self._limit = settings.history_limit
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database and tables exist."""
        # Ensure directory exists
        path = Path(self._db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript(self.CREATE_TABLE_SQL)
            conn.executescript(self.CREATE_INDEX_SQL)
            conn.commit()
        logger.info(f"History database initialized at {self._db_path}")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def add_entry(
        self,
        user_id: int,
        expression: str,
        result: str,
        entry_type: str = "calc",
    ) -> Optional[int]:
        """
        Add a history entry.

        Args:
            user_id: Telegram user ID
            expression: The expression or command
            result: The result
            entry_type: Type of entry (calc, convert, price, etc.)

        Returns:
            Entry ID or None if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO history (user_id, expression, result, timestamp, entry_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, expression, result, time.time(), entry_type),
                )
                conn.commit()
                entry_id = cursor.lastrowid

                # Cleanup old entries
                self._cleanup_old_entries(conn, user_id)

                return entry_id
        except sqlite3.Error as e:
            logger.error(f"Error adding history entry: {e}")
            return None

    def _cleanup_old_entries(self, conn: sqlite3.Connection, user_id: int) -> None:
        """Remove entries beyond the limit for a user."""
        try:
            # Get count of entries
            cursor = conn.execute(
                "SELECT COUNT(*) as cnt FROM history WHERE user_id = ?",
                (user_id,),
            )
            count = cursor.fetchone()["cnt"]

            if count > self._limit * 2:  # Only cleanup when significantly over limit
                # Delete oldest entries keeping only the limit
                conn.execute(
                    """
                    DELETE FROM history
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM history
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    )
                    """,
                    (user_id, user_id, self._limit),
                )
                conn.commit()
                logger.debug(f"Cleaned up old entries for user {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up history: {e}")

    def get_history(
        self,
        user_id: int,
        limit: Optional[int] = None,
        entry_type: Optional[str] = None,
    ) -> List[HistoryEntry]:
        """
        Get history for a user.

        Args:
            user_id: Telegram user ID
            limit: Max entries to return (default: config limit)
            entry_type: Filter by entry type

        Returns:
            List of HistoryEntry objects (newest first)
        """
        limit = limit or self._limit

        try:
            with self._get_connection() as conn:
                if entry_type:
                    cursor = conn.execute(
                        """
                        SELECT id, user_id, expression, result, timestamp, entry_type
                        FROM history
                        WHERE user_id = ? AND entry_type = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                        """,
                        (user_id, entry_type, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT id, user_id, expression, result, timestamp, entry_type
                        FROM history
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                        """,
                        (user_id, limit),
                    )

                rows = cursor.fetchall()
                return [
                    HistoryEntry(
                        id=row["id"],
                        user_id=row["user_id"],
                        expression=row["expression"],
                        result=row["result"],
                        timestamp=row["timestamp"],
                        entry_type=row["entry_type"] or "calc",
                    )
                    for row in rows
                ]
        except sqlite3.Error as e:
            logger.error(f"Error getting history: {e}")
            return []

    def clear_history(self, user_id: int) -> bool:
        """
        Clear all history for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing history: {e}")
            return False

    def get_stats(self, user_id: int) -> dict:
        """Get statistics for a user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        MIN(timestamp) as first_use,
                        MAX(timestamp) as last_use
                    FROM history
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()

                # Count by type
                cursor = conn.execute(
                    """
                    SELECT entry_type, COUNT(*) as cnt
                    FROM history
                    WHERE user_id = ?
                    GROUP BY entry_type
                    """,
                    (user_id,),
                )
                by_type = {r["entry_type"]: r["cnt"] for r in cursor.fetchall()}

                return {
                    "total": row["total"],
                    "first_use": row["first_use"],
                    "last_use": row["last_use"],
                    "by_type": by_type,
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {"total": 0, "by_type": {}}


# Global store instance
_history_store: Optional[HistoryStore] = None


def get_history_store() -> HistoryStore:
    """Get or create history store instance."""
    global _history_store
    if _history_store is None:
        _history_store = HistoryStore()
    return _history_store
