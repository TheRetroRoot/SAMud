# Implementation Tasks: San Antonio MUD (SAMUD)

## Technology Decision
**Recommended Stack**: Python 3.10+ with asyncio
- **Rationale**: Built-in async support, simple telnet protocol handling, SQLite integration, bcrypt available

## Files to Create/Modify

### Core Application Files
- `src/server.py` - Main telnet server and connection handler ✅
- `src/auth.py` - Authentication system (signup/login) ✅
- `src/database.py` - SQLite database interface and models ✅
- `src/world.py` - Room definitions and world graph ✅
- `src/player.py` - Player state management and session handling ✅
- `src/commands.py` - Command parser and executor ✅
- `src/broadcast.py` - Message broadcasting system ✅
- `src/config.py` - Configuration constants (port, database path, etc.) ✅

### Supporting Files
- `requirements.txt` - Python dependencies ✅
- `schema.sql` - Database schema definition ✅
- `.env.example` - Environment variables template ✅
- `.gitignore` - Git ignore patterns ✅
- `run.sh` - Start script for the server ✅
- `test_client.py` - Simple telnet test client for development ✅

### Documentation
- `tasks/tasks-prd-samud.md` - This task list (current file)
- `IMPLEMENTATION.md` - Technical implementation notes

## Implementation Tasks with Sub-Tasks

### 1.0 Project Setup and Infrastructure
*Initialize Python project structure with dependencies and configuration*

- [x] **1.1 Create project structure**
  - [x] 1.1.1 Create `src/` directory for source code
  - [x] 1.1.2 Create `tests/` directory for test files
  - [x] 1.1.3 Create `data/` directory for SQLite database
  - [x] 1.1.4 Initialize git repository (if not already)

- [x] **1.2 Setup Python environment**
  - [x] 1.2.1 Create `requirements.txt` with dependencies: `bcrypt`, `aiosqlite`, `python-dotenv`
  - [x] 1.2.2 Create `.env.example` with: `PORT=2323`, `DB_PATH=data/samud.db`, `IDLE_TIMEOUT=1800`
  - [x] 1.2.3 Create `.gitignore` including: `*.pyc`, `__pycache__/`, `.env`, `data/*.db`
  - [x] 1.2.4 Create virtual environment and install dependencies

- [x] **1.3 Create configuration module**
  - [x] 1.3.1 Create `src/config.py` with constants from environment variables
  - [x] 1.3.2 Define server settings (port, buffer size, encoding)
  - [x] 1.3.3 Define game constants (room IDs, command list)
  - [x] 1.3.4 Add logging configuration

### 2.0 Database Layer Implementation
*Create SQLite database schema and data access layer*

- [x] **2.1 Define database schema**
  - [x] 2.1.1 Create `schema.sql` with players table (id, username, password_hash, current_room_id, created_at, last_login)
  - [x] 2.1.2 Add unique constraint on username
  - [x] 2.1.3 Add index on username for login performance
  - [x] 2.1.4 Set default room to 'alamo_plaza' for new players

- [x] **2.2 Create database module**
  - [x] 2.2.1 Create `src/database.py` with async SQLite connection manager
  - [x] 2.2.2 Implement `init_database()` to create tables from schema
  - [x] 2.2.3 Implement `get_connection()` for connection pooling
  - [x] 2.2.4 Add database initialization on server start

- [x] **2.3 Implement player data access**
  - [x] 2.3.1 Create `create_player(username, password_hash)` function
  - [x] 2.3.2 Create `get_player_by_username(username)` function
  - [x] 2.3.3 Create `update_player_room(player_id, room_id)` function
  - [x] 2.3.4 Create `update_last_login(player_id)` function

### 3.0 Telnet Server Foundation
*Implement async telnet server with connection handling*

- [x] **3.1 Create telnet server base**
  - [x] 3.1.1 Create `src/server.py` with asyncio TCP server
  - [x] 3.1.2 Implement `start_server()` listening on port 2323
  - [x] 3.1.3 Add connection accept handler
  - [x] 3.1.4 Implement graceful shutdown with signal handlers

- [x] **3.2 Handle client connections**
  - [x] 3.2.1 Create `Client` class to wrap connection state
  - [x] 3.2.2 Implement `send_to_client(client, message)` with encoding
  - [x] 3.2.3 Implement `read_from_client(client)` with line buffering
  - [x] 3.2.4 Add connection tracking dictionary

- [x] **3.3 Implement telnet protocol basics**
  - [x] 3.3.1 Send telnet IAC sequences for character mode
  - [x] 3.3.2 Handle telnet negotiation (ignore complex options)
  - [x] 3.3.3 Strip telnet commands from input
  - [x] 3.3.4 Handle CR/LF line endings from different clients

### 4.0 Authentication System
*Build signup/login flows with password hashing*

- [x] **4.1 Create authentication module**
  - [x] 4.1.1 Create `src/auth.py` with bcrypt integration
  - [x] 4.1.2 Implement `hash_password(password)` function
  - [x] 4.1.3 Implement `verify_password(password, hash)` function
  - [x] 4.1.4 Add input validation helpers

- [x] **4.2 Implement signup flow**
  - [x] 4.2.1 Create `handle_signup(client)` function
  - [x] 4.2.2 Prompt for username (validate: alphanumeric, 3-20 chars)
  - [x] 4.2.3 Check for existing username in database
  - [x] 4.2.4 Prompt for password (validate: min 6 chars)
  - [x] 4.2.5 Create player record and auto-login

- [x] **4.3 Implement login flow**
  - [x] 4.3.1 Create `handle_login(client)` function
  - [x] 4.3.2 Prompt for username
  - [x] 4.3.3 Prompt for password (mask input with asterisks)
  - [x] 4.3.4 Verify credentials and load player state
  - [x] 4.3.5 Update last_login timestamp

- [x] **4.4 Create session management**
  - [x] 4.4.1 Implement welcome screen with login/signup options
  - [x] 4.4.2 Track authenticated state in Client object
  - [x] 4.4.3 Prevent duplicate logins for same username
  - [x] 4.4.4 Handle authentication timeout (30 seconds)

### 5.0 World and Room System
*Define San Antonio rooms and navigation graph*

- [x] **5.1 Create world module**
  - [x] 5.1.1 Create `src/world.py` with Room class
  - [x] 5.1.2 Define Room properties (id, name, description, exits)
  - [x] 5.1.3 Implement room graph as singleton
  - [x] 5.1.4 Add helper to get room by ID

- [x] **5.2 Define San Antonio rooms**
  - [x] 5.2.1 Create Alamo Plaza (exits: east to River Walk North, south to Mission San Jose)
  - [x] 5.2.2 Create River Walk North (exits: west to Alamo, south to River Walk South, north to Pearl)
  - [x] 5.2.3 Create River Walk South (exits: north to River Walk North, east to Tower, west to Southtown)
  - [x] 5.2.4 Create The Pearl (exits: south to River Walk North)
  - [x] 5.2.5 Create Tower of the Americas (exits: west to River Walk South)
  - [x] 5.2.6 Create Mission San Jose (exits: north to Alamo Plaza)
  - [x] 5.2.7 Create Southtown (exits: east to River Walk South)

- [x] **5.3 Write room descriptions**
  - [x] 5.3.1 Alamo: "Stone walls surround you. Tourists move in and out of the historic courtyard."
  - [x] 5.3.2 River Walk North: "The water glistens as colorful barges float past. Cafes line both banks."
  - [x] 5.3.3 River Walk South: "Music drifts from restaurants. Cypress trees shade the walkway."
  - [x] 5.3.4 Pearl: "The old brewery buzzes with activity. Food trucks and shops fill the plaza."
  - [x] 5.3.5 Tower: "The needle pierces the sky at 750 feet. The city spreads out below."
  - [x] 5.3.6 Mission: "The limestone church stands serene. The rose window catches the light."
  - [x] 5.3.7 Southtown: "Art galleries and vintage shops line the street. Murals cover the walls."

- [x] **5.4 Validate room connections**
  - [x] 5.4.1 Verify all exits are bidirectional
  - [x] 5.4.2 Ensure every room is reachable
  - [x] 5.4.3 Test cardinal direction consistency
  - [x] 5.4.4 Create room graph visualization (optional)

### 6.0 Player Session Management
*Handle player state, presence, and persistence*

- [x] **6.1 Create player module**
  - [x] 6.1.1 Create `src/player.py` with Player class
  - [x] 6.1.2 Track player properties (id, username, current_room, client)
  - [x] 6.1.3 Maintain active_players dictionary
  - [x] 6.1.4 Add methods for player movement

- [x] **6.2 Implement player presence**
  - [x] 6.2.1 Add player to room on login/movement
  - [x] 6.2.2 Remove player from room on logout/movement
  - [x] 6.2.3 Track players per room in world module
  - [x] 6.2.4 Implement `get_players_in_room(room_id)` function

- [x] **6.3 Handle player state persistence**
  - [x] 6.3.1 Load player's last room on login
  - [x] 6.3.2 Save room changes to database immediately
  - [x] 6.3.3 Save state on quit command
  - [x] 6.3.4 Handle cleanup on unexpected disconnect

- [x] **6.4 Implement idle timeout**
  - [x] 6.4.1 Track last activity timestamp per client
  - [x] 6.4.2 Create periodic idle check task
  - [x] 6.4.3 Warn player at 25 minutes idle
  - [x] 6.4.4 Disconnect at 30 minutes idle

### 7.0 Command Processing System
*Implement command parser and all required commands*

- [x] **7.1 Create command parser**
  - [x] 7.1.1 Create `src/commands.py` with command registry
  - [x] 7.1.2 Implement `parse_command(input)` to split command/args
  - [x] 7.1.3 Make commands case-insensitive
  - [x] 7.1.4 Add command validation and sanitization

- [x] **7.2 Implement navigation commands**
  - [x] 7.2.1 `look` - Show room description, exits, and players
  - [x] 7.2.2 `move <direction>` - Move to adjacent room
  - [x] 7.2.3 `n/s/e/w` - Shorthand movement commands
  - [x] 7.2.4 `where` - Show current room name

- [x] **7.3 Implement communication commands**
  - [x] 7.3.1 `say <message>` - Send to room with "[Room] username: message"
  - [x] 7.3.2 `shout <message>` - Send globally with "[Global] username: message"
  - [x] 7.3.3 Add 250 character limit for messages
  - [x] 7.3.4 Strip/escape special characters

- [x] **7.4 Implement system commands**
  - [x] 7.4.1 `who` - List all online players
  - [x] 7.4.2 `help` - Show all available commands with descriptions
  - [x] 7.4.3 `quit` - Save and disconnect gracefully
  - [x] 7.4.4 Add command aliases (e.g., 'exit' for 'quit')

### 8.0 Communication System
*Build room and global chat with broadcasting*

- [x] **8.1 Create broadcast module**
  - [x] 8.1.1 Create `src/broadcast.py` for message distribution
  - [x] 8.1.2 Implement `broadcast_to_room(room_id, message, exclude_player)`
  - [x] 8.1.3 Implement `broadcast_to_all(message, exclude_player)`
  - [x] 8.1.4 Add async message queue for performance

- [x] **8.2 Implement room notifications**
  - [x] 8.2.1 Broadcast when player enters room: "PlayerName has arrived from the [direction]"
  - [x] 8.2.2 Broadcast when player leaves room: "PlayerName heads [direction]"
  - [x] 8.2.3 Show entry message to arriving player
  - [x] 8.2.4 Handle special cases (login/logout vs movement)

- [x] **8.3 Format message output**
  - [x] 8.3.1 Ensure 80-column width formatting
  - [x] 8.3.2 Add timestamps to messages (optional)
  - [x] 8.3.3 Color code message types (if client supports)
  - [x] 8.3.4 Add line wrapping for long messages

- [x] **8.4 Handle rapid messaging**
  - [x] 8.4.1 Add basic flood protection (5 messages per 10 seconds)
  - [x] 8.4.2 Queue messages during high load
  - [x] 8.4.3 Ensure message order preservation
  - [x] 8.4.4 Drop messages gracefully if client disconnected

### 9.0 Error Handling and Edge Cases
*Add graceful error handling and disconnection management*

- [x] **9.1 Command error handling**
  - [x] 9.1.1 Unknown command: "I don't understand 'xyz'. Type 'help' for commands."
  - [x] 9.1.2 Invalid direction: "You can't go that way. Exits are: [list]"
  - [x] 9.1.3 Missing arguments: "Usage: say <message>"
  - [x] 9.1.4 Suggest similar commands for typos

- [x] **9.2 Connection error handling**
  - [x] 9.2.1 Handle sudden client disconnect (broken pipe)
  - [x] 9.2.2 Clean up player from room on disconnect
  - [x] 9.2.3 Broadcast disconnect to room: "PlayerName has disconnected"
  - [x] 9.2.4 Save player state before cleanup

- [x] **9.3 Database error handling**
  - [x] 9.3.1 Handle database locked errors with retry
  - [x] 9.3.2 Validate all SQL inputs (prevent injection)
  - [x] 9.3.3 Handle constraint violations gracefully
  - [x] 9.3.4 Add database connection retry logic

- [x] **9.4 Input validation**
  - [x] 9.4.1 Limit input line length to 1024 chars
  - [x] 9.4.2 Filter control characters from input
  - [x] 9.4.3 Handle Unicode properly
  - [x] 9.4.4 Prevent empty commands

### 10.0 Testing and Validation
*Verify all acceptance criteria and multi-user scenarios*

- [x] **10.1 Create test client**
  - [x] 10.1.1 Create `test_client.py` for automated testing
  - [x] 10.1.2 Implement scripted command sequences
  - [x] 10.1.3 Add multi-client test scenarios
  - [x] 10.1.4 Verify expected responses

- [x] **10.2 Test authentication flows**
  - [x] 10.2.1 Test successful signup with valid data
  - [x] 10.2.2 Test duplicate username rejection
  - [x] 10.2.3 Test login with correct/incorrect credentials
  - [x] 10.2.4 Test password requirements enforcement

- [x] **10.3 Test multi-user scenarios**
  - [x] 10.3.1 Test 5 concurrent connections
  - [x] 10.3.2 Test players seeing each other in rooms
  - [x] 10.3.3 Test room and global chat delivery
  - [x] 10.3.4 Test movement notifications

- [x] **10.4 Acceptance criteria validation**
  - [x] 10.4.1 ✓ Telnet to localhost:2323 shows welcome
  - [x] 10.4.2 ✓ New user can sign up
  - [x] 10.4.3 ✓ Existing user can log in
  - [x] 10.4.4 ✓ Navigate all 7 rooms
  - [x] 10.4.5 ✓ Multiple users see each other
  - [x] 10.4.6 ✓ Chat commands work
  - [x] 10.4.7 ✓ Location persists after reconnect
  - [x] 10.4.8 ✓ All commands function
  - [x] 10.4.9 ✓ 30-minute stability test
  - [x] 10.4.10 ✓ Code organized for extensions

- [x] **10.5 Performance testing**
  - [x] 10.5.1 Measure command response time (<100ms)
  - [x] 10.5.2 Test with 10+ concurrent users
  - [x] 10.5.3 Monitor memory usage over time
  - [x] 10.5.4 Verify no memory leaks

- [x] **10.6 Create run script**
  - [x] 10.6.1 Create `run.sh` to start server
  - [x] 10.6.2 Add environment variable checks
  - [x] 10.6.3 Create database if not exists
  - [x] 10.6.4 Add restart on crash option

---

## Completion Checklist

When all tasks are complete, verify:
- [ ] Server runs on port 2323
- [ ] All 7 San Antonio rooms are explorable
- [ ] Authentication works (signup/login)
- [ ] Commands work as specified
- [ ] Multiple players interact correctly
- [ ] State persists across sessions
- [ ] Error messages are helpful
- [ ] Code is modular and extensible

## Notes for Implementation

1. **Start with tasks 1-3** to get basic server running
2. **Test frequently** with telnet client during development
3. **Use async/await** throughout for scalability
4. **Keep functions small** and focused on one task
5. **Log everything** during development for debugging

---

*Task List Version: 2.0 - Detailed Sub-tasks*
*Generated: 2025-09-20*