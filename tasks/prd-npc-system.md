# Product Requirements Document: NPC System

**Feature Name:** Non-Player Character (NPC) System
**Date:** 2025-09-20
**Status:** Draft

## Introduction/Overview

The NPC System introduces lifelike non-player characters to the San Antonio MUD, creating a more immersive and dynamic world. NPCs will populate various San Antonio landmarks with culturally authentic characters that can interact with players, move between locations, perform ambient actions, and remember player interactions. This system will make the world feel alive and provide players with richer gameplay experiences through San Antonio-themed character interactions.

## Goals

1. **Populate the World**: Add 8+ thematic NPCs across all major San Antonio locations to create a living, breathing environment
2. **Enable Dynamic Interactions**: Allow players to interact with NPCs through ambient keyword responses and contextual reactions
3. **Implement Autonomous Movement**: Create a tick system where NPCs move between rooms based on schedules and time of day
4. **Provide Persistent State**: Maintain NPC locations and interaction history across server restarts
5. **Support Configuration-Based Design**: Enable easy NPC creation and modification through YAML configuration files
6. **Enhance Immersion**: Use NPCs to provide local flavor, historical information, and cultural authenticity

## User Stories

### As a Player
1. I want to see NPCs in various rooms so the world feels populated and alive
2. I want NPCs to respond when I mention keywords in my messages so interactions feel natural
3. I want to see NPCs moving between rooms so the world feels dynamic
4. I want NPCs to remember our previous interactions so relationships can develop
5. I want to see NPCs performing ambient actions so they feel like real inhabitants
6. I want NPCs to react to my arrival and actions so I feel acknowledged

### As a Game Administrator
1. I want to configure NPCs through YAML files so I can easily add or modify characters
2. I want to define NPC movement patterns and schedules so each character has unique behaviors
3. I want to set starting locations in room configurations so NPCs spawn appropriately
4. I want NPC state to persist across restarts so the world maintains continuity

### As a Developer
1. I want NPCs to integrate with existing systems (rooms, players, commands) seamlessly
2. I want clear separation between NPC definition and runtime behavior
3. I want the tick system to be performant and not impact player experience
4. I want NPC state changes to be properly synchronized across async operations

## Functional Requirements

### NPC Definition and Configuration

1. **NPC Configuration Directory**: Create `/data/npcs/` directory structure for NPC definitions
2. **YAML Configuration Files**: Each NPC defined in individual YAML files with:
   - Basic properties (id, name, description, personality)
   - Keyword responses (mapping of trigger words to responses)
   - Movement patterns (allowed rooms, movement probability, schedule)
   - Ambient actions (list of random actions/emotes)
   - Initial dialogue/greeting messages
   - Memory settings (what to remember about players)

3. **Room Integration**: Room YAML files include `npcs` field listing NPC IDs that start there:
   ```yaml
   rooms:
     alamo_plaza:
       npcs:
         - tourist_guide
         - photographer
   ```

### NPC Types

4. **Tourist at the Alamo**: Provides historical facts, takes photos, asks about Texas history
5. **Mariachi Band**: Travels between River Walk locations, plays music, accepts song requests
6. **Food Vendor at The Pearl**: Sells tacos (descriptive only), talks about local cuisine
7. **Tour Guide at Tower of the Americas**: Describes city views, shares local trivia
8. **Priest/Friar at Mission San Jose**: Offers blessings, shares mission history
9. **Artist in Southtown**: Discusses art scene, describes current work
10. **Boat Captain on River Walk**: Tells river stories, announces boat arrivals/departures
11. **Additional NPCs**: Local residents, shopkeepers, street performers as configured

### Interaction System

12. **Keyword Detection**: NPCs scan player messages for trigger words and respond appropriately
13. **Response Timing**: NPCs respond 1-2 seconds after player message for natural feel
14. **Contextual Awareness**: NPCs acknowledge when players enter/leave rooms
15. **Ambient Actions**: NPCs perform random actions every 30-60 seconds when players present
16. **Response Formatting**: NPC messages formatted as: `[NPC] <name>: <message>`

### Movement System (Tick System)

17. **Variable Tick Intervals**: Different NPCs move at different rates (30 seconds to 5 minutes)
18. **Time-Based Schedules**: NPCs follow morning/afternoon/evening location patterns
19. **Movement Broadcasts**: Players see messages when NPCs enter/leave:
    - `The mariachi band wanders south toward River Walk South.`
    - `A tourist guide arrives from the north, leading a small group.`
20. **Smart Movement**: NPCs only move if no players are actively interacting with them
21. **Path Constraints**: NPCs only move between predefined allowed rooms

### Memory and Persistence

22. **Player Recognition**: NPCs remember player names and previous interactions
23. **Interaction History**: Track last interaction timestamp, conversation topics
24. **Greeting Variations**: Different greetings for first-time vs returning players
25. **Database Storage**: NPC current location and memory stored in SQLite:
    ```sql
    CREATE TABLE npc_state (
        npc_id TEXT PRIMARY KEY,
        current_room TEXT,
        last_moved TIMESTAMP,
        state_data TEXT  -- JSON for flexible data
    );

    CREATE TABLE npc_memory (
        npc_id TEXT,
        player_name TEXT,
        last_interaction TIMESTAMP,
        interaction_count INTEGER,
        memory_data TEXT,  -- JSON for flexible memories
        PRIMARY KEY (npc_id, player_name)
    );
    ```

### Edge Case Handling

26. **Concurrent Interactions**: When multiple players interact simultaneously, NPC responds to all in room
27. **Mid-Conversation Movement**: NPCs announce departure but complete current response before leaving
28. **Server Restart**: NPCs restore to last saved location and maintain memories
29. **Missing NPCs**: If NPC location invalid after restart, return to initial spawn room
30. **Room Capacity**: No limit on NPCs per room, but consider performance

## Non-Goals (Out of Scope)

1. **Combat System**: NPCs cannot fight or be attacked
2. **Complex AI**: No learning algorithms or advanced natural language processing
3. **Voice Generation**: No dynamic personality or dialogue generation
4. **NPC Inventory**: NPCs don't carry or manage items (descriptions only)
5. **Romantic Relationships**: No dating or relationship mechanics
6. **Quest System**: NPCs don't assign or track quests (future feature)
7. **Trading System**: No actual item exchange mechanics (descriptive only)
8. **NPC-to-NPC Interaction**: NPCs don't interact with each other

## Technical Considerations

### Architecture
- **NPC Manager Module** (`src/npcs.py`): Central system for NPC lifecycle management
- **NPC Class**: Individual NPC instances with state and behavior
- **Tick Scheduler**: Async task managing NPC movement and actions
- **Memory Manager**: Handles persistence and retrieval of NPC memories
- **YAML Loader**: Parses and validates NPC configuration files

### Performance
- NPCs should not impact server response time (< 50ms overhead)
- Tick system uses async scheduling to prevent blocking
- Database writes batched during quiet periods
- Memory pruning for interactions older than 30 days

### Integration Points
- **Room System**: NPCs listed in room's "who's here" display
- **Broadcast System**: NPC messages use existing broadcast channels
- **Command Parser**: No new commands needed (uses existing `say` detection)
- **Database**: Extends existing schema with NPC tables

### Configuration Schema
```yaml
# /data/npcs/mariachi_band.yml
npc:
  id: mariachi_band
  name: Mariachi Los Gallos
  description: A lively mariachi band in traditional charro outfits

  dialogue:
    greeting_new: "¡Hola, amigo! Welcome to San Antonio!"
    greeting_return: "¡Ay, {player}! Good to see you again!"
    farewell: "¡Hasta la vista!"

  keywords:
    music|song|play: "We know all the classics! Any requests?"
    taco|food: "The best tacos are at The Pearl, amigo!"
    river|water: "The River Walk is beautiful, especially at sunset."

  movement:
    allowed_rooms:
      - river_walk_north
      - river_walk_south
      - the_pearl
    tick_interval: 120  # seconds
    schedule:
      morning: river_walk_north
      afternoon: the_pearl
      evening: river_walk_south

  ambient_actions:
    - "strums their guitars in harmony"
    - "adjusts their sombreros"
    - "begins playing 'Cielito Lindo'"
    - "takes a quick water break between songs"
```

## Design Considerations

### User Experience
- NPC responses should feel natural and contextual
- Movement messages should be descriptive and immersive
- NPCs should acknowledge player actions without being intrusive
- Response delays (1-2 seconds) create conversational flow

### Localization
- NPCs use regional dialect and Spanish phrases appropriately
- Cultural authenticity in character behaviors and responses
- Historical accuracy for location-specific information

## Success Metrics

1. **Engagement**: 80% of players interact with at least one NPC per session
2. **Immersion**: NPCs successfully create "living world" feeling (player feedback)
3. **Performance**: NPC system adds < 5% server resource overhead
4. **Stability**: Zero server crashes related to NPC system in first week
5. **Content**: All 8+ planned NPCs implemented and active
6. **Persistence**: NPC state correctly maintained across 100% of server restarts
7. **Natural Interaction**: Players report NPC interactions feel contextual and appropriate

## Open Questions

1. Should NPCs have different response personalities based on time of day (grumpy in morning, cheerful at noon)?
2. Should certain NPCs only appear during specific times (e.g., mariachi only in evening)?
3. Should NPCs react differently based on number of players in room?
4. How should NPCs handle player emotes (`/emote` command when implemented)?
5. Should some NPCs be "unique" (only one instance) vs "generic" (multiple tourists)?
6. Should NPCs have special responses during holidays or special events?
7. Should there be a limit on how often the same NPC responds to prevent spam?
8. Should NPCs remember negative interactions differently than positive ones?

## Implementation Priority

### Phase 1: Core System
1. NPC configuration loader
2. Basic NPC class with keyword responses
3. Room integration (display NPCs)
4. Simple keyword detection and response

### Phase 2: Movement and Persistence
1. Tick system implementation
2. NPC movement between rooms
3. Database schema for NPC state
4. State restoration on server restart

### Phase 3: Advanced Features
1. Time-based schedules
2. Player memory system
3. Ambient actions
4. Contextual reactions

### Phase 4: Content Creation
1. Create all 8+ NPC configurations
2. Write dialogue and responses
3. Define movement patterns
4. Test and refine interactions

---

*This PRD is ready for implementation by the development team. All requirements are explicit enough for a junior developer to understand and implement with appropriate technical guidance.*