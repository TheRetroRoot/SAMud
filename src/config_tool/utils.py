"""
Utility functions for the configuration tool
"""
import shutil
from pathlib import Path
from datetime import datetime
import yaml
from typing import Dict, Any, List


def create_backup(file_path: Path) -> Path:
    """Create a backup of a file before modifying it"""
    if not file_path.exists():
        return None

    backup_dir = Path('data/backups')
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(file_path, backup_path)
    return backup_path


def validate_room_id(room_id: str) -> bool:
    """Validate a room ID format"""
    if not room_id:
        return False
    # Room IDs should be alphanumeric with underscores
    return all(c.isalnum() or c == '_' for c in room_id)


def validate_npc_id(npc_id: str) -> bool:
    """Validate an NPC ID format"""
    if not npc_id:
        return False
    # NPC IDs should be alphanumeric with underscores
    return all(c.isalnum() or c == '_' for c in npc_id)


def find_broken_exits(rooms: Dict[str, Any]) -> List[str]:
    """Find exits that point to non-existent rooms"""
    broken = []
    room_ids = set(rooms.keys())

    for room_id, room in rooms.items():
        for direction, target in room.exits.items():
            if target not in room_ids:
                broken.append(f"{room_id} -> {direction} -> {target} (not found)")

    return broken


def find_unreachable_rooms(rooms: Dict[str, Any], start_room: str = 'alamo_plaza') -> List[str]:
    """Find rooms that cannot be reached from the starting room"""
    if start_room not in rooms:
        return []

    visited = set()
    to_visit = [start_room]

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue

        visited.add(current)
        if current in rooms:
            for target in rooms[current].exits.values():
                if target not in visited and target in rooms:
                    to_visit.append(target)

    unreachable = [room_id for room_id in rooms.keys() if room_id not in visited]
    return unreachable


def find_orphaned_npcs(npcs: Dict[str, Any], rooms: Dict[str, Any]) -> List[str]:
    """Find NPCs that reference non-existent rooms"""
    orphaned = []
    room_ids = set(rooms.keys())

    for npc_id, npc in npcs.items():
        # Check allowed rooms
        for room_id in npc.movement.allowed_rooms:
            if room_id not in room_ids:
                orphaned.append(f"{npc_id} references non-existent room: {room_id}")

        # Check schedule rooms
        for time_slot, room_id in npc.movement.schedule.items():
            if room_id not in room_ids:
                orphaned.append(f"{npc_id} schedule ({time_slot}) references non-existent room: {room_id}")

    return orphaned


def sanitize_yaml_string(text: str) -> str:
    """Sanitize a string for YAML output"""
    # Escape special YAML characters if needed
    if any(c in text for c in [':', '{', '}', '[', ']', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
        # Use literal style for multi-line strings with special chars
        if '\n' in text:
            return f"|\n  {text.replace(chr(10), chr(10) + '  ')}"
        else:
            # Use quoted style for single-line strings
            return f'"{text.replace('"', '\\"')}"'
    return text


def get_direction_opposite(direction: str) -> str:
    """Get the opposite direction for bidirectional exits"""
    opposites = {
        'north': 'south',
        'south': 'north',
        'east': 'west',
        'west': 'east',
        'northeast': 'southwest',
        'northwest': 'southeast',
        'southeast': 'northwest',
        'southwest': 'northeast',
        'up': 'down',
        'down': 'up',
        'in': 'out',
        'out': 'in'
    }
    return opposites.get(direction.lower(), None)


def format_room_display_name(room) -> str:
    """Format a room for display in UI elements"""
    return f"{room.name} ({room.id})"


def format_npc_display_name(npc) -> str:
    """Format an NPC for display in UI elements"""
    return f"{npc.name} ({npc.id})"