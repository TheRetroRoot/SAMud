"""NPC module for SAMUD - manages non-player characters."""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class NPC:
    """Represents a non-player character in the game."""

    def __init__(self, npc_id: str, config: Dict[str, Any]):
        """Initialize an NPC from configuration.

        Args:
            npc_id: Unique identifier for the NPC
            config: Configuration dictionary from YAML
        """
        self.id = npc_id
        self.name = config.get('name', 'Unknown')
        self.description = config.get('description', 'An unremarkable figure.')
        self.personality = config.get('personality', '')

        # Current state
        self.current_room: Optional[str] = None
        self.last_moved: datetime = datetime.now()
        self.last_action: datetime = datetime.now()
        self.is_interacting: bool = False
        self.state_data: Dict[str, Any] = {}

        # Configuration
        self.dialogue = config.get('dialogue', {})
        self.keywords = config.get('keywords', {})
        self.movement = config.get('movement', {})
        self.ambient_actions = config.get('ambient_actions', [])
        self.memory_settings = config.get('memory', {})
        self.context = config.get('context', {})

        # Runtime data
        self.player_memories: Dict[str, Dict] = {}  # player_name -> memory data
        self.pending_response: Optional[tuple] = None  # (message, delay)

        logger.debug(f"Initialized NPC: {self.id} ({self.name})")

    def get_greeting(self, player_name: str, is_known: bool = False) -> str:
        """Get appropriate greeting for a player.

        Args:
            player_name: Name of the player
            is_known: Whether this player has been met before

        Returns:
            Greeting message
        """
        if is_known and 'greeting_return' in self.dialogue:
            greeting = self.dialogue['greeting_return']
            return greeting.replace('{player}', player_name)
        elif 'greeting_new' in self.dialogue:
            return self.dialogue['greeting_new']
        return f"{self.name} nods in acknowledgment."

    def get_farewell(self) -> str:
        """Get farewell message when NPC leaves."""
        return self.dialogue.get('farewell', f"{self.name} departs.")

    def check_keywords(self, message: str) -> Optional[str]:
        """Check if message contains any trigger keywords.

        Args:
            message: Player's message to check

        Returns:
            NPC response if keywords found, None otherwise
        """
        import re

        message_lower = message.lower()

        # Track best match priority (longer matches are higher priority)
        best_match = None
        best_match_length = 0

        for pattern, response in self.keywords.items():
            # Split pattern by pipe for multiple triggers
            triggers = [t.strip().lower() for t in pattern.split('|')]
            for trigger in triggers:
                # Try exact word match first (with word boundaries)
                word_pattern = r'\b' + re.escape(trigger) + r'\b'
                if re.search(word_pattern, message_lower):
                    if len(trigger) > best_match_length:
                        best_match = response
                        best_match_length = len(trigger)
                # Fall back to substring match
                elif trigger in message_lower:
                    if len(trigger) > best_match_length:
                        best_match = response
                        best_match_length = len(trigger)

        return best_match

    def get_ambient_action(self, player_count: int = 0) -> Optional[str]:
        """Get a random ambient action.

        Args:
            player_count: Number of players in room (for contextual actions)

        Returns:
            Action description or None if no actions defined
        """
        if not self.ambient_actions:
            return None

        # Don't perform actions too frequently
        if (datetime.now() - self.last_action).seconds < 30:
            return None

        # Check context awareness settings
        if self.context.get('crowd_aware', False) and player_count > 0:
            # Adjust behavior based on crowd size
            crowd_reactions = self.context.get('crowd_reactions', {})
            if player_count == 0 and 'empty' in crowd_reactions:
                action = crowd_reactions['empty']
            elif player_count <= 2 and 'few' in crowd_reactions:
                action = crowd_reactions['few']
            elif player_count > 4 and 'many' in crowd_reactions:
                action = crowd_reactions['many']
            else:
                action = random.choice(self.ambient_actions)
        else:
            action = random.choice(self.ambient_actions)

        self.last_action = datetime.now()

        # Check time awareness
        if self.context.get('time_aware', False):
            from tick_scheduler import TimeOfDay
            period = TimeOfDay.get_period()
            # Could modify action based on time, but keep it simple for now

        return f"{self.name} {action}."

    def get_arrival_reaction(self, player_name: str) -> Optional[str]:
        """Get NPC reaction when a player arrives.

        Args:
            player_name: Player who arrived

        Returns:
            Reaction message or None
        """
        if 'player_arrival' in self.dialogue:
            msg = self.dialogue['player_arrival']
            return msg.replace('{player}', player_name)
        return None

    def get_departure_reaction(self, player_name: str) -> Optional[str]:
        """Get NPC reaction when a player leaves.

        Args:
            player_name: Player who left

        Returns:
            Reaction message or None
        """
        if 'player_departure' in self.dialogue:
            msg = self.dialogue['player_departure']
            return msg.replace('{player}', player_name)
        return None

    def can_move_to(self, room_id: str) -> bool:
        """Check if NPC can move to a specific room.

        Args:
            room_id: Room to check

        Returns:
            True if movement is allowed
        """
        if not self.movement:
            return False

        allowed_rooms = self.movement.get('allowed_rooms', [])
        return room_id in allowed_rooms

    def get_next_room(self, current_time: Optional[datetime] = None) -> Optional[str]:
        """Determine next room based on schedule or random choice.

        Args:
            current_time: Current time for schedule checking

        Returns:
            Room ID to move to, or None if no movement
        """
        if not self.movement or self.is_interacting:
            return None

        # Check if enough time has passed
        tick_interval = self.movement.get('tick_interval', 120)
        if (datetime.now() - self.last_moved).seconds < tick_interval:
            return None

        # Check movement probability
        move_prob = self.movement.get('movement_probability', 0.3)
        if random.random() > move_prob:
            return None

        # Check schedule first
        if current_time and 'schedule' in self.movement:
            schedule = self.movement['schedule']
            hour = current_time.hour

            if 6 <= hour < 12:
                time_period = 'morning'
            elif 12 <= hour < 18:
                time_period = 'afternoon'
            elif 18 <= hour < 24:
                time_period = 'evening'
            else:
                time_period = 'night'

            if time_period in schedule:
                target_room = schedule[time_period]
                if target_room != self.current_room:
                    return target_room

        # Otherwise pick random allowed room
        allowed_rooms = self.movement.get('allowed_rooms', [])
        if allowed_rooms:
            # Filter out current room
            other_rooms = [r for r in allowed_rooms if r != self.current_room]
            if other_rooms:
                return random.choice(other_rooms)

        return None

    def get_movement_message(self, destination: str, is_departure: bool) -> str:
        """Get movement broadcast message.

        Args:
            destination: Room being moved to/from
            is_departure: True for departure, False for arrival

        Returns:
            Movement message
        """
        if is_departure:
            if 'departure_message' in self.movement:
                msg = self.movement['departure_message']
                return msg.replace('{npc_name}', self.name).replace('{destination}', destination)
            return f"{self.name} heads off toward {destination}."
        else:
            if 'arrival_message' in self.movement:
                msg = self.movement['arrival_message']
                return msg.replace('{npc_name}', self.name).replace('{origin}', destination)
            return f"{self.name} arrives."

    def remember_player(self, player_name: str, topic: Optional[str] = None):
        """Record interaction with a player.

        Args:
            player_name: Player to remember
            topic: Optional conversation topic
        """
        if not self.memory_settings.get('remember_names', True):
            return

        if player_name not in self.player_memories:
            self.player_memories[player_name] = {
                'first_met': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'interaction_count': 0,
                'topics': []
            }

        memory = self.player_memories[player_name]
        memory['last_seen'] = datetime.now().isoformat()
        memory['interaction_count'] += 1

        if topic and self.memory_settings.get('remember_topics', True):
            if topic not in memory['topics']:
                memory['topics'].append(topic)

    def knows_player(self, player_name: str) -> bool:
        """Check if NPC remembers a player.

        Args:
            player_name: Player to check

        Returns:
            True if player is remembered
        """
        if not self.memory_settings.get('remember_names', True):
            return False

        if player_name not in self.player_memories:
            return False

        # Check if memory has expired
        memory_duration = self.memory_settings.get('memory_duration', 30)
        last_seen = datetime.fromisoformat(self.player_memories[player_name]['last_seen'])

        if (datetime.now() - last_seen).days > memory_duration:
            del self.player_memories[player_name]
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize NPC state for storage.

        Returns:
            Dictionary of NPC state
        """
        return {
            'id': self.id,
            'current_room': self.current_room,
            'last_moved': self.last_moved.isoformat(),
            'state_data': self.state_data,
            'player_memories': self.player_memories
        }

    def from_dict(self, state: Dict[str, Any]):
        """Restore NPC state from storage.

        Args:
            state: Saved state dictionary
        """
        self.current_room = state.get('current_room')
        self.last_moved = datetime.fromisoformat(state.get('last_moved', datetime.now().isoformat()))
        self.state_data = state.get('state_data', {})
        self.player_memories = state.get('player_memories', {})


class NPCManager:
    """Manages all NPCs in the game."""

    def __init__(self):
        """Initialize the NPC manager."""
        self.npcs: Dict[str, NPC] = {}
        self.room_npcs: Dict[str, Set[str]] = {}  # room_id -> set of npc_ids
        self.npc_tasks: Dict[str, asyncio.Task] = {}  # Active async tasks
        logger.info("NPCManager initialized")

    def register_npc(self, npc: NPC, initial_room: Optional[str] = None):
        """Register an NPC with the manager.

        Args:
            npc: NPC instance to register
            initial_room: Optional starting room
        """
        self.npcs[npc.id] = npc

        if initial_room:
            self.place_npc(npc.id, initial_room)

        logger.info(f"Registered NPC: {npc.id} ({npc.name})")

    def unregister_npc(self, npc_id: str):
        """Remove an NPC from the manager.

        Args:
            npc_id: ID of NPC to remove
        """
        if npc_id in self.npcs:
            npc = self.npcs[npc_id]

            # Remove from room
            if npc.current_room:
                self.remove_npc_from_room(npc_id, npc.current_room)

            # Cancel any active tasks
            if npc_id in self.npc_tasks:
                self.npc_tasks[npc_id].cancel()
                del self.npc_tasks[npc_id]

            del self.npcs[npc_id]
            logger.info(f"Unregistered NPC: {npc_id}")

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID.

        Args:
            npc_id: NPC identifier

        Returns:
            NPC instance or None if not found
        """
        return self.npcs.get(npc_id)

    def get_npcs_in_room(self, room_id: str) -> List[NPC]:
        """Get all NPCs in a specific room.

        Args:
            room_id: Room identifier

        Returns:
            List of NPC instances
        """
        npc_ids = self.room_npcs.get(room_id, set())
        return [self.npcs[npc_id] for npc_id in npc_ids if npc_id in self.npcs]

    def place_npc(self, npc_id: str, room_id: str):
        """Place an NPC in a room.

        Args:
            npc_id: NPC to place
            room_id: Destination room
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            logger.warning(f"Attempted to place unknown NPC: {npc_id}")
            return

        # Remove from current room
        if npc.current_room:
            self.remove_npc_from_room(npc_id, npc.current_room)
            # Update Room object
            from world import world
            old_room = world.get_room(npc.current_room)
            if old_room:
                old_room.remove_npc(npc_id)

        # Add to new room
        npc.current_room = room_id
        if room_id not in self.room_npcs:
            self.room_npcs[room_id] = set()
        self.room_npcs[room_id].add(npc_id)

        # Update Room object
        from world import world
        new_room = world.get_room(room_id)
        if new_room:
            new_room.add_npc(npc_id)

        logger.debug(f"Placed NPC {npc_id} in room {room_id}")

    def remove_npc_from_room(self, npc_id: str, room_id: str):
        """Remove an NPC from a room.

        Args:
            npc_id: NPC to remove
            room_id: Room to remove from
        """
        if room_id in self.room_npcs:
            self.room_npcs[room_id].discard(npc_id)
            if not self.room_npcs[room_id]:
                del self.room_npcs[room_id]

    async def move_npc(self, npc_id: str, destination: str) -> bool:
        """Move an NPC to a different room.

        Args:
            npc_id: NPC to move
            destination: Target room

        Returns:
            True if move was successful
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return False

        if not npc.can_move_to(destination):
            logger.debug(f"NPC {npc_id} cannot move to {destination}")
            return False

        old_room = npc.current_room

        # Broadcast departure
        if old_room:
            from broadcast import broadcast_manager
            departure_msg = npc.get_movement_message(destination, is_departure=True)
            await broadcast_manager.broadcast_to_room(
                old_room, departure_msg, is_system=True
            )

        # Update room tracking
        from world import world
        if old_room:
            old_room_obj = world.get_room(old_room)
            if old_room_obj:
                old_room_obj.remove_npc(npc_id)

        # Move NPC
        self.place_npc(npc_id, destination)
        npc.last_moved = datetime.now()

        # Add to new room
        new_room_obj = world.get_room(destination)
        if new_room_obj:
            new_room_obj.add_npc(npc_id)

        # Broadcast arrival
        from broadcast import broadcast_manager
        arrival_msg = npc.get_movement_message(old_room or "somewhere", is_departure=False)
        await broadcast_manager.broadcast_to_room(
            destination, arrival_msg, is_system=True
        )

        # Save state to database
        await self.save_npc_state(npc_id)

        logger.info(f"NPC {npc_id} moved from {old_room} to {destination}")
        return True

    def check_player_interaction(self, npc_id: str, room_id: str) -> bool:
        """Check if players are interacting with an NPC.

        Args:
            npc_id: NPC to check
            room_id: Room to check

        Returns:
            True if players are present and potentially interacting
        """
        from player import player_manager

        # Check if players are in the room
        players = player_manager.get_players_in_room(room_id)
        if not players:
            return False

        # Check if NPC was recently addressed
        npc = self.npcs.get(npc_id)
        if npc and npc.pending_response:
            return True

        return len(players) > 0  # Conservative: assume interaction if players present

    async def save_npc_state(self, npc_id: str):
        """Save NPC state to database.

        Args:
            npc_id: NPC to save
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return

        from database import Database
        db = Database()

        state_data = json.dumps(npc.state_data)
        memory_data = json.dumps(npc.player_memories)

        async with db.get_connection() as conn:
            # Save or update NPC state
            await conn.execute("""
                INSERT INTO npc_state (npc_id, current_room, last_moved, state_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(npc_id) DO UPDATE SET
                    current_room = excluded.current_room,
                    last_moved = excluded.last_moved,
                    state_data = excluded.state_data
            """, (npc_id, npc.current_room, npc.last_moved, state_data))

            # Save player memories
            for player_name, memory in npc.player_memories.items():
                await conn.execute("""
                    INSERT INTO npc_memory (npc_id, player_name, last_interaction, interaction_count, memory_data)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(npc_id, player_name) DO UPDATE SET
                        last_interaction = excluded.last_interaction,
                        interaction_count = excluded.interaction_count,
                        memory_data = excluded.memory_data
                """, (
                    npc_id,
                    player_name,
                    memory.get('last_seen', datetime.now().isoformat()),
                    memory.get('interaction_count', 1),
                    json.dumps(memory)
                ))

            await conn.commit()

    async def load_npc_state(self, npc_id: str) -> bool:
        """Load NPC state from database.

        Args:
            npc_id: NPC to load

        Returns:
            True if state was loaded successfully
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return False

        from database import Database
        db = Database()

        async with db.get_connection() as conn:
            # Load NPC state
            cursor = await conn.execute(
                "SELECT current_room, last_moved, state_data FROM npc_state WHERE npc_id = ?",
                (npc_id,)
            )
            row = await cursor.fetchone()

            if row:
                npc.current_room = row['current_room']
                npc.last_moved = datetime.fromisoformat(row['last_moved'])
                npc.state_data = json.loads(row['state_data']) if row['state_data'] else {}

                # Place NPC in room
                if npc.current_room:
                    self.place_npc(npc_id, npc.current_room)

            # Load player memories
            cursor = await conn.execute(
                "SELECT player_name, memory_data FROM npc_memory WHERE npc_id = ?",
                (npc_id,)
            )
            rows = await cursor.fetchall()

            for row in rows:
                player_name = row['player_name']
                memory_data = json.loads(row['memory_data']) if row['memory_data'] else {}
                npc.player_memories[player_name] = memory_data

        logger.info(f"Loaded state for NPC {npc_id}")
        return True

    async def save_all_states(self):
        """Save all NPC states to database."""
        tasks = [self.save_npc_state(npc_id) for npc_id in self.npcs]
        await asyncio.gather(*tasks)
        logger.info(f"Saved state for {len(self.npcs)} NPCs")

    async def process_room_message(self, room_id: str, player_name: str, message: str):
        """Process a player's message for NPC keyword responses.

        Args:
            room_id: Room where message was spoken
            player_name: Player who spoke
            message: The message content
        """
        npcs_in_room = self.get_npcs_in_room(room_id)
        if not npcs_in_room:
            return

        # Check each NPC for keyword matches
        responses = []
        for npc in npcs_in_room:
            response = npc.check_keywords(message)
            if response:
                # Remember this interaction
                npc.remember_player(player_name, topic=message[:50])

                # Schedule response with delay
                responses.append((npc, response))

        # Send NPC responses with delay
        if responses:
            await asyncio.sleep(1.5)  # Natural response delay

            from broadcast import broadcast_manager
            for npc, response in responses:
                # Format NPC response
                npc_message = f"[NPC] {npc.name}: {response}"
                await broadcast_manager.broadcast_to_room(
                    room_id, npc_message, is_system=False
                )

                # Small delay between multiple NPC responses
                if len(responses) > 1:
                    await asyncio.sleep(0.5)

    async def handle_player_arrival(self, room_id: str, player_name: str):
        """Handle when a player enters a room with NPCs.

        Args:
            room_id: Room the player entered
            player_name: Player who arrived
        """
        npcs_in_room = self.get_npcs_in_room(room_id)
        if not npcs_in_room:
            return

        await asyncio.sleep(1.0)  # Brief delay before greeting

        from broadcast import broadcast_manager
        for npc in npcs_in_room:
            if 'player_arrival' in npc.dialogue:
                message = npc.dialogue['player_arrival']
                npc_message = f"[NPC] {npc.name}: {message}"
                await broadcast_manager.broadcast_to_room(
                    room_id, npc_message, is_system=False
                )
                break  # Only one NPC greets to avoid spam

    async def handle_player_departure(self, room_id: str, player_name: str):
        """Handle when a player leaves a room with NPCs.

        Args:
            room_id: Room the player left
            player_name: Player who left
        """
        npcs_in_room = self.get_npcs_in_room(room_id)
        if not npcs_in_room:
            return

        from broadcast import broadcast_manager
        for npc in npcs_in_room:
            if 'player_departure' in npc.dialogue:
                message = npc.dialogue['player_departure']
                npc_message = f"[NPC] {npc.name}: {message}"
                await broadcast_manager.broadcast_to_room(
                    room_id, npc_message, is_system=False
                )
                break  # Only one NPC says goodbye to avoid spam

    def shutdown(self):
        """Clean shutdown of NPC manager."""
        # Cancel all active tasks
        for task in self.npc_tasks.values():
            task.cancel()
        self.npc_tasks.clear()

        logger.info("NPCManager shutdown complete")


# Singleton instance
npc_manager = NPCManager()