# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

San Antonio MUD (SAMUD) is a text-based multiuser dungeon accessible via telnet. It's built with Python 3.10+ using asyncio for concurrent connections and features San Antonio-themed locations.

## Common Development Commands

### Server Management
```bash
# Start the server (port 2323)
./run.sh

# Start with auto-restart on crash
./run.sh --auto-restart

# Stop running servers
pkill -f "python src/server.py"
```

### Testing
```bash
# Connect as client
telnet localhost 2323

# Run automated tests (if test_client.py exists)
python3 test_client.py
```

### Development Setup
```bash
# Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Async Event Loop Architecture
The server uses Python's asyncio with a central event loop managing concurrent client connections. Each client runs in its own coroutine, with shared state managed through thread-safe data structures.

### Module Responsibilities
- **server.py**: Main TCP server, client connection management, telnet protocol handling
- **auth.py**: Authentication flow (signup/login), bcrypt password hashing, session management
- **database.py**: Async SQLite operations using aiosqlite, connection pooling
- **world.py**: Room graph, location definitions, navigation logic
- **player.py**: Player state, session tracking, activity monitoring
- **commands.py**: Command parsing, execution logic, rate limiting
- **broadcast.py**: Message routing between room/global channels, player targeting
- **config.py**: Central configuration, telnet constants, timeout values

### Database Design
Uses SQLite with three tables:
- **players**: Account data, current room, timestamps
- **sessions**: Active connections, prevents duplicate logins
- **player_stats**: Gameplay metrics (future expansion)

### Room Navigation Graph
Rooms are connected as a graph with bidirectional edges stored in ROOM_EXITS dict. Each room has unique ID, description, and exit mappings.

### Message Flow
1. Client sends input → Server reads from StreamReader
2. Server processes telnet sequences, extracts command
3. Command parser validates and routes to handler
4. Handler executes action, updates state
5. Broadcast system distributes messages to affected clients
6. Server writes to each client's StreamWriter

### Security Features
- Bcrypt password hashing
- Session tokens prevent duplicate logins
- Rate limiting (5 messages per 10 seconds)
- Input sanitization
- Idle timeout (30 minutes)

## Key Implementation Details

### Telnet Protocol
Implements IAC (Interpret As Command) sequences for echo control during password input:
- IAC WILL ECHO: Server controls echoing
- IAC WONT ECHO: Client controls echoing
- IAC DO SGA: Suppress Go-Ahead

### Player State Persistence
Player location saved to database on every room change and disconnect. Sessions table ensures single login per account.

### Broadcast Channels
- **Room**: Messages to players in same room
- **Global**: Messages to all connected players
- **System**: Server announcements to individual players

### Rate Limiting
Sliding window algorithm tracks message timestamps, prevents flooding while allowing burst communication.