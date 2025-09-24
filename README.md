# Project: San Antonio Multiuser Dungeon (MUD)

## Goal
Create a simple text-based Multiuser Dungeon that people can connect to using telnet.  
The world should be San Antonio themed, with recognizable locations like the Alamo, the River Walk, and the Tower of the Americas.

---

## Requirements

### Core Features
- Runs as a telnet-accessible server on port 2323  
- Players can **sign up** and **log in**  
- World contains at least **six rooms** based on San Antonio landmarks  
- Player state (last room) is saved in **SQLite**  
- Multiuser: players should see and interact with each other if they’re in the same room  
- Supports both **room chat** and **global chat**  

### Minimum Commands
- `look` — shows the room description, exits, and who is there  
- `say <message>` — sends a message to everyone in the **same room**  
- `shout <message>` — sends a message to **all players in the world**  
- `move <exit>` or shortcuts like `n`, `s`, `e`, `w` — moves to another room  
- `who` — shows who is online  
- `where` — shows your current room  
- `help` — lists available commands  
- `quit` — saves progress and disconnects  

### The World (minimum set)
- **The Alamo Plaza**  
- **River Walk North**  
- **River Walk South**  
- **The Pearl**  
- **Tower of the Americas**  
- **Mission San Jose**  
- **Southtown**  

Each room should have a short description and at least one exit leading to another room.

---

## Configuration Tool

SAMUD includes a graphical configuration tool for managing rooms and NPCs:

```bash
# Launch the configuration tool
./run.sh config

# Or directly
python3 config_tool.py
```

**Features:**
- Visual room graph with drag-and-drop
- Complete NPC editor with dialogue, movement, and memory settings
- Validation system to check for errors
- Automatic backups when saving

See [CONFIG_TOOL_README.md](CONFIG_TOOL_README.md) for detailed documentation.

## Stretch Goals

1. **NPCs (Non-Player Characters)**  ✓ COMPLETED
   - Create simple NPCs that live in certain rooms
   - NPCs can respond to keywords (e.g. an NPC at The Pearl might talk about tacos if you mention tacos)

2. **NPC Interactions**  ✓ COMPLETED
   - Allow `talk <npc>` for basic dialogue
   - Support simple scripted responses or branching text  

3. **Tick System**  
   - Add a timed “tick” (e.g. every 30 seconds)  
   - NPCs move between rooms on ticks  
   - NPC actions should be broadcast to players in the room  
   - Example: `The mariachi band wanders south toward the River Walk South.`  

4. **Extra Commands**  
   - `emote <text>` — describe an action  
   - `whisper <player> <message>` — send a private message  
   - `get` / `drop` — pick up or drop items in rooms  

---

## Session Structure
- Everyone works on **the same project and requirements**  
- Each participant uses their AI programming assistant to implement the system  
- Work is divided into **sessions** with roundtable check-ins every 20 minutes to share strategies and results  

---

## Example Interaction

```text
$ telnet localhost 2323
Trying 127.0.0.1...
Connected to localhost.
Welcome to the San Antonio MUD
Type `login` or `signup` to begin

> signup
Choose a username:
> ATC
Choose a password:
> ********
Account created. Welcome, ATC!

You appear at The Alamo Plaza
Stone walls surround you. Tourists move in and out of the courtyard.
Exits: east, south
Players here: none

> say Hello, anyone here?
[Room] ATC: Hello, anyone here?

> shout Hola San Antonio!
[Global] ATC: Hola San Antonio!
[Global] maria: Welcome to the River Walk!

> e
River Walk North
The water glistens as barges float past. Cafes line the banks.
Exits: west, south, north
Players here: none

> who
Online: ATC, maria

> say The view here is amazing
[Room] ATC: The view here is amazing

[Global] maria: Meet me at the Pearl!

> n
The Pearl
The old brewery is alive with music and food. Families gather in the plaza.
Exits: south
Players here: maria

> say I found you!
[Room] ATC: I found you!
[Room] maria: Bienvenidos!

> quit
Goodbye, ATC. Your progress has been saved.
Connection closed by foreign host.
