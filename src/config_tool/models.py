"""
Data models for room and NPC configurations
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path


@dataclass
class Exit:
    """Represents a room exit"""
    direction: str
    target_room: str


@dataclass
class Room:
    """Represents a room configuration"""
    id: str
    name: str
    description: str
    ascii_art_file: Optional[str] = None
    exits: Dict[str, str] = field(default_factory=dict)
    npcs: List[str] = field(default_factory=list)

    def to_yaml_dict(self) -> Dict:
        """Convert to YAML-compatible dictionary"""
        data = {
            'name': self.name,
            'description': self.description
        }
        if self.ascii_art_file:
            data['ascii_art_file'] = self.ascii_art_file
        if self.exits:
            data['exits'] = self.exits
        if self.npcs:
            data['npcs'] = self.npcs
        return data

    @classmethod
    def from_yaml_dict(cls, room_id: str, data: Dict) -> 'Room':
        """Create Room from YAML dictionary"""
        # Handle multiline descriptions - just strip trailing newline
        description = data.get('description', '')
        if isinstance(description, str):
            description = description.strip()

        return cls(
            id=room_id,
            name=data.get('name', ''),
            description=description,
            ascii_art_file=data.get('ascii_art_file'),
            exits=data.get('exits', {}),
            npcs=data.get('npcs', [])
        )


@dataclass
class Zone:
    """Represents a zone configuration"""
    name: str
    description: str
    file: str
    rooms: Dict[str, Room] = field(default_factory=dict)

    def to_yaml_dict(self) -> Dict:
        """Convert to YAML-compatible dictionary for zones.yml"""
        return {
            'name': self.name,
            'description': self.description,
            'file': self.file
        }

    def rooms_to_yaml_dict(self) -> Dict:
        """Convert rooms to YAML-compatible dictionary for zone file"""
        return {
            'rooms': {
                room_id: room.to_yaml_dict()
                for room_id, room in self.rooms.items()
            }
        }


@dataclass
class NPCDialogue:
    """NPC dialogue configuration"""
    greeting_new: str = ""
    greeting_return: str = ""
    farewell: str = ""
    player_arrival: str = ""
    player_departure: str = ""

    def to_dict(self) -> Dict:
        return {
            'greeting_new': self.greeting_new,
            'greeting_return': self.greeting_return,
            'farewell': self.farewell,
            'player_arrival': self.player_arrival,
            'player_departure': self.player_departure
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCDialogue':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NPCMovement:
    """NPC movement configuration"""
    allowed_rooms: List[str] = field(default_factory=list)
    tick_interval: int = 120
    movement_probability: float = 0.3
    schedule: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = {
            'allowed_rooms': self.allowed_rooms,
            'tick_interval': self.tick_interval,
            'movement_probability': self.movement_probability
        }
        if self.schedule:
            data['schedule'] = self.schedule
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCMovement':
        return cls(
            allowed_rooms=data.get('allowed_rooms', []),
            tick_interval=data.get('tick_interval', 120),
            movement_probability=data.get('movement_probability', 0.3),
            schedule=data.get('schedule', {})
        )


@dataclass
class NPCMemory:
    """NPC memory configuration"""
    remember_names: bool = True
    remember_topics: bool = True
    memory_duration: int = 30

    def to_dict(self) -> Dict:
        return {
            'remember_names': self.remember_names,
            'remember_topics': self.remember_topics,
            'memory_duration': self.memory_duration
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCMemory':
        return cls(
            remember_names=data.get('remember_names', True),
            remember_topics=data.get('remember_topics', True),
            memory_duration=data.get('memory_duration', 30)
        )


@dataclass
class NPCContext:
    """NPC context awareness configuration"""
    time_aware: bool = False
    crowd_aware: bool = False
    crowd_reactions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = {
            'time_aware': self.time_aware,
            'crowd_aware': self.crowd_aware
        }
        if self.crowd_reactions:
            data['crowd_reactions'] = self.crowd_reactions
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCContext':
        return cls(
            time_aware=data.get('time_aware', False),
            crowd_aware=data.get('crowd_aware', False),
            crowd_reactions=data.get('crowd_reactions', {})
        )


@dataclass
class NPC:
    """Represents an NPC configuration"""
    id: str
    name: str
    description: str = ""
    personality: str = ""
    dialogue: NPCDialogue = field(default_factory=NPCDialogue)
    keywords: Dict[str, str] = field(default_factory=dict)
    movement: NPCMovement = field(default_factory=NPCMovement)
    ambient_actions: List[str] = field(default_factory=list)
    memory: NPCMemory = field(default_factory=NPCMemory)
    context: NPCContext = field(default_factory=NPCContext)

    def to_yaml_dict(self) -> Dict:
        """Convert to YAML-compatible dictionary"""
        data = {
            'npc': {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'personality': self.personality,
                'dialogue': self.dialogue.to_dict(),
                'keywords': self.keywords,
                'movement': self.movement.to_dict(),
                'ambient_actions': self.ambient_actions,
                'memory': self.memory.to_dict(),
                'context': self.context.to_dict()
            }
        }

        # Remove empty fields
        if not data['npc']['keywords']:
            del data['npc']['keywords']
        if not data['npc']['ambient_actions']:
            del data['npc']['ambient_actions']

        return data

    @classmethod
    def from_yaml_dict(cls, data: Dict) -> 'NPC':
        """Create NPC from YAML dictionary"""
        npc_data = data.get('npc', data)
        return cls(
            id=npc_data.get('id', ''),
            name=npc_data.get('name', ''),
            description=npc_data.get('description', ''),
            personality=npc_data.get('personality', ''),
            dialogue=NPCDialogue.from_dict(npc_data.get('dialogue', {})),
            keywords=npc_data.get('keywords', {}),
            movement=NPCMovement.from_dict(npc_data.get('movement', {})),
            ambient_actions=npc_data.get('ambient_actions', []),
            memory=NPCMemory.from_dict(npc_data.get('memory', {})),
            context=NPCContext.from_dict(npc_data.get('context', {}))
        )


class WorldData:
    """Container for all world data"""
    def __init__(self):
        self.zones: Dict[str, Zone] = {}
        self.npcs: Dict[str, NPC] = {}
        self.zone_order: List[str] = []

    def load_from_files(self, data_dir: Path):
        """Load world data from YAML files"""
        rooms_dir = data_dir / 'rooms'
        npcs_dir = data_dir / 'npcs'

        # Load zones configuration
        zones_file = rooms_dir / 'zones.yml'
        if zones_file.exists():
            with open(zones_file) as f:
                zones_data = yaml.safe_load(f)

                # Handle both list and dict format for zones
                zones_list = zones_data.get('zones', [])
                if isinstance(zones_list, list):
                    # New format: zones is a list
                    for zone_info in zones_list:
                        zone_id = zone_info.get('id', zone_info.get('name', '').lower().replace(' ', '_'))
                        zone = Zone(
                            name=zone_info.get('name', ''),
                            description=zone_info.get('description', ''),
                            file=zone_info.get('file', '')
                        )

                        # Load zone rooms
                        zone_file = rooms_dir / zone_info.get('file', '')
                        if zone_file.exists():
                            with open(zone_file) as zf:
                                zone_rooms = yaml.safe_load(zf)
                                if zone_rooms and 'rooms' in zone_rooms:
                                    for room_id, room_data in zone_rooms.get('rooms', {}).items():
                                        zone.rooms[room_id] = Room.from_yaml_dict(room_id, room_data)

                        self.zones[zone_id] = zone
                        self.zone_order.append(zone_id)

                elif isinstance(zones_list, dict):
                    # Old format: zones is a dict
                    for zone_id, zone_info in zones_list.items():
                        zone = Zone(
                            name=zone_info.get('name', ''),
                            description=zone_info.get('description', ''),
                            file=zone_info.get('file', '')
                        )

                        # Load zone rooms
                        zone_file = rooms_dir / zone_info.get('file', '')
                        if zone_file.exists():
                            with open(zone_file) as zf:
                                zone_rooms = yaml.safe_load(zf)
                                for room_id, room_data in zone_rooms.get('rooms', {}).items():
                                    zone.rooms[room_id] = Room.from_yaml_dict(room_id, room_data)

                        self.zones[zone_id] = zone
                        self.zone_order.append(zone_id)

        # Load NPCs
        if npcs_dir.exists():
            for npc_file in npcs_dir.glob('*.yml'):
                if npc_file.name != 'npc_schema_template.yml':
                    with open(npc_file) as f:
                        npc_data = yaml.safe_load(f)
                        npc = NPC.from_yaml_dict(npc_data)
                        self.npcs[npc.id] = npc

    def save_to_files(self, data_dir: Path):
        """Save world data to YAML files"""
        rooms_dir = data_dir / 'rooms'
        npcs_dir = data_dir / 'npcs'

        # Save zones configuration in list format
        zones_list = []
        for zone_id in self.zone_order:
            if zone_id in self.zones:
                zone = self.zones[zone_id]
                zone_data = {
                    'id': zone_id,
                    'name': zone.name,
                    'file': zone.file,
                    'enabled': True,
                    'load_order': len(zones_list) + 1
                }
                if zone.description:
                    zone_data['description'] = zone.description
                zones_list.append(zone_data)

        zones_data = {
            'zones': zones_list,
            'settings': {
                'starting_room': 'alamo_plaza',
                'default_description': 'You find yourself in an undefined space.',
                'validate_connections': True,
                'allow_dynamic_loading': False
            }
        }

        zones_file = rooms_dir / 'zones.yml'
        with open(zones_file, 'w') as f:
            yaml.dump(zones_data, f, default_flow_style=False, sort_keys=False)

        # Save zone rooms
        for zone_id, zone in self.zones.items():
            zone_file = rooms_dir / zone.file
            with open(zone_file, 'w') as f:
                yaml.dump(zone.rooms_to_yaml_dict(), f, default_flow_style=False, sort_keys=False)

        # Save NPCs
        for npc_id, npc in self.npcs.items():
            npc_file = npcs_dir / f"{npc_id}.yml"
            with open(npc_file, 'w') as f:
                yaml.dump(npc.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)

    def get_all_rooms(self) -> Dict[str, Room]:
        """Get all rooms across all zones"""
        all_rooms = {}
        for zone in self.zones.values():
            all_rooms.update(zone.rooms)
        return all_rooms

    def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """Find a room by ID across all zones"""
        for zone in self.zones.values():
            if room_id in zone.rooms:
                return zone.rooms[room_id]
        return None