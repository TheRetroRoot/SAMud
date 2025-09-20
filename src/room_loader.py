"""Room loader module for YAML-based room definitions."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from world import Room

logger = logging.getLogger(__name__)


class RoomLoader:
    """Loads room definitions from YAML files."""

    def __init__(self, data_dir: str = "data/rooms"):
        """Initialize the room loader.

        Args:
            data_dir: Directory containing room YAML files
        """
        self.data_dir = Path(data_dir)
        self.zones: Dict[str, dict] = {}
        self.rooms: Dict[str, Room] = {}
        self.connections: List[dict] = []
        self.room_npcs: Dict[str, List[str]] = {}  # room_id -> list of npc_ids
        self.starting_room: str = 'alamo_plaza'  # Default, will be overridden from YAML

    def load_all_rooms(self) -> Dict[str, Room]:
        """Load all rooms from YAML files.

        Returns:
            Dictionary mapping room IDs to Room objects
        """
        # Load zone metadata
        zones_file = self.data_dir / "zones.yml"
        if not zones_file.exists():
            logger.error(f"Zones file not found: {zones_file}")
            return {}

        try:
            with open(zones_file, 'r', encoding='utf-8') as f:
                zones_data = yaml.safe_load(f)

            # Get settings
            self.settings = zones_data.get('settings', {})
            self.starting_room = self.settings.get('starting_room', 'alamo_plaza')

            # Load zones in order
            zones = sorted(
                zones_data.get('zones', []),
                key=lambda z: z.get('load_order', 999)
            )

            for zone_info in zones:
                if zone_info.get('enabled', True):
                    self._load_zone(zone_info)

            # Create all connections after loading all rooms
            self._create_connections()

            # Validate if requested
            if self.settings.get('validate_connections', True):
                self._validate_connections()

            logger.info(f"Loaded {len(self.rooms)} rooms from {len(self.zones)} zones")
            return self.rooms

        except Exception as e:
            logger.error(f"Failed to load rooms: {e}")
            return {}

    def _load_zone(self, zone_info: dict):
        """Load a single zone file.

        Args:
            zone_info: Zone metadata dictionary
        """
        zone_file = self.data_dir / zone_info['file']
        if not zone_file.exists():
            logger.warning(f"Zone file not found: {zone_file}")
            return

        try:
            with open(zone_file, 'r', encoding='utf-8') as f:
                zone_data = yaml.safe_load(f)

            zone_id = zone_info['id']
            self.zones[zone_id] = zone_data.get('zone', {})

            # Load rooms from this zone
            for room_id, room_data in zone_data.get('rooms', {}).items():
                self._load_room(room_id, room_data, zone_id)

            logger.info(f"Loaded zone '{zone_id}' from {zone_file.name}")

        except Exception as e:
            logger.error(f"Failed to load zone {zone_info['id']}: {e}")

    def _load_room(self, room_id: str, room_data: dict, zone_id: str):
        """Load a single room from YAML data.

        Args:
            room_id: Unique room identifier
            room_data: Room data from YAML
            zone_id: Zone this room belongs to
        """
        try:
            # Load ASCII art from file if specified
            ascii_art = ''
            if 'ascii_art_file' in room_data:
                art_file = self.data_dir / 'art' / room_data['ascii_art_file']
                if art_file.exists():
                    try:
                        with open(art_file, 'r', encoding='utf-8') as f:
                            ascii_art = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to load art file for {room_id}: {e}")
                else:
                    logger.warning(f"Art file not found for {room_id}: {art_file}")
            elif 'ascii_art' in room_data:
                # Still support inline ASCII art if provided
                ascii_art = room_data.get('ascii_art', '')

            # Create Room object
            room = Room(
                id=room_id,
                name=room_data.get('name', room_id),
                description=room_data.get('description', self.settings.get('default_description', '')),
                ascii_art=ascii_art,
                exits={},  # Will be populated during connection phase
                players=set()
            )

            self.rooms[room_id] = room

            # Store exit information for later processing
            if 'exits' in room_data:
                for direction, target_id in room_data['exits'].items():
                    self.connections.append({
                        'from_room': room_id,
                        'direction': direction,
                        'to_room': target_id
                    })

            # Store NPC spawn information
            if 'npcs' in room_data and isinstance(room_data['npcs'], list):
                self.room_npcs[room_id] = room_data['npcs']
                logger.debug(f"Room '{room_id}' spawns NPCs: {room_data['npcs']}")

            logger.debug(f"Loaded room '{room_id}' in zone '{zone_id}'")

        except Exception as e:
            logger.error(f"Failed to load room {room_id}: {e}")

    def _create_connections(self):
        """Create all room connections after all rooms are loaded."""
        opposite_directions = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east',
            'up': 'down',
            'down': 'up',
            'northeast': 'southwest',
            'northwest': 'southeast',
            'southeast': 'northwest',
            'southwest': 'northeast'
        }

        # Track which connections we've already created
        created_connections = set()

        for conn in self.connections:
            from_room_id = conn['from_room']
            direction = conn['direction']
            to_room_id = conn['to_room']

            # Check if both rooms exist
            if from_room_id not in self.rooms:
                logger.warning(f"Connection references non-existent room: {from_room_id}")
                continue
            if to_room_id not in self.rooms:
                logger.warning(f"Connection references non-existent room: {to_room_id}")
                continue

            # Create forward connection
            from_room = self.rooms[from_room_id]
            from_room.exits[direction] = to_room_id

            # Create bidirectional connection if not already done
            conn_key = tuple(sorted([from_room_id, to_room_id]))
            if conn_key not in created_connections:
                # Create reverse connection
                opposite = opposite_directions.get(direction)
                if opposite:
                    to_room = self.rooms[to_room_id]
                    # Only create reverse if not explicitly defined
                    if opposite not in to_room.exits:
                        to_room.exits[opposite] = from_room_id

                created_connections.add(conn_key)

            logger.debug(f"Connected {from_room_id} ({direction}) -> {to_room_id}")

    def _validate_connections(self):
        """Validate that all rooms are reachable and connections are valid."""
        # Check for unreachable rooms
        if self.starting_room not in self.rooms:
            logger.error(f"Starting room '{self.starting_room}' not found!")
            return

        visited = set()
        to_visit = [self.starting_room]

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

        logger.info(f"Validation complete: {len(visited)}/{len(self.rooms)} rooms reachable")

    def reload_rooms(self) -> Dict[str, Room]:
        """Reload all rooms from YAML files (for development).

        Returns:
            Dictionary mapping room IDs to Room objects
        """
        logger.info("Reloading rooms from YAML files...")

        # Preserve player positions
        old_player_positions = {}
        for room_id, room in self.rooms.items():
            if room.players:
                old_player_positions[room_id] = room.players.copy()

        # Clear and reload
        self.zones.clear()
        self.rooms.clear()
        self.connections.clear()
        self.room_npcs.clear()

        # Load fresh data
        new_rooms = self.load_all_rooms()

        # Restore player positions
        for room_id, player_ids in old_player_positions.items():
            if room_id in new_rooms:
                new_rooms[room_id].players = player_ids
            else:
                logger.warning(f"Room {room_id} no longer exists, players displaced")

        return new_rooms

    def get_room_npcs(self) -> Dict[str, List[str]]:
        """Get NPC spawn information for all rooms.

        Returns:
            Dictionary mapping room IDs to lists of NPC IDs
        """
        return self.room_npcs.copy()