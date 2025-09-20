"""NPC loader module for YAML-based NPC definitions."""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from npcs import NPC, npc_manager

logger = logging.getLogger(__name__)


class NPCLoader:
    """Loads NPC definitions from YAML files."""

    def __init__(self, data_dir: str = "data/npcs"):
        """Initialize the NPC loader.

        Args:
            data_dir: Directory containing NPC YAML files
        """
        self.data_dir = Path(data_dir)
        self.npc_configs: Dict[str, dict] = {}
        self.room_npcs: Dict[str, List[str]] = {}  # room_id -> list of npc_ids to spawn there
        self.loaded_npcs: Set[str] = set()

    def load_all_npcs(self) -> Dict[str, NPC]:
        """Load all NPCs from YAML files.

        Returns:
            Dictionary mapping NPC IDs to NPC objects
        """
        if not self.data_dir.exists():
            logger.error(f"NPC directory not found: {self.data_dir}")
            return {}

        # Find all YAML files
        npc_files = list(self.data_dir.glob("*.yml")) + list(self.data_dir.glob("*.yaml"))

        # Filter out template and schema files
        npc_files = [
            f for f in npc_files
            if not f.stem.startswith('_') and
               f.stem not in ['npc_schema_template', 'README']
        ]

        logger.info(f"Found {len(npc_files)} NPC configuration files")

        # Load each NPC configuration
        for file_path in npc_files:
            try:
                self._load_npc_file(file_path)
            except Exception as e:
                logger.error(f"Failed to load NPC file {file_path}: {e}")

        # Create NPC instances
        npcs = {}
        for npc_id, config in self.npc_configs.items():
            try:
                npc = NPC(npc_id, config)
                npcs[npc_id] = npc
                self.loaded_npcs.add(npc_id)
                logger.info(f"Loaded NPC: {npc_id} ({config.get('name', 'Unknown')})")
            except Exception as e:
                logger.error(f"Failed to create NPC {npc_id}: {e}")

        return npcs

    def _load_npc_file(self, file_path: Path):
        """Load a single NPC configuration file.

        Args:
            file_path: Path to the NPC YAML file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'npc' not in data:
                logger.warning(f"Invalid NPC file format: {file_path}")
                return

            npc_config = data['npc']
            npc_id = npc_config.get('id')

            if not npc_id:
                logger.warning(f"NPC missing ID in file: {file_path}")
                return

            # Validate required fields
            required_fields = ['name', 'description']
            missing_fields = [f for f in required_fields if f not in npc_config]

            if missing_fields:
                logger.warning(f"NPC {npc_id} missing required fields: {missing_fields}")
                # Add defaults for missing fields
                if 'name' not in npc_config:
                    npc_config['name'] = npc_id.replace('_', ' ').title()
                if 'description' not in npc_config:
                    npc_config['description'] = f"A {npc_config['name']}."

            # Store configuration
            self.npc_configs[npc_id] = npc_config

            logger.debug(f"Loaded NPC configuration: {npc_id}")

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading NPC file {file_path}: {e}")

    def parse_room_npcs(self, room_configs: Dict[str, dict]):
        """Parse NPC spawn points from room configurations.

        Args:
            room_configs: Dictionary of room configurations

        Note:
            This should be called by room_loader after rooms are loaded
        """
        self.room_npcs.clear()

        for room_id, room_config in room_configs.items():
            if 'npcs' in room_config and isinstance(room_config['npcs'], list):
                self.room_npcs[room_id] = room_config['npcs']
                logger.debug(f"Room {room_id} spawns NPCs: {room_config['npcs']}")

    async def initialize_npcs(self) -> int:
        """Initialize all NPCs and place them in their starting rooms.

        Returns:
            Number of NPCs initialized
        """
        # Load all NPC configurations
        npcs = self.load_all_npcs()

        # Register with manager
        for npc_id, npc in npcs.items():
            npc_manager.register_npc(npc)

        # Try to restore state from database first
        restored_count = 0
        for npc_id in npcs:
            try:
                if await npc_manager.load_npc_state(npc_id):
                    restored_count += 1
                    logger.debug(f"Restored state for NPC {npc_id}")
            except Exception as e:
                logger.warning(f"Could not restore state for NPC {npc_id}: {e}")

        # Place NPCs that weren't restored in their spawn rooms
        for room_id, npc_ids in self.room_npcs.items():
            for npc_id in npc_ids:
                npc = npc_manager.get_npc(npc_id)
                if npc and not npc.current_room:
                    # NPC hasn't been placed yet (no saved state)
                    npc_manager.place_npc(npc_id, room_id)
                    logger.info(f"Placed NPC {npc_id} in spawn room {room_id}")

        # Handle NPCs with invalid saved rooms
        for npc_id, npc in npcs.items():
            if npc.current_room:
                # Verify the room still exists
                from world import world
                if not world.get_room(npc.current_room):
                    logger.warning(f"NPC {npc_id} was in non-existent room {npc.current_room}")

                    # Find spawn room for this NPC
                    spawn_room = self._find_spawn_room(npc_id)
                    if spawn_room:
                        npc_manager.place_npc(npc_id, spawn_room)
                        logger.info(f"Relocated NPC {npc_id} to spawn room {spawn_room}")
                    else:
                        # Place in first allowed room if no spawn point
                        if npc.movement and 'allowed_rooms' in npc.movement:
                            allowed = npc.movement['allowed_rooms']
                            if allowed:
                                npc_manager.place_npc(npc_id, allowed[0])
                                logger.info(f"Placed NPC {npc_id} in first allowed room {allowed[0]}")

        logger.info(f"Initialized {len(npcs)} NPCs ({restored_count} restored from database)")
        return len(npcs)

    def _find_spawn_room(self, npc_id: str) -> Optional[str]:
        """Find the spawn room for an NPC.

        Args:
            npc_id: NPC to find spawn room for

        Returns:
            Room ID or None if no spawn point defined
        """
        for room_id, npc_ids in self.room_npcs.items():
            if npc_id in npc_ids:
                return room_id
        return None

    def validate_npc_config(self, config: dict) -> List[str]:
        """Validate an NPC configuration.

        Args:
            config: NPC configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        required = ['id', 'name', 'description']
        for field in required:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate ID format
        if 'id' in config:
            npc_id = config['id']
            if not isinstance(npc_id, str) or not npc_id.replace('_', '').isalnum():
                errors.append(f"Invalid ID format: {npc_id} (use snake_case)")

        # Validate dialogue
        if 'dialogue' in config:
            dialogue = config.get('dialogue', {})
            if not isinstance(dialogue, dict):
                errors.append("'dialogue' must be a dictionary")

        # Validate keywords
        if 'keywords' in config:
            keywords = config.get('keywords', {})
            if not isinstance(keywords, dict):
                errors.append("'keywords' must be a dictionary")
            else:
                for pattern in keywords:
                    if not isinstance(pattern, str):
                        errors.append(f"Invalid keyword pattern: {pattern}")

        # Validate movement
        if 'movement' in config:
            movement = config.get('movement', {})
            if not isinstance(movement, dict):
                errors.append("'movement' must be a dictionary")
            else:
                if 'allowed_rooms' in movement:
                    allowed = movement['allowed_rooms']
                    if not isinstance(allowed, list):
                        errors.append("'allowed_rooms' must be a list")

                if 'tick_interval' in movement:
                    interval = movement['tick_interval']
                    if not isinstance(interval, (int, float)) or interval <= 0:
                        errors.append(f"Invalid tick_interval: {interval}")

                if 'movement_probability' in movement:
                    prob = movement['movement_probability']
                    if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                        errors.append(f"Invalid movement_probability: {prob}")

        # Validate ambient actions
        if 'ambient_actions' in config:
            actions = config.get('ambient_actions', [])
            if not isinstance(actions, list):
                errors.append("'ambient_actions' must be a list")

        return errors

    def reload_npc(self, npc_id: str) -> bool:
        """Reload a specific NPC's configuration.

        Args:
            npc_id: NPC to reload

        Returns:
            True if reload was successful
        """
        # Find the NPC's configuration file
        npc_file = self.data_dir / f"{npc_id}.yml"
        if not npc_file.exists():
            npc_file = self.data_dir / f"{npc_id}.yaml"
            if not npc_file.exists():
                logger.error(f"NPC configuration file not found: {npc_id}")
                return False

        try:
            # Load new configuration
            with open(npc_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'npc' not in data:
                logger.error(f"Invalid NPC file format: {npc_file}")
                return False

            new_config = data['npc']

            # Validate configuration
            errors = self.validate_npc_config(new_config)
            if errors:
                logger.error(f"Invalid NPC configuration for {npc_id}: {errors}")
                return False

            # Get existing NPC
            existing_npc = npc_manager.get_npc(npc_id)
            if existing_npc:
                # Preserve runtime state
                current_room = existing_npc.current_room
                player_memories = existing_npc.player_memories
                state_data = existing_npc.state_data

                # Unregister old NPC
                npc_manager.unregister_npc(npc_id)

                # Create new NPC with updated config
                new_npc = NPC(npc_id, new_config)

                # Restore runtime state
                new_npc.current_room = current_room
                new_npc.player_memories = player_memories
                new_npc.state_data = state_data

                # Register new NPC
                npc_manager.register_npc(new_npc, current_room)
            else:
                # Create and register new NPC
                new_npc = NPC(npc_id, new_config)
                spawn_room = self._find_spawn_room(npc_id)
                npc_manager.register_npc(new_npc, spawn_room)

            self.npc_configs[npc_id] = new_config
            logger.info(f"Reloaded NPC configuration: {npc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reload NPC {npc_id}: {e}")
            return False


# Singleton instance
npc_loader = NPCLoader()