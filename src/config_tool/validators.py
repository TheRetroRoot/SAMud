"""
Validation logic for room and NPC configurations
"""
from typing import List, Tuple
from .models import Room, NPC, Zone, WorldData


class ValidationError:
    """Represents a validation error"""
    def __init__(self, level: str, category: str, message: str):
        self.level = level  # 'error', 'warning', 'info'
        self.category = category  # 'room', 'npc', 'exit', etc
        self.message = message

    def __str__(self):
        return f"[{self.level.upper()}] {self.category}: {self.message}"


class ConfigValidator:
    """Validates world configuration data"""

    def __init__(self, world_data: WorldData):
        self.world_data = world_data
        self.errors: List[ValidationError] = []

    def validate_all(self) -> List[ValidationError]:
        """Run all validations and return errors"""
        self.errors = []

        self._validate_room_ids()
        self._validate_npc_ids()
        self._validate_exits()
        self._validate_room_connectivity()
        self._validate_npc_rooms()
        self._validate_room_npcs()
        self._validate_zone_files()

        return self.errors

    def _validate_room_ids(self):
        """Check for duplicate or invalid room IDs"""
        seen_ids = set()
        for zone in self.world_data.zones.values():
            for room_id in zone.rooms.keys():
                # Check for duplicates
                if room_id in seen_ids:
                    self.errors.append(ValidationError(
                        'error', 'room',
                        f"Duplicate room ID: {room_id}"
                    ))
                seen_ids.add(room_id)

                # Check for invalid characters
                if not all(c.isalnum() or c == '_' for c in room_id):
                    self.errors.append(ValidationError(
                        'error', 'room',
                        f"Invalid room ID format: {room_id} (use only alphanumeric and underscore)"
                    ))

    def _validate_npc_ids(self):
        """Check for duplicate or invalid NPC IDs"""
        for npc_id in self.world_data.npcs.keys():
            # Check for invalid characters
            if not all(c.isalnum() or c == '_' for c in npc_id):
                self.errors.append(ValidationError(
                    'error', 'npc',
                    f"Invalid NPC ID format: {npc_id} (use only alphanumeric and underscore)"
                ))

    def _validate_exits(self):
        """Check that all exits point to valid rooms"""
        all_rooms = self.world_data.get_all_rooms()
        room_ids = set(all_rooms.keys())

        for room_id, room in all_rooms.items():
            for direction, target_id in room.exits.items():
                if target_id not in room_ids:
                    self.errors.append(ValidationError(
                        'error', 'exit',
                        f"Room '{room_id}' has exit '{direction}' to non-existent room '{target_id}'"
                    ))

                # Check if reverse exit exists (warning only)
                if target_id in all_rooms:
                    target_room = all_rooms[target_id]
                    opposite = self._get_opposite_direction(direction)
                    if opposite and opposite not in target_room.exits:
                        self.errors.append(ValidationError(
                            'warning', 'exit',
                            f"Room '{room_id}' exit '{direction}' to '{target_id}' has no return path"
                        ))

    def _validate_room_connectivity(self):
        """Check for unreachable rooms"""
        all_rooms = self.world_data.get_all_rooms()
        if not all_rooms:
            return

        # Find a starting room (prefer 'alamo_plaza' or first room)
        start_room = 'alamo_plaza' if 'alamo_plaza' in all_rooms else next(iter(all_rooms.keys()))

        visited = set()
        to_visit = [start_room]

        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue

            visited.add(current)
            if current in all_rooms:
                for target in all_rooms[current].exits.values():
                    if target not in visited and target in all_rooms:
                        to_visit.append(target)

        # Find unreachable rooms
        for room_id in all_rooms.keys():
            if room_id not in visited:
                self.errors.append(ValidationError(
                    'warning', 'room',
                    f"Room '{room_id}' is unreachable from starting room '{start_room}'"
                ))

    def _validate_npc_rooms(self):
        """Check that NPCs reference valid rooms"""
        all_rooms = self.world_data.get_all_rooms()
        room_ids = set(all_rooms.keys())

        for npc_id, npc in self.world_data.npcs.items():
            # Check allowed rooms
            for room_id in npc.movement.allowed_rooms:
                if room_id not in room_ids:
                    self.errors.append(ValidationError(
                        'error', 'npc',
                        f"NPC '{npc_id}' references non-existent room '{room_id}' in allowed_rooms"
                    ))

            # Check schedule rooms
            for time_slot, room_id in npc.movement.schedule.items():
                if room_id not in room_ids:
                    self.errors.append(ValidationError(
                        'error', 'npc',
                        f"NPC '{npc_id}' schedule ({time_slot}) references non-existent room '{room_id}'"
                    ))

    def _validate_room_npcs(self):
        """Check that rooms reference valid NPCs"""
        npc_ids = set(self.world_data.npcs.keys())
        all_rooms = self.world_data.get_all_rooms()

        for room_id, room in all_rooms.items():
            for npc_id in room.npcs:
                if npc_id not in npc_ids:
                    self.errors.append(ValidationError(
                        'error', 'room',
                        f"Room '{room_id}' references non-existent NPC '{npc_id}'"
                    ))

    def _validate_zone_files(self):
        """Check zone file references"""
        for zone_id, zone in self.world_data.zones.items():
            if not zone.file:
                self.errors.append(ValidationError(
                    'error', 'zone',
                    f"Zone '{zone_id}' has no file specified"
                ))

    def _get_opposite_direction(self, direction: str) -> str:
        """Get the opposite direction for bidirectional exits"""
        opposites = {
            'north': 'south', 'south': 'north',
            'east': 'west', 'west': 'east',
            'northeast': 'southwest', 'northwest': 'southeast',
            'southeast': 'northwest', 'southwest': 'northeast',
            'up': 'down', 'down': 'up',
            'in': 'out', 'out': 'in'
        }
        return opposites.get(direction.lower(), None)


def validate_world_data(world_data: WorldData) -> Tuple[List[ValidationError], int, int]:
    """
    Validate world data and return errors, warnings, and info counts
    Returns: (errors_list, error_count, warning_count)
    """
    validator = ConfigValidator(world_data)
    errors = validator.validate_all()

    error_count = sum(1 for e in errors if e.level == 'error')
    warning_count = sum(1 for e in errors if e.level == 'warning')

    return errors, error_count, warning_count