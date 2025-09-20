# Product Requirements Document: San Antonio MUD (SAMUD)

## 1. Introduction/Overview

The San Antonio MUD (SAMUD) is a text-based multiplayer online game accessible via telnet that allows players to explore a virtual representation of San Antonio landmarks. Players connect through a telnet client, create accounts, and navigate through interconnected rooms representing iconic San Antonio locations while interacting with other players through chat systems.

## 2. Goals

### Primary Goals
1. **Launch MVP within sprint timeline** - Deliver a functional MUD with core features operational
2. **Support 10+ concurrent users** - Handle multiple simultaneous telnet connections without degradation
3. **Achieve 90% uptime** - Maintain stable server operation during testing period
4. **Enable real-time player interaction** - Players in same room see each other's actions within 1 second

### Secondary Goals
1. **Extensible architecture** - Code structure allows easy addition of new rooms and commands
2. **Intuitive command system** - New players can navigate without external documentation
3. **Authentic San Antonio theme** - Room descriptions capture real landmark characteristics

## 3. User Stories

### As a New Player
- I want to create an account with username/password so I can have a persistent identity
- I want to see available commands when I type 'help' so I can learn the game
- I want clear error messages when I mistype commands so I can correct my input

### As a Returning Player
- I want to log in with my credentials so I can resume where I left off
- I want to spawn in my last visited room so my progress is saved
- I want to see who else is online so I can find other players

### As an Active Player
- I want to move between rooms using cardinal directions so I can explore the world
- I want to chat with players in my room so I can interact locally
- I want to broadcast messages globally so I can communicate with all online players
- I want to see room descriptions and exits so I can navigate effectively

## 4. Functional Requirements

### 4.1 Server Infrastructure
1. Server SHALL listen on port 2323 for telnet connections
2. Server SHALL handle multiple concurrent client connections
3. Server SHALL maintain persistent connection until client disconnects or quits

### 4.2 Authentication System
4. System SHALL provide signup flow requesting username and password
5. System SHALL store passwords using secure hashing (bcrypt or similar)
6. System SHALL provide login flow for existing users
7. System SHALL reject duplicate usernames during signup
8. System SHALL validate username (alphanumeric, 3-20 characters)
9. System SHALL require passwords (minimum 6 characters)

### 4.3 Database Requirements
10. System SHALL use SQLite for data persistence
11. Database SHALL store: username, password_hash, current_room_id, created_at, last_login
12. System SHALL save player location on room change
13. System SHALL save player state on quit command

### 4.4 World Structure
14. World SHALL contain minimum 7 rooms:
    - The Alamo Plaza
    - River Walk North
    - River Walk South
    - The Pearl
    - Tower of the Americas
    - Mission San Jose
    - Southtown
15. Each room SHALL have unique description (50-200 characters)
16. Rooms SHALL connect via cardinal directions (N, S, E, W)
17. Each room SHALL have at least one exit
18. Room connections SHALL be bidirectional by default

### 4.5 Navigation Commands
19. System SHALL support 'look' command showing room description, exits, and players
20. System SHALL support movement via 'move <direction>' command
21. System SHALL support shorthand movement (n, s, e, w)
22. System SHALL display new room description after successful movement
23. System SHALL show error for invalid exit attempts
24. System SHALL support 'where' command showing current room name

### 4.6 Communication System
25. System SHALL support 'say <message>' for room-specific chat
26. Room chat SHALL display as "[Room] username: message"
27. System SHALL support 'shout <message>' for global chat
28. Global chat SHALL display as "[Global] username: message"
29. Messages SHALL be delivered to recipients within 1 second
30. System SHALL NOT store chat history

### 4.7 Player Awareness
31. System SHALL support 'who' command listing all online players
32. 'look' command SHALL list players in current room
33. System SHALL broadcast player entry to room occupants
34. System SHALL broadcast player exit from room to occupants
35. System SHALL immediately remove player from room on disconnect

### 4.8 System Commands
36. System SHALL support 'help' command listing all available commands
37. System SHALL support 'quit' command for graceful disconnect
38. 'quit' SHALL save player state before disconnecting

### 4.9 Error Handling
39. System SHALL provide friendly error for unrecognized commands
40. Error messages SHALL suggest similar valid commands when possible
41. System SHALL handle unexpected disconnections gracefully
42. System SHALL prevent SQL injection through parameterized queries

## 5. Non-Goals (Out of Scope for MVP)

The following features are explicitly excluded from MVP scope:

1. **NPCs (Non-Player Characters)** - No computer-controlled entities
2. **Combat System** - No fighting or health mechanics
3. **Inventory/Items** - No object pickup or management
4. **Private Messaging** - No whisper or tell commands
5. **Character Customization** - No player descriptions or attributes
6. **Room Persistence** - No dynamic room states or modifications
7. **Admin Commands** - No moderation or administrative tools
8. **Web Interface** - Telnet only, no HTTP server
9. **Chat History** - No message persistence or replay
10. **Email Verification** - No email-based account features
11. **Password Recovery** - No reset mechanism
12. **Rate Limiting** - No spam prevention beyond basic measures
13. **Profanity Filtering** - No content moderation

## 6. Design Considerations

### User Interface
- All output formatted for 80-column telnet display
- Clear visual separation between game output and user input
- Consistent prompt character (">") for command entry
- Room descriptions written in second person ("You see...")

### Command Syntax
- Commands case-insensitive
- Single-word commands preferred
- Clear parameter separation with spaces
- No command aliases in MVP (except movement shortcuts)

## 7. Technical Considerations

### Technology Stack
- **Language**: To be determined (Python, Node.js, or Go recommended)
- **Database**: SQLite3
- **Protocol**: Raw telnet (no SSH)
- **Deployment**: Single process application

### Architecture Patterns
- Event-driven for handling multiple connections
- Command pattern for processing user input
- Repository pattern for database access
- Singleton for world/room management

### Security
- Bcrypt for password hashing
- Parameterized queries for SQL
- Input validation on all commands
- Connection timeout after 30 minutes idle

### Performance
- Non-blocking I/O for connection handling
- Connection pooling for database
- In-memory room graph for navigation
- Lazy loading of room descriptions

## 8. Success Metrics

### Launch Criteria (Must Have)
- [ ] All 7 rooms accessible and connected
- [ ] All required commands functional
- [ ] 3+ players can connect simultaneously
- [ ] Player state persists between sessions
- [ ] No crashes during 1-hour test session

### Success Indicators (Nice to Have)
- Average session length > 10 minutes
- 80% of players use chat features
- 90% of players explore 3+ rooms
- < 100ms response time for commands
- Zero data loss during normal operation

## 9. Open Questions

1. **Hosting**: Where will the server be deployed? (Local, VPS, Cloud)
2. **Monitoring**: What logging/metrics are needed for debugging?
3. **Room Descriptions**: Who writes the San Antonio-themed content?
4. **Connection Limits**: Maximum concurrent connections to support?
5. **Timeout Policy**: Disconnect idle players after X minutes?
6. **Character Encoding**: UTF-8 support or ASCII only?
7. **Line Endings**: How to handle different client line endings (CRLF vs LF)?
8. **Testing Strategy**: Unit tests, integration tests, or manual testing only?
9. **Backup Strategy**: How often to backup the SQLite database?
10. **Future Phases**: Priority order for stretch goals post-MVP?

## 10. Acceptance Criteria

The MVP is considered complete when:

1. A user can telnet to localhost:2323 and receive welcome message
2. A new user can sign up with username/password
3. An existing user can log in with credentials
4. A logged-in user can navigate all 7 rooms
5. Multiple users in same room can see each other via 'look'
6. Users can communicate via 'say' (room) and 'shout' (global)
7. User location persists after quit and re-login
8. All required commands work as specified
9. Server remains stable with 5 concurrent users for 30 minutes
10. Code is organized for easy room/command additions

---

*Document Version: 1.0*
*Created: 2025-09-20*
*Status: Draft - Pending Review*