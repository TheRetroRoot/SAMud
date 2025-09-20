"""Player module for SAMUD - manages player state and session handling."""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, TYPE_CHECKING

from config import MESSAGE_RATE_LIMIT, MESSAGE_RATE_WINDOW
from database import db
from world import world

if TYPE_CHECKING:
    from server import Client, MudServer

logger = logging.getLogger(__name__)


class Player:
    """Represents a player in the game world."""

    def __init__(self, player_id: int, username: str, client: 'Client'):
        self.id = player_id
        self.username = username
        self.client = client
        self.current_room_id = world.starting_room
        self.last_activity = datetime.now()

        # Rate limiting for messages
        self.message_times: List[datetime] = []

        logger.info(f"Player {username} (ID: {player_id}) initialized")

    async def move_to_room(self, room_id: str, from_direction: Optional[str] = None):
        """Move player to a new room and handle notifications."""
        old_room_id = self.current_room_id

        # Update world state
        world.move_player(self.id, old_room_id, room_id)

        # Update player state
        self.current_room_id = room_id
        self.client.current_room = room_id

        # Save to database
        await db.update_player_room(self.id, room_id)

        # Get direction for movement messages
        if from_direction:
            # Player came from a direction (opposite of where they went)
            arrival_direction = world.get_opposite_direction(from_direction)
        else:
            # Determine direction based on room connections
            arrival_direction = world.get_direction_from_rooms(room_id, old_room_id)

        # Notify players in old room (if it wasn't login)
        if old_room_id and old_room_id != room_id:
            await self._notify_room_exit(old_room_id, from_direction)

        # Notify players in new room
        await self._notify_room_entry(room_id, arrival_direction)

        logger.debug(f"Player {self.username} moved from {old_room_id} to {room_id}")

    async def _notify_room_exit(self, room_id: str, direction: Optional[str]):
        """Notify players in a room that someone left."""
        from broadcast import broadcast_to_room

        if direction:
            message = f"{self.username} heads {direction}."
        else:
            message = f"{self.username} has left."

        await broadcast_to_room(room_id, message, exclude_player_id=self.id)

    async def _notify_room_entry(self, room_id: str, from_direction: Optional[str]):
        """Notify players in a room that someone arrived."""
        from broadcast import broadcast_to_room

        if from_direction:
            message = f"{self.username} arrives from the {from_direction}."
        else:
            message = f"{self.username} has arrived."

        await broadcast_to_room(room_id, message, exclude_player_id=self.id)

    def check_rate_limit(self) -> bool:
        """
        Check if player is within message rate limits.

        Returns:
            True if within limits, False if rate limited.
        """
        now = datetime.now()

        # Remove old timestamps outside the window
        self.message_times = [
            t for t in self.message_times
            if (now - t).total_seconds() < MESSAGE_RATE_WINDOW
        ]

        # Check if at limit
        if len(self.message_times) >= MESSAGE_RATE_LIMIT:
            return False

        # Add current timestamp
        self.message_times.append(now)
        return True

    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()
        self.client.last_activity = self.last_activity


class PlayerManager:
    """Manages all active players in the game."""

    def __init__(self):
        self.active_players: Dict[int, Player] = {}

    async def add_player(self, player_id: int, username: str, client: 'Client',
                         room_id: Optional[str] = None) -> Player:
        """Add a new player to the game."""
        player = Player(player_id, username, client)

        # Set initial room
        if room_id:
            player.current_room_id = room_id
        else:
            # Load from database or use default
            player_data = await db.get_player_by_id(player_id)
            if player_data and player_data.get('current_room_id'):
                player.current_room_id = player_data['current_room_id']

        # Add to active players
        self.active_players[player_id] = player

        # Add to room
        room = world.get_room(player.current_room_id)
        if room:
            room.add_player(player_id)

        logger.info(f"Player {username} added to game in {player.current_room_id}")
        return player

    async def remove_player(self, player_id: int):
        """Remove a player from the game."""
        player = self.active_players.get(player_id)
        if not player:
            return

        # Remove from room
        room = world.get_room(player.current_room_id)
        if room:
            room.remove_player(player_id)

        # Notify other players
        from broadcast import broadcast_to_room
        await broadcast_to_room(
            player.current_room_id,
            f"{player.username} has disconnected.",
            exclude_player_id=player_id
        )

        # Remove from active players
        del self.active_players[player_id]

        # End database session
        await db.end_session(player_id)

        logger.info(f"Player {player.username} removed from game")

    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        return self.active_players.get(player_id)

    def get_player_by_username(self, username: str) -> Optional[Player]:
        """Get a player by username."""
        for player in self.active_players.values():
            if player.username.lower() == username.lower():
                return player
        return None

    def get_players_in_room(self, room_id: str) -> List[Player]:
        """Get all players in a specific room."""
        room = world.get_room(room_id)
        if not room:
            return []

        players = []
        for player_id in room.players:
            player = self.get_player(player_id)
            if player:
                players.append(player)
        return players

    def get_online_players(self) -> List[Player]:
        """Get all online players."""
        return list(self.active_players.values())

    def get_online_count(self) -> int:
        """Get the count of online players."""
        return len(self.active_players)

    async def save_all_players(self):
        """Save all player states to database."""
        for player in self.active_players.values():
            await db.update_player_room(player.id, player.current_room_id)
        logger.info(f"Saved {len(self.active_players)} player states")

    async def broadcast_to_all(self, message: str, exclude_player_id: Optional[int] = None):
        """Send a message to all online players."""
        for player in self.active_players.values():
            if player.id != exclude_player_id:
                await player.client.send(message)

    async def check_idle_players(self):
        """Check for idle players and send warnings or disconnect."""
        from config import IDLE_TIMEOUT, IDLE_WARNING_TIME

        current_time = datetime.now()

        for player in list(self.active_players.values()):
            idle_seconds = (current_time - player.last_activity).total_seconds()

            if idle_seconds > IDLE_TIMEOUT:
                # Disconnect idle player
                await player.client.send("\n[System] You have been disconnected due to inactivity.\n")
                player.client.is_active = False
                logger.info(f"Player {player.username} disconnected for inactivity")

            elif idle_seconds > IDLE_WARNING_TIME:
                # Send warning (only once)
                if not hasattr(player, '_idle_warned'):
                    await player.client.send(
                        "\n[System] You will be disconnected in 5 minutes due to inactivity.\n"
                    )
                    player._idle_warned = True


# Global player manager instance
player_manager = PlayerManager()