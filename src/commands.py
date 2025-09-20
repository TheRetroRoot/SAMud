"""Commands module for SAMUD - handles command parsing and execution."""

import logging
import re
from typing import Dict, Callable, Optional, List, TYPE_CHECKING
from dataclasses import dataclass

from config import COMMANDS, MOVEMENT_SHORTCUTS, MAX_MESSAGE_LENGTH
from world import world
from player import player_manager
from broadcast import broadcast_room_message, broadcast_global_message
from database import db

if TYPE_CHECKING:
    from server import Client

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Represents a command that can be executed."""
    name: str
    handler: Callable
    description: str
    requires_auth: bool = True
    usage: Optional[str] = None


class CommandProcessor:
    """Processes and executes player commands."""

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self._register_commands()

    def _register_commands(self):
        """Register all available commands."""
        # Navigation commands
        self.register("look", self.cmd_look, "Show room description, exits, and players")
        self.register("move", self.cmd_move, "Move in a direction", usage="move <direction>")
        self.register("n", self.cmd_north, "Move north")
        self.register("north", self.cmd_north, "Move north")
        self.register("s", self.cmd_south, "Move south")
        self.register("south", self.cmd_south, "Move south")
        self.register("e", self.cmd_east, "Move east")
        self.register("east", self.cmd_east, "Move east")
        self.register("w", self.cmd_west, "Move west")
        self.register("west", self.cmd_west, "Move west")
        self.register("where", self.cmd_where, "Show your current location")

        # Communication commands
        self.register("say", self.cmd_say, "Say something to everyone in the room",
                      usage="say <message>")
        self.register("shout", self.cmd_shout, "Shout a message to all players",
                      usage="shout <message>")

        # System commands
        self.register("who", self.cmd_who, "Show all online players")
        self.register("help", self.cmd_help, "Show available commands")
        self.register("quit", self.cmd_quit, "Save and disconnect")
        self.register("exit", self.cmd_quit, "Save and disconnect")

    def register(self, name: str, handler: Callable, description: str,
                 usage: Optional[str] = None, requires_auth: bool = True):
        """Register a new command."""
        self.commands[name.lower()] = Command(
            name=name,
            handler=handler,
            description=description,
            requires_auth=requires_auth,
            usage=usage
        )

    async def process_command(self, client: 'Client', input_text: str) -> bool:
        """
        Process a command from a client.

        Returns:
            True if command was processed, False if not found
        """
        if not input_text:
            return False

        # Parse command and arguments
        parts = input_text.strip().split(maxsplit=1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Find command
        command = self.commands.get(command_name)
        if not command:
            # Try to find similar commands for suggestion
            similar = self._find_similar_commands(command_name)
            if similar:
                await client.send(f"Unknown command '{command_name}'. Did you mean '{similar[0]}'?\n")
            else:
                await client.send(f"Unknown command '{command_name}'. Type 'help' for available commands.\n")
            return False

        # Check authentication requirement
        if command.requires_auth and not client.authenticated:
            await client.send("You must be logged in to use that command.\n")
            return False

        # Update player activity
        if client.player_id:
            player = player_manager.get_player(client.player_id)
            if player:
                player.update_activity()

        # Execute command
        try:
            await command.handler(client, args)
            return True
        except Exception as e:
            logger.error(f"Error executing command {command_name}: {e}")
            await client.send("An error occurred while processing your command.\n")
            return False

    def _find_similar_commands(self, command_name: str) -> List[str]:
        """Find commands similar to the given name."""
        similar = []
        for cmd in self.commands.keys():
            # Check if command starts with the given text
            if cmd.startswith(command_name):
                similar.append(cmd)
            # Check Levenshtein distance for typos (simple version)
            elif len(cmd) > 3 and len(command_name) > 3:
                if abs(len(cmd) - len(command_name)) <= 2:
                    matches = sum(1 for a, b in zip(cmd, command_name) if a == b)
                    if matches >= len(command_name) - 2:
                        similar.append(cmd)
        return similar[:3]  # Return top 3 suggestions

    # === Navigation Commands ===

    async def cmd_look(self, client: 'Client', args: str):
        """Look at the current room."""
        player = player_manager.get_player(client.player_id)
        if not player:
            await client.send("You are not properly logged in.\n")
            return

        room = world.get_room(player.current_room_id)
        if not room:
            await client.send("You are in a void. Something went wrong!\n")
            return

        # Send room information with ASCII art
        await client.send(f"\n{room.name}\n")
        if room.ascii_art:
            await client.send(f"{room.ascii_art}\n")
        await client.send(f"{room.description}\n")
        await client.send(f"Exits: {room.get_exit_list()}\n")

        # Show other players in room
        players = player_manager.get_players_in_room(room.id)
        other_players = [p for p in players if p.id != player.id]
        if other_players:
            names = [p.username for p in other_players]
            await client.send(f"Players here: {', '.join(names)}\n")
        else:
            await client.send("You are alone here.\n")

    async def cmd_move(self, client: 'Client', args: str):
        """Move in a specified direction."""
        if not args:
            await client.send("Move where? Usage: move <direction>\n")
            return

        direction = args.lower().strip()
        await self._move_player(client, direction)

    async def cmd_north(self, client: 'Client', args: str):
        """Move north."""
        await self._move_player(client, "north")

    async def cmd_south(self, client: 'Client', args: str):
        """Move south."""
        await self._move_player(client, "south")

    async def cmd_east(self, client: 'Client', args: str):
        """Move east."""
        await self._move_player(client, "east")

    async def cmd_west(self, client: 'Client', args: str):
        """Move west."""
        await self._move_player(client, "west")

    async def _move_player(self, client: 'Client', direction: str):
        """Handle player movement in a direction."""
        player = player_manager.get_player(client.player_id)
        if not player:
            await client.send("You are not properly logged in.\n")
            return

        # Expand shortcuts
        if direction in MOVEMENT_SHORTCUTS:
            direction = MOVEMENT_SHORTCUTS[direction]

        # Get current room
        room = world.get_room(player.current_room_id)
        if not room:
            await client.send("You cannot move from here.\n")
            return

        # Check if exit exists
        if direction not in room.exits:
            await client.send(f"You can't go {direction}. Available exits: {room.get_exit_list()}\n")
            return

        # Get destination room
        dest_room_id = room.exits[direction]
        dest_room = world.get_room(dest_room_id)
        if not dest_room:
            await client.send("That direction leads nowhere.\n")
            return

        # Move player
        await player.move_to_room(dest_room_id, direction)

        # Show new room with ASCII art
        await client.send(f"\n{dest_room.name}\n")
        if dest_room.ascii_art:
            await client.send(f"{dest_room.ascii_art}\n")
        await client.send(f"{dest_room.description}\n")
        await client.send(f"Exits: {dest_room.get_exit_list()}\n")

        # Show other players
        players = player_manager.get_players_in_room(dest_room_id)
        other_players = [p for p in players if p.id != player.id]
        if other_players:
            names = [p.username for p in other_players]
            await client.send(f"Players here: {', '.join(names)}\n")

    async def cmd_where(self, client: 'Client', args: str):
        """Show current location."""
        player = player_manager.get_player(client.player_id)
        if not player:
            await client.send("You are not properly logged in.\n")
            return

        room = world.get_room(player.current_room_id)
        if room:
            await client.send(f"You are at: {room.name}\n")
        else:
            await client.send("Your location is unknown.\n")

    # === Communication Commands ===

    async def cmd_say(self, client: 'Client', args: str):
        """Say something to the room."""
        if not args:
            await client.send("Say what? Usage: say <message>\n")
            return

        player = player_manager.get_player(client.player_id)
        if not player:
            await client.send("You are not properly logged in.\n")
            return

        # Check rate limit
        if not player.check_rate_limit():
            await client.send("You are speaking too quickly. Please slow down.\n")
            return

        # Truncate message if too long
        message = args[:MAX_MESSAGE_LENGTH]
        if len(args) > MAX_MESSAGE_LENGTH:
            message += "..."

        # Send to room
        await broadcast_room_message(player.current_room_id, player.username, message)

    async def cmd_shout(self, client: 'Client', args: str):
        """Shout to all players."""
        if not args:
            await client.send("Shout what? Usage: shout <message>\n")
            return

        player = player_manager.get_player(client.player_id)
        if not player:
            await client.send("You are not properly logged in.\n")
            return

        # Check rate limit
        if not player.check_rate_limit():
            await client.send("You are shouting too quickly. Please slow down.\n")
            return

        # Truncate message if too long
        message = args[:MAX_MESSAGE_LENGTH]
        if len(args) > MAX_MESSAGE_LENGTH:
            message += "..."

        # Send globally
        await broadcast_global_message(player.username, message, player.id)

    # === System Commands ===

    async def cmd_who(self, client: 'Client', args: str):
        """List all online players."""
        players = player_manager.get_online_players()

        if not players:
            await client.send("No players online.\n")
            return

        await client.send(f"\n=== Online Players ({len(players)}) ===\n")
        for player in sorted(players, key=lambda p: p.username.lower()):
            room = world.get_room(player.current_room_id)
            room_name = room.name if room else "Unknown"
            await client.send(f"  {player.username:<20} - {room_name}\n")

    async def cmd_help(self, client: 'Client', args: str):
        """Show help for commands."""
        if args:
            # Show help for specific command
            cmd_name = args.lower().strip()
            command = self.commands.get(cmd_name)
            if command:
                await client.send(f"\n{command.name.upper()}: {command.description}\n")
                if command.usage:
                    await client.send(f"Usage: {command.usage}\n")
            else:
                await client.send(f"No help available for '{cmd_name}'.\n")
        else:
            # Show all commands
            await client.send("\n=== Available Commands ===\n")

            # Group commands by category
            navigation = ["look", "move", "n", "s", "e", "w", "where"]
            communication = ["say", "shout"]
            system = ["who", "help", "quit"]

            await client.send("\nNavigation:\n")
            for cmd_name in navigation:
                if cmd_name in self.commands:
                    cmd = self.commands[cmd_name]
                    await client.send(f"  {cmd.name:10} - {cmd.description}\n")

            await client.send("\nCommunication:\n")
            for cmd_name in communication:
                if cmd_name in self.commands:
                    cmd = self.commands[cmd_name]
                    await client.send(f"  {cmd.name:10} - {cmd.description}\n")

            await client.send("\nSystem:\n")
            for cmd_name in system:
                if cmd_name in self.commands:
                    cmd = self.commands[cmd_name]
                    await client.send(f"  {cmd.name:10} - {cmd.description}\n")

            await client.send("\nType 'help <command>' for more information about a specific command.\n")

    async def cmd_quit(self, client: 'Client', args: str):
        """Save and quit the game."""
        player = player_manager.get_player(client.player_id)

        await client.send("Saving your progress...\n")

        # Save player state
        if player:
            await db.update_player_room(player.id, player.current_room_id)
            await player_manager.remove_player(player.id)

        await client.send("Goodbye! Come back soon!\n")
        client.is_active = False


# Global command processor instance
command_processor = CommandProcessor()