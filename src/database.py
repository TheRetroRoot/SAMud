"""Database module for SAMUD - async SQLite interface and player data access."""

import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from config import DB_PATH

logger = logging.getLogger(__name__)


class Database:
    """Manages async SQLite database connections and operations."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row  # Return rows as dictionaries
            yield conn

    async def init_database(self):
        """Initialize database schema from schema.sql file."""
        schema_path = Path('schema.sql')
        if not schema_path.exists():
            raise FileNotFoundError("schema.sql not found")

        with open(schema_path, 'r') as f:
            schema = f.read()

        async with self.get_connection() as conn:
            await conn.executescript(schema)
            await conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def create_player(self, username: str, password_hash: str) -> Optional[int]:
        """
        Create a new player account.

        Returns:
            Player ID if successful, None if username already exists.
        """
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    INSERT INTO players (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, password_hash)
                )
                await conn.commit()
                player_id = cursor.lastrowid
                logger.info(f"Created player: {username} (ID: {player_id})")
                return player_id
        except aiosqlite.IntegrityError:
            logger.warning(f"Username already exists: {username}")
            return None

    async def get_player_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve player data by username.

        Returns:
            Player dict if found, None otherwise.
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT id, username, password_hash, current_room_id,
                       created_at, last_login
                FROM players
                WHERE username = ? COLLATE NOCASE
                """,
                (username,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve player data by ID.

        Returns:
            Player dict if found, None otherwise.
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT id, username, password_hash, current_room_id,
                       created_at, last_login
                FROM players
                WHERE id = ?
                """,
                (player_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_player_room(self, player_id: int, room_id: str) -> bool:
        """
        Update player's current room.

        Returns:
            True if successful, False otherwise.
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE players
                SET current_room_id = ?
                WHERE id = ?
                """,
                (room_id, player_id)
            )
            await conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.debug(f"Player {player_id} moved to {room_id}")
            return success

    async def update_last_login(self, player_id: int) -> bool:
        """
        Update player's last login timestamp.

        Returns:
            True if successful, False otherwise.
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE players
                SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (player_id,)
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def get_all_players(self) -> List[Dict[str, Any]]:
        """
        Retrieve all player records.

        Returns:
            List of player dictionaries.
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT id, username, current_room_id, created_at, last_login
                FROM players
                ORDER BY username
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def create_session(self, player_id: int, ip_address: str = None) -> int:
        """
        Create a new session for a player.

        Returns:
            Session ID.
        """
        async with self.get_connection() as conn:
            # First, mark any existing sessions as inactive
            await conn.execute(
                """
                UPDATE sessions
                SET is_active = 0
                WHERE player_id = ? AND is_active = 1
                """,
                (player_id,)
            )

            # Create new session
            cursor = await conn.execute(
                """
                INSERT INTO sessions (player_id, ip_address)
                VALUES (?, ?)
                """,
                (player_id, ip_address)
            )
            await conn.commit()
            return cursor.lastrowid

    async def end_session(self, player_id: int):
        """Mark player's active session as ended."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                UPDATE sessions
                SET is_active = 0
                WHERE player_id = ? AND is_active = 1
                """,
                (player_id,)
            )
            await conn.commit()

    async def is_player_online(self, player_id: int) -> bool:
        """Check if a player has an active session."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as count
                FROM sessions
                WHERE player_id = ? AND is_active = 1
                """,
                (player_id,)
            )
            row = await cursor.fetchone()
            return row['count'] > 0 if row else False


# Global database instance
db = Database()