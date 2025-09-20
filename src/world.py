"""World module for SAMUD - defines rooms and the game world structure."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Room:
    """Represents a location in the game world."""

    id: str
    name: str
    description: str
    ascii_art: str = ""  # ASCII art for the room
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    players: Set[int] = field(default_factory=set)  # Set of player IDs in room
    npcs: Set[str] = field(default_factory=set)  # Set of NPC IDs in room

    def get_exit_list(self) -> str:
        """Get formatted string of available exits."""
        if not self.exits:
            return "none"
        return ", ".join(self.exits.keys())

    def add_player(self, player_id: int):
        """Add a player to this room."""
        self.players.add(player_id)
        logger.debug(f"Player {player_id} entered {self.name}")

    def remove_player(self, player_id: int):
        """Remove a player from this room."""
        self.players.discard(player_id)
        logger.debug(f"Player {player_id} left {self.name}")

    def get_player_count(self) -> int:
        """Get the number of players in this room."""
        return len(self.players)

    def add_npc(self, npc_id: str):
        """Add an NPC to this room."""
        self.npcs.add(npc_id)
        logger.debug(f"NPC {npc_id} entered {self.name}")

    def remove_npc(self, npc_id: str):
        """Remove an NPC from this room."""
        self.npcs.discard(npc_id)
        logger.debug(f"NPC {npc_id} left {self.name}")

    def get_npc_count(self) -> int:
        """Get the number of NPCs in this room."""
        return len(self.npcs)

    def get_total_occupants(self) -> int:
        """Get total number of players and NPCs in room."""
        return len(self.players) + len(self.npcs)

    def is_full(self, max_occupants: int = 20) -> bool:
        """Check if room has reached capacity.

        Args:
            max_occupants: Maximum allowed occupants (players + NPCs)

        Returns:
            True if room is at capacity
        """
        return self.get_total_occupants() >= max_occupants

    def can_enter(self, is_npc: bool = False, max_occupants: int = 20) -> bool:
        """Check if an entity can enter this room.

        Args:
            is_npc: True if checking for an NPC
            max_occupants: Maximum allowed occupants

        Returns:
            True if entity can enter
        """
        # NPCs don't count toward player-only limits
        if is_npc:
            return self.get_total_occupants() < max_occupants
        # Players have priority over NPCs for space
        return len(self.players) < max_occupants


class World:
    """Manages the game world and room connections."""

    def __init__(self):
        """Initialize the world from YAML files."""
        self.rooms: Dict[str, Room] = {}
        self.starting_room: str = 'alamo_plaza'  # Default
        self._load_from_yaml()

    def _load_from_yaml(self):
        """Load rooms from YAML files."""
        try:
            from room_loader import RoomLoader

            # Check if data directory exists
            data_dir = Path("data/rooms")
            if not data_dir.exists():
                raise RuntimeError(f"Room data directory not found: {data_dir}")

            # Load rooms from YAML
            loader = RoomLoader(str(data_dir))
            self.rooms = loader.load_all_rooms()

            if not self.rooms:
                raise RuntimeError("No rooms loaded from YAML files. Check your room definitions in data/rooms/")

            # Get the starting room from the loader
            self.starting_room = loader.starting_room
            logger.info(f"Successfully loaded {len(self.rooms)} rooms from YAML")
            logger.info(f"Starting room: {self.starting_room}")

        except ImportError as e:
            raise RuntimeError(f"Could not import room_loader: {e}. Make sure PyYAML is installed.")
        except Exception as e:
            logger.error(f"Error loading rooms from YAML: {e}")
            raise RuntimeError(f"Failed to load rooms: {e}")



    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by its ID."""
        return self.rooms.get(room_id)

    def get_room_players(self, room_id: str) -> Set[int]:
        """Get the set of player IDs in a room."""
        room = self.get_room(room_id)
        return room.players if room else set()

    def move_player(self, player_id: int, from_room_id: str, to_room_id: str):
        """Move a player from one room to another."""
        from_room = self.get_room(from_room_id)
        to_room = self.get_room(to_room_id)

        if from_room:
            from_room.remove_player(player_id)
        if to_room:
            to_room.add_player(player_id)

    def find_player_room(self, player_id: int) -> Optional[str]:
        """Find which room a player is in."""
        for room_id, room in self.rooms.items():
            if player_id in room.players:
                return room_id
        return None

    def get_direction_from_rooms(self, from_room_id: str, to_room_id: str) -> Optional[str]:
        """Get the direction to travel from one room to another."""
        from_room = self.get_room(from_room_id)
        if not from_room:
            return None

        for direction, room_id in from_room.exits.items():
            if room_id == to_room_id:
                return direction
        return None

    def get_opposite_direction(self, direction: str) -> str:
        """Get the opposite of a direction."""
        opposites = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east',
            'up': 'down',
            'down': 'up'
        }
        return opposites.get(direction, direction)

    def debug_world_state(self):
        """Print debug information about the world state."""
        logger.info("=== World State ===")
        logger.info(f"Total rooms loaded: {len(self.rooms)}")
        for room_id, room in self.rooms.items():
            logger.info(f"{room.name} ({room_id}):")
            logger.info(f"  Exits: {room.get_exit_list()}")
            logger.info(f"  Players: {len(room.players)}")

    def reload_rooms(self) -> bool:
        """Reload rooms from YAML files (development feature).

        Returns:
            True if reload was successful, False otherwise
        """

        try:
            from room_loader import RoomLoader

            # Preserve current player positions
            player_positions = {}
            for room_id, room in self.rooms.items():
                if room.players:
                    player_positions[room_id] = room.players.copy()

            # Load fresh room data
            loader = RoomLoader("data/rooms")
            new_rooms = loader.reload_rooms()

            if new_rooms:
                # Update rooms
                self.rooms = new_rooms

                # Restore player positions
                for room_id, players in player_positions.items():
                    if room_id in self.rooms:
                        self.rooms[room_id].players = players
                    else:
                        logger.warning(f"Room {room_id} no longer exists after reload")

                logger.info(f"Successfully reloaded {len(self.rooms)} rooms")
                return True
            else:
                logger.error("Failed to reload rooms")
                return False

        except Exception as e:
            logger.error(f"Error reloading rooms: {e}")
            return False


# Global world instance
world = World()