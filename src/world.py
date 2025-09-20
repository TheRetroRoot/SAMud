"""World module for SAMUD - defines rooms and the game world structure."""

import logging
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


class World:
    """Manages the game world and room connections."""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._initialize_world()

    def _initialize_world(self):
        """Create all rooms and their connections."""

        # Create rooms with descriptions
        self.rooms = {
            'alamo_plaza': Room(
                id='alamo_plaza',
                name='The Alamo Plaza',
                description='Stone walls surround you. Tourists move in and out of the historic courtyard. '
                           'The limestone facade of the mission stands proud against the Texas sky.',
                ascii_art="""
       _____
      /     \\
     /  ___  \\
    |  |   |  |      THE ALAMO
    |  | † |  |    Remember 1836
    |__|___|__|   _______________
       | | |     |_______________|
     __| | |__   |_______________|
    |_________|  |_______________|
    ||  ___  ||  |_______________|
    || |___| ||  |_______________|
    ||_______||  |_______________|
"""
            ),

            'river_walk_north': Room(
                id='river_walk_north',
                name='River Walk North',
                description='The water glistens as colorful barges float past. Cafes line both banks. '
                           'The sound of mariachi music drifts from a nearby restaurant.',
                ascii_art="""
    🌴                              🌴
   __|__    ☕ Cafe Rio    _____   __|__
  |     |__________________|     |_|     |
  |_____|~~~~~~~~~~~~~~~~~|______|_|_____|
     ~~~~~~~~🚣~~~~~~~~~~~~~🌊~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   ~~~~~~~~~ San Antonio River ~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  |‾‾‾‾‾|__________________|‾‾‾‾‾|‾|‾‾‾‾‾|
  |_____|   🍹 Cantina     |_____|_|_____|
    ||                              ||
"""
            ),

            'river_walk_south': Room(
                id='river_walk_south',
                name='River Walk South',
                description='Music drifts from restaurants. Cypress trees shade the walkway. '
                           'Stone bridges arch gracefully over the San Antonio River.',
                ascii_art="""
         _____..._____
       _/             \\_     Stone Bridge
      /                 \\
  ___/___________________\\___
  ‾‾‾\\‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾//‾‾‾
    ~~~~~~~~~~~~~~~~~~~~~
   ~~🦆~~~~ River ~~~~🦆~~
    ~~~~~~~~~~~~~~~~~~~~~
  🌳 |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| 🌳
     | Cypress Walkway  |
     |__________________|
"""
            ),

            'pearl': Room(
                id='pearl',
                name='The Pearl',
                description='The old brewery buzzes with activity. Food trucks and shops fill the plaza. '
                           'The weekend farmers market brings locals and visitors together.',
                ascii_art="""
     _____|PEARL|_____
    |   ___BREWERY___ |
    |  |  _______  |  |
    |  | |       | |  |    🚚 Food Trucks
    |  | | SHOPS | |  |    🌮 🍔 🍕
    |  |_|_______|_|  |
    |_________________|
    | 🏪 | 🏪 | 🏪 |
    |_____|_____|_____|
      Farmers Market
     🥬 🍅 🌽 🥕 🍎
"""
            ),

            'tower': Room(
                id='tower',
                name='Tower of the Americas',
                description='The needle pierces the sky at 750 feet. The city spreads out below. '
                           'You can see for miles in every direction from this vantage point.',
                ascii_art="""
           ☁️
           |
          _|_      750 ft
         |   |     ☁️
         |◉◉◉|    Observation Deck
         |___|
           |
           |      ☁️
           |
           |
          /|\\
         / | \\
        /  |  \\
       /   |   \\
      /____|____\\
     |___base___|
"""
            ),

            'mission': Room(
                id='mission',
                name='Mission San Jose',
                description='The limestone church stands serene. The rose window catches the light. '
                           'The Queen of Missions showcases Spanish colonial architecture.',
                ascii_art="""
         ___†___
        /       \\
       /  _◉_   \\    Rose Window
      |  |   |   |
      |  |___|   |    Mission San Jose
      |   ___    |    "Queen of Missions"
      |  |   |   |
    __|__|   |___|__
   |  ___     ___  |
   | |   |   |   | |
   |_|___|___|___|_|
         [===]       Spanish Colonial
"""
            ),

            'southtown': Room(
                id='southtown',
                name='Southtown',
                description='Art galleries and vintage shops line the street. Murals cover the walls. '
                           'The King William district showcases historic homes and trendy eateries.',
                ascii_art="""
   🎨 ART DISTRICT 🎨
  |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|
  | 🖼️ Gallery Row   |
  |___________________|
  | M U R A L   W A L L |
  |~~~~~~~~~~~~~~~~~~~~~|
  | 🎭 🎨 🖌️ 🎪 🎭 |
  |_____________________|
  | Vintage | Coffee ☕ |
  |_________|___________|
    King William Historic
         🏛️ 🏛️ 🏛️
"""
            )
        }

        # Define connections (bidirectional)
        self._connect_rooms('alamo_plaza', 'east', 'river_walk_north')
        self._connect_rooms('alamo_plaza', 'south', 'mission')
        self._connect_rooms('river_walk_north', 'south', 'river_walk_south')
        self._connect_rooms('river_walk_north', 'north', 'pearl')
        self._connect_rooms('river_walk_south', 'east', 'tower')
        self._connect_rooms('river_walk_south', 'west', 'southtown')

        logger.info(f"World initialized with {len(self.rooms)} rooms")
        self._validate_connections()

    def _connect_rooms(self, room1_id: str, direction: str, room2_id: str):
        """Create a bidirectional connection between two rooms."""
        opposite_directions = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east',
            'up': 'down',
            'down': 'up'
        }

        if room1_id in self.rooms and room2_id in self.rooms:
            # Connect room1 to room2
            self.rooms[room1_id].exits[direction] = room2_id

            # Connect room2 to room1 (opposite direction)
            opposite = opposite_directions.get(direction)
            if opposite:
                self.rooms[room2_id].exits[opposite] = room1_id

            logger.debug(f"Connected {room1_id} ({direction}) <-> {room2_id} ({opposite})")

    def _validate_connections(self):
        """Validate that all rooms are reachable and connections are bidirectional."""
        # Check all rooms are reachable from starting room
        visited = set()
        to_visit = ['alamo_plaza']

        while to_visit:
            room_id = to_visit.pop(0)
            if room_id in visited:
                continue

            visited.add(room_id)
            room = self.rooms[room_id]

            for exit_room_id in room.exits.values():
                if exit_room_id not in visited:
                    to_visit.append(exit_room_id)

        unreachable = set(self.rooms.keys()) - visited
        if unreachable:
            logger.warning(f"Unreachable rooms detected: {unreachable}")

        # Validate bidirectional connections
        for room_id, room in self.rooms.items():
            for direction, target_id in room.exits.items():
                if target_id not in self.rooms:
                    logger.error(f"Room {room_id} has exit to non-existent room {target_id}")
                    continue

                target_room = self.rooms[target_id]
                # Check if target has a connection back
                has_return = any(
                    back_id == room_id
                    for back_id in target_room.exits.values()
                )
                if not has_return:
                    logger.warning(f"Room {room_id} -> {target_id} lacks return connection")

        logger.info("World validation complete")

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
        for room_id, room in self.rooms.items():
            logger.info(f"{room.name} ({room_id}):")
            logger.info(f"  Exits: {room.get_exit_list()}")
            logger.info(f"  Players: {len(room.players)}")


# Global world instance
world = World()