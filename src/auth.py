"""Authentication module for SAMUD - handles signup, login, and password management."""

import re
import bcrypt
import asyncio
import logging
from typing import Optional, TYPE_CHECKING

from config import (
    MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH, DEFAULT_ROOM
)
from database import db

if TYPE_CHECKING:
    from server import Client

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication flows for the MUD."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Returns:
            The hashed password as a string.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Validate username format.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty."

        if len(username) < MIN_USERNAME_LENGTH:
            return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters."

        if len(username) > MAX_USERNAME_LENGTH:
            return False, f"Username cannot exceed {MAX_USERNAME_LENGTH} characters."

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores."

        return True, ""

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password format.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password cannot be empty."

        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

        return True, ""

    async def handle_signup(self, client: 'Client', server: 'MudServer') -> bool:
        """
        Handle the signup flow for a new player.

        Returns:
            True if signup successful, False otherwise.
        """
        await client.send("\n=== Create New Account ===\n")

        # Get username
        max_attempts = 3
        for attempt in range(max_attempts):
            await client.send("\nChoose a username: ")
            username = await client.readline()

            if not username:
                await client.send("Signup cancelled.\n")
                return False

            # Validate username
            is_valid, error_msg = self.validate_username(username)
            if not is_valid:
                await client.send(f"Error: {error_msg}\n")
                continue

            # Check if username exists
            existing = await db.get_player_by_username(username)
            if existing:
                await client.send(f"Username '{username}' is already taken. Please choose another.\n")
                continue

            break
        else:
            await client.send("Too many attempts. Signup cancelled.\n")
            return False

        # Get password
        for attempt in range(max_attempts):
            await client.send("Choose a password: ")
            password = await client.readline(echo=False)

            if not password:
                await client.send("Signup cancelled.\n")
                return False

            # Validate password
            is_valid, error_msg = self.validate_password(password)
            if not is_valid:
                await client.send(f"Error: {error_msg}\n")
                continue

            # Confirm password
            await client.send("Confirm password: ")
            confirm = await client.readline(echo=False)

            if password != confirm:
                await client.send("Passwords do not match. Please try again.\n")
                continue

            break
        else:
            await client.send("Too many attempts. Signup cancelled.\n")
            return False

        # Create account
        password_hash = self.hash_password(password)
        player_id = await db.create_player(username, password_hash)

        if not player_id:
            await client.send("Failed to create account. Please try again.\n")
            return False

        # Auto-login
        await client.send(f"\nAccount created successfully! Welcome, {username}!\n")
        await self._complete_login(client, player_id, username, server)

        return True

    async def handle_login(self, client: 'Client', server: 'MudServer') -> bool:
        """
        Handle the login flow for an existing player.

        Returns:
            True if login successful, False otherwise.
        """
        await client.send("\n=== Login ===\n")

        # Get username
        await client.send("Username: ")
        username = await client.readline()

        if not username:
            await client.send("Login cancelled.\n")
            return False

        # Get password
        await client.send("Password: ")
        password = await client.readline(echo=False)

        if not password:
            await client.send("Login cancelled.\n")
            return False

        # Verify credentials
        player = await db.get_player_by_username(username)
        if not player:
            await client.send("Invalid username or password.\n")
            await asyncio.sleep(1)  # Prevent brute force
            return False

        if not self.verify_password(password, player['password_hash']):
            await client.send("Invalid username or password.\n")
            await asyncio.sleep(1)  # Prevent brute force
            return False

        # Check if already logged in
        if player['id'] in server.active_players:
            await client.send("This account is already logged in. Disconnecting other session...\n")
            other_client = server.active_players[player['id']]
            await other_client.send("\n[System] You have been disconnected (logged in from another location).\n")
            other_client.is_active = False
            await asyncio.sleep(1)  # Give time for disconnect

        # Complete login
        await client.send(f"\nWelcome back, {username}!\n")
        await self._complete_login(client, player['id'], username, server)

        return True

    async def _complete_login(self, client: 'Client', player_id: int, username: str, server: 'MudServer'):
        """Complete the login process and place player in game."""
        from player import player_manager
        from world import world

        # Set client state
        client.player_id = player_id
        client.username = username
        client.authenticated = True

        # Add to server's active players (for backwards compatibility)
        server.active_players[player_id] = client

        # Update last login
        await db.update_last_login(player_id)

        # Create session
        ip_address = f"{client.address[0]}:{client.address[1]}" if client.address else None
        await db.create_session(player_id, ip_address)

        # Add player to player manager
        player = await player_manager.add_player(player_id, username, client)

        # Get room info
        room = world.get_room(player.current_room_id)
        if room:
            await client.send(f"\nYou appear at {room.name}.\n")
            if room.ascii_art:
                await client.send(f"{room.ascii_art}\n")
            await client.send(f"{room.description}\n")
            await client.send(f"Exits: {room.get_exit_list()}\n")

            # Show other players in room
            other_players = [p for p in player_manager.get_players_in_room(room.id)
                           if p.id != player_id]
            if other_players:
                names = [p.username for p in other_players]
                await client.send(f"Players here: {', '.join(names)}\n")

        await client.send("\nType 'help' for a list of commands.\n")

        logger.info(f"Player {username} logged in from {client.address}")

    async def handle_welcome_choice(self, client: 'Client', server: 'MudServer', choice: str) -> bool:
        """
        Handle the welcome screen choice (login/signup).

        Returns:
            True if authentication successful, False otherwise.
        """
        choice = choice.lower().strip()

        if choice == 'login':
            return await self.handle_login(client, server)
        elif choice == 'signup':
            return await self.handle_signup(client, server)
        elif choice == 'help':
            help_text = """
Available commands before login:
  login  - Log into an existing account
  signup - Create a new account
  help   - Show this help message
  quit   - Disconnect from the server
"""
            await client.send(help_text)
            return False
        elif choice in ['quit', 'exit']:
            await client.send("Goodbye!\n")
            client.is_active = False
            return False
        else:
            await client.send("Please type 'login' or 'signup' to begin.\n")
            return False


# Global auth manager instance
auth_manager = AuthManager()