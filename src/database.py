"""Database module for SAMUD - async SQLite interface and player data access."""

import aiosqlite
import json
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

    # === NPC Database Methods ===

    async def save_npc_state(self, npc_id: str, current_room: str,
                            last_moved: datetime, state_data: Dict[str, Any]):
        """Save or update NPC state.

        Args:
            npc_id: NPC identifier
            current_room: Current room ID
            last_moved: Last movement timestamp
            state_data: Additional state data
        """
        async with self.get_connection() as conn:
            state_json = json.dumps(state_data) if state_data else None

            await conn.execute("""
                INSERT INTO npc_state (npc_id, current_room, last_moved, state_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(npc_id) DO UPDATE SET
                    current_room = excluded.current_room,
                    last_moved = excluded.last_moved,
                    state_data = excluded.state_data
            """, (npc_id, current_room, last_moved, state_json))

            await conn.commit()
            logger.debug(f"Saved state for NPC {npc_id}")

    async def load_npc_state(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Load NPC state from database.

        Args:
            npc_id: NPC to load

        Returns:
            Dictionary with NPC state or None if not found
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT current_room, last_moved, state_data FROM npc_state WHERE npc_id = ?",
                (npc_id,)
            )
            row = await cursor.fetchone()

            if row:
                return {
                    'current_room': row['current_room'],
                    'last_moved': row['last_moved'],
                    'state_data': json.loads(row['state_data']) if row['state_data'] else {}
                }
            return None

    async def save_npc_memory(self, npc_id: str, player_name: str,
                              interaction_count: int, memory_data: Dict[str, Any]):
        """Save or update NPC memory of a player.

        Args:
            npc_id: NPC identifier
            player_name: Player being remembered
            interaction_count: Number of interactions
            memory_data: Memory details
        """
        async with self.get_connection() as conn:
            memory_json = json.dumps(memory_data) if memory_data else None

            await conn.execute("""
                INSERT INTO npc_memory (npc_id, player_name, last_interaction,
                                      interaction_count, memory_data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(npc_id, player_name) DO UPDATE SET
                    last_interaction = excluded.last_interaction,
                    interaction_count = excluded.interaction_count,
                    memory_data = excluded.memory_data
            """, (
                npc_id, player_name, datetime.now(),
                interaction_count, memory_json
            ))

            await conn.commit()

    async def load_npc_memories(self, npc_id: str) -> List[Dict[str, Any]]:
        """Load all memories for an NPC.

        Args:
            npc_id: NPC to load memories for

        Returns:
            List of memory records
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT player_name, last_interaction, interaction_count, memory_data
                FROM npc_memory
                WHERE npc_id = ?
                ORDER BY last_interaction DESC
            """, (npc_id,))

            rows = await cursor.fetchall()
            memories = []

            for row in rows:
                memories.append({
                    'player_name': row['player_name'],
                    'last_interaction': row['last_interaction'],
                    'interaction_count': row['interaction_count'],
                    'memory_data': json.loads(row['memory_data']) if row['memory_data'] else {}
                })

            return memories

    async def prune_old_npc_memories(self, days: int = 30):
        """Remove NPC memories older than specified days.

        Args:
            days: Age threshold in days
        """
        async with self.get_connection() as conn:
            cutoff_date = datetime.now().replace(
                day=datetime.now().day - days if datetime.now().day > days else 1
            )

            await conn.execute("""
                DELETE FROM npc_memory
                WHERE last_interaction < ?
            """, (cutoff_date,))

            await conn.commit()
            logger.info(f"Pruned NPC memories older than {days} days")

    async def get_all_npc_states(self) -> List[Dict[str, Any]]:
        """Get all NPC states from database.

        Returns:
            List of NPC state dictionaries
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT npc_id, current_room, last_moved, state_data FROM npc_state"
            )
            rows = await cursor.fetchall()

            states = []
            for row in rows:
                states.append({
                    'npc_id': row['npc_id'],
                    'current_room': row['current_room'],
                    'last_moved': row['last_moved'],
                    'state_data': json.loads(row['state_data']) if row['state_data'] else {}
                })

            return states


# Global database instance
db = Database()