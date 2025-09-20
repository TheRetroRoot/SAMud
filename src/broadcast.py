"""Broadcast module for SAMUD - handles message distribution to players."""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime

from config import ROOM_MESSAGE_FORMAT, GLOBAL_MESSAGE_FORMAT, SYSTEM_MESSAGE_FORMAT

logger = logging.getLogger(__name__)


class BroadcastManager:
    """Manages message broadcasting to players."""

    def __init__(self):
        self.message_queue: List[tuple] = []
        self.processing = False

    async def broadcast_to_room(self, room_id: str, message: str,
                               exclude_player_id: Optional[int] = None,
                               is_system: bool = True):
        """
        Send a message to all players in a room.

        Args:
            room_id: The room to broadcast to
            message: The message to send
            exclude_player_id: Player ID to exclude from broadcast
            is_system: Whether this is a system message
        """
        from player import player_manager
        from world import world

        room = world.get_room(room_id)
        if not room:
            logger.warning(f"Attempted to broadcast to non-existent room: {room_id}")
            return

        # Format message if it's a system message
        if is_system:
            formatted_message = f"[System] {message}"
        else:
            formatted_message = message

        # Get players in room
        players = player_manager.get_players_in_room(room_id)

        # Send to each player
        tasks = []
        for player in players:
            if player.id != exclude_player_id:
                tasks.append(self._send_to_player(player, formatted_message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Broadcasted to {len(tasks)} players in {room_id}: {message[:50]}")

    async def broadcast_to_all(self, message: str,
                              exclude_player_id: Optional[int] = None):
        """
        Send a message to all online players.

        Args:
            message: The message to send
            exclude_player_id: Player ID to exclude from broadcast
        """
        from player import player_manager

        players = player_manager.get_online_players()

        tasks = []
        for player in players:
            if player.id != exclude_player_id:
                tasks.append(self._send_to_player(player, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Global broadcast to {len(tasks)} players: {message[:50]}")

    async def broadcast_room_message(self, room_id: str, username: str,
                                    message: str):
        """
        Broadcast a player's message to their room.

        Args:
            room_id: The room to broadcast to
            username: The speaking player's username
            message: The message they said
        """
        formatted = ROOM_MESSAGE_FORMAT.format(
            username=username,
            message=message
        )
        await self.broadcast_to_room(room_id, formatted, exclude_player_id=None,
                                    is_system=False)

    async def broadcast_global_message(self, username: str, message: str,
                                      sender_id: Optional[int] = None):
        """
        Broadcast a player's message globally.

        Args:
            username: The shouting player's username
            message: The message they shouted
            sender_id: The sender's player ID (to include them in broadcast)
        """
        formatted = GLOBAL_MESSAGE_FORMAT.format(
            username=username,
            message=message
        )
        # Don't exclude sender for global messages - they should see their own shout
        await self.broadcast_to_all(formatted, exclude_player_id=None)

    async def _send_to_player(self, player, message: str):
        """Send a message to a specific player."""
        try:
            if player.client and player.client.is_active:
                await player.client.send(f"\n{message}")
        except Exception as e:
            logger.error(f"Failed to send to player {player.username}: {e}")

    async def announce_player_connection(self, username: str, connected: bool = True):
        """
        Announce when a player connects or disconnects.

        Args:
            username: The player's username
            connected: True for connection, False for disconnection
        """
        if connected:
            message = f"[System] {username} has joined the game."
        else:
            message = f"[System] {username} has left the game."

        await self.broadcast_to_all(message)
        logger.info(message)

    async def send_to_player_by_id(self, player_id: int, message: str):
        """Send a message directly to a specific player by ID."""
        from player import player_manager

        player = player_manager.get_player(player_id)
        if player:
            await self._send_to_player(player, message)

    async def send_to_player_by_username(self, username: str, message: str):
        """Send a message directly to a specific player by username."""
        from player import player_manager

        player = player_manager.get_player_by_username(username)
        if player:
            await self._send_to_player(player, message)


# Global broadcast manager instance
broadcast_manager = BroadcastManager()


# Convenience functions for module-level access
async def broadcast_to_room(room_id: str, message: str,
                           exclude_player_id: Optional[int] = None,
                           is_system: bool = True):
    """Convenience function for room broadcasting."""
    await broadcast_manager.broadcast_to_room(room_id, message,
                                             exclude_player_id, is_system)


async def broadcast_to_all(message: str, exclude_player_id: Optional[int] = None):
    """Convenience function for global broadcasting."""
    await broadcast_manager.broadcast_to_all(message, exclude_player_id)


async def broadcast_room_message(room_id: str, username: str, message: str):
    """Convenience function for room messages."""
    await broadcast_manager.broadcast_room_message(room_id, username, message)


async def broadcast_global_message(username: str, message: str,
                                  sender_id: Optional[int] = None):
    """Convenience function for global messages."""
    await broadcast_manager.broadcast_global_message(username, message, sender_id)