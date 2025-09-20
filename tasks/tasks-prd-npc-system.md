# Task List: NPC System Implementation

**Generated from:** prd-npc-system.md
**Date:** 2025-09-20
**Status:** Phase 1 - Parent Tasks

## Relevant Files

### Files to Create:
- `src/npcs.py` - Main NPC manager module with NPC lifecycle management
- `src/npc_loader.py` - YAML loader for NPC configurations (similar pattern to room_loader.py)
- `src/tick_scheduler.py` - Async tick system for NPC movements and ambient actions
- `data/npcs/` - Directory for NPC YAML configurations
- `data/npcs/*.yml` - Individual NPC configuration files (8+ NPCs)

### Files to Modify:
- `schema.sql` - Add npc_state and npc_memory tables
- `src/database.py` - Add NPC-related database operations
- `src/room_loader.py` - Parse NPC references in room YAML files
- `src/world.py` - Integrate NPCs into room display
- `src/commands.py` - Add keyword detection for NPC responses
- `src/broadcast.py` - Add NPC message formatting
- `src/server.py` - Initialize NPC system on startup
- `src/player.py` - Track NPC interactions
- `data/rooms/*.yml` - Add NPC spawn points to existing rooms

## Phase 1: Parent Tasks

These are the high-level implementation tasks. Wait for confirmation before expanding into sub-tasks.

- [x] **1.0 Database Schema Extension**
  Setup database tables for NPC state persistence and player memory
  - [x] 1.1 Create SQL migration script for npc_state table
  - [x] 1.2 Create SQL migration script for npc_memory table
  - [x] 1.3 Add indexes for efficient NPC lookups
  - [x] 1.4 Update schema.sql with new table definitions
  - [x] 1.5 Test database initialization with new schema

- [x] **2.0 NPC Configuration System**
  Create YAML-based configuration system for defining NPCs
  - [x] 2.1 Create data/npcs/ directory structure
  - [x] 2.2 Define NPC YAML schema specification
  - [x] 2.3 Create example NPC configuration template
  - [x] 2.4 Add YAML validation for NPC configs
  - [x] 2.5 Document NPC configuration format

- [x] **3.0 Core NPC Module**
  Implement NPC manager and individual NPC class with basic functionality
  - [x] 3.1 Create src/npcs.py with NPCManager class
  - [x] 3.2 Implement NPC class with properties (id, name, description)
  - [x] 3.3 Add NPC state management (current_room, last_moved)
  - [x] 3.4 Create singleton npc_manager instance
  - [x] 3.5 Add logging for NPC lifecycle events
  - [x] 3.6 Implement NPC registry and lookup methods

- [x] **4.0 NPC Loading System**
  Build loader to parse YAML configs and instantiate NPCs at startup
  - [x] 4.1 Create src/npc_loader.py following room_loader pattern
  - [x] 4.2 Implement YAML parsing for NPC files
  - [x] 4.3 Add NPC instantiation from configs
  - [x] 4.4 Load NPCs into manager registry
  - [x] 4.5 Handle missing/invalid NPC configs gracefully
  - [x] 4.6 Restore NPC state from database on startup

- [x] **5.0 Room Integration**
  Modify room system to display NPCs and handle spawn points
  - [x] 5.1 Add npcs field to room YAML schema
  - [x] 5.2 Modify room_loader.py to parse NPC spawn points
  - [x] 5.3 Update Room class to track NPCs present
  - [x] 5.4 Modify look command to show NPCs in room
  - [x] 5.5 Format NPC descriptions in room display
  - [x] 5.6 Add NPC count to room capacity checks

- [x] **6.0 Keyword Detection System**
  Implement message scanning for NPC trigger words and responses
  - [x] 6.1 Create keyword matching engine with regex support
  - [x] 6.2 Parse keyword mappings from NPC configs
  - [x] 6.3 Integrate with say command processing
  - [x] 6.4 Add 1-2 second response delay
  - [x] 6.5 Format NPC responses with [NPC] prefix
  - [x] 6.6 Handle multiple keyword matches priority

- [x] **7.0 Tick Scheduler Implementation**
  Create async tick system for NPC movements and scheduled actions
  - [x] 7.1 Create src/tick_scheduler.py with TickScheduler class
  - [x] 7.2 Implement async task loop for ticks
  - [x] 7.3 Add variable tick intervals per NPC
  - [x] 7.4 Create time-of-day detection (morning/afternoon/evening)
  - [x] 7.5 Register NPCs with scheduler on load
  - [x] 7.6 Handle scheduler shutdown gracefully

- [x] **8.0 NPC Movement System**
  Implement room-to-room movement with broadcasts and constraints
  - [x] 8.1 Add movement logic to NPC class
  - [x] 8.2 Validate movement against allowed_rooms
  - [x] 8.3 Check for player interactions before moving
  - [x] 8.4 Broadcast departure message to current room
  - [x] 8.5 Update NPC location in manager and database
  - [x] 8.6 Broadcast arrival message to new room
  - [x] 8.7 Handle schedule-based movement targets

- [x] **9.0 Memory and Persistence System**
  Build player recognition and interaction history tracking
  - [x] 9.1 Add database methods for NPC state save/load
  - [x] 9.2 Implement player memory storage (JSON in database)
  - [x] 9.3 Track interaction counts and timestamps
  - [x] 9.4 Create greeting variation logic (new vs returning)
  - [x] 9.5 Add memory pruning for 30+ day old interactions
  - [x] 9.6 Implement state restoration after server restart

- [x] **10.0 Ambient Action System**
  Add contextual reactions and periodic ambient behaviors
  - [x] 10.1 Parse ambient_actions from NPC configs
  - [x] 10.2 Create random action selection logic
  - [x] 10.3 Add player arrival/departure reactions
  - [x] 10.4 Implement ambient action timer (30-60 seconds)
  - [x] 10.5 Broadcast ambient actions to room
  - [x] 10.6 Add contextual awareness (player count, time of day)

- [x] **11.0 NPC Content Creation**
  Create 8+ San Antonio-themed NPC configurations
  - [x] 11.1 Create tourist_guide.yml (Alamo Plaza)
  - [x] 11.2 Create mariachi_band.yml (River Walk areas)
  - [x] 11.3 Create food_vendor.yml (The Pearl)
  - [x] 11.4 Create tour_guide.yml (Tower of the Americas)
  - [x] 11.5 Create priest.yml (Mission San Jose)
  - [x] 11.6 Create artist.yml (Southtown)
  - [x] 11.7 Create boat_captain.yml (River Walk)
  - [x] 11.8 Create photographer.yml (various locations)
  - [x] 11.9 Add NPCs to appropriate room YAML files
  - [x] 11.10 Write culturally authentic dialogue and responses

---

## Notes for Implementation

### Architecture Patterns to Follow:
- Use async/await pattern consistent with existing codebase
- Follow singleton pattern for managers (like player_manager, broadcast_manager)
- Use YAML for configuration (similar to room_loader pattern)
- Implement proper logging throughout

### Key Integration Points:
- NPCs must work with existing broadcast system for messages
- Database operations should use existing connection pooling
- Movement must respect existing room exit constraints
- Messages should follow existing formatting standards

### Performance Considerations:
- Tick system must not block main event loop
- Database writes should be batched when possible
- NPC responses should have 1-2 second delay for natural feel
- Memory pruning for old interactions (30+ days)

---

**Ready for Phase 2?**
Say "Go" to generate detailed sub-tasks for each parent task above.