# SAMUD Implementation Notes

## Quick Start

1. **Start the server:**
   ```bash
   ./run.sh
   ```

2. **Connect via telnet:**
   ```bash
   telnet localhost 2323
   ```

3. **Run automated tests:**
   ```bash
   python3 test_client.py
   ```

## Architecture Overview

The San Antonio MUD is built with Python 3.10+ using asyncio for concurrent connections.

### Core Modules

- **server.py** - Main asyncio TCP server handling telnet connections
- **auth.py** - Authentication system with bcrypt password hashing
- **database.py** - Async SQLite interface for player persistence
- **world.py** - Room definitions and world graph (7 San Antonio locations)
- **player.py** - Player state management and session handling
- **commands.py** - Command parser and all game commands
- **broadcast.py** - Message distribution system
- **config.py** - Configuration and constants

### Key Features

- **Async Architecture**: Handles multiple concurrent players efficiently
- **Secure Authentication**: Bcrypt password hashing, session management
- **State Persistence**: Player locations saved to SQLite database
- **Rate Limiting**: 5 messages per 10 seconds flood protection
- **Idle Timeout**: 30-minute timeout with 5-minute warning
- **Telnet Protocol**: Proper IAC sequences for echo control

### Room Map
```
        The Pearl
            |
    River Walk North --- Alamo Plaza
            |                |
    River Walk South    Mission San Jose
        /   |   \
Southtown   |   Tower of Americas
```

## Commands

### Navigation
- `look` - Examine current room
- `move <direction>` or `n/s/e/w` - Move between rooms
- `where` - Show current location

### Communication
- `say <message>` - Talk to players in same room
- `shout <message>` - Broadcast to all players

### System
- `who` - List online players
- `help` - Show available commands
- `quit` - Save and disconnect

## Testing

The test_client.py provides automated testing for:
- Single client signup/login
- Multiple concurrent clients
- State persistence across sessions
- All command functionality

## Database Schema

Players table stores:
- username (unique, case-insensitive)
- password_hash (bcrypt)
- current_room_id
- timestamps

Sessions table tracks active connections to prevent duplicate logins.

## Known Issues

- Test client may have timing issues with telnet echo negotiation
- Manual testing via telnet is more reliable than automated tests

## Future Enhancements

The architecture supports easy addition of:
- NPCs (Non-Player Characters)
- Items and inventory system
- Combat mechanics
- More rooms and areas
- Private messaging
- Admin commands