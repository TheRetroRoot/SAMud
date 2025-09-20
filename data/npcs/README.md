# NPC Configuration Guide

This directory contains YAML configuration files for all NPCs in the San Antonio MUD.

## File Structure

Each NPC is defined in its own YAML file with the naming convention: `{npc_id}.yml`

## Quick Start

1. Copy `npc_schema_template.yml` to create a new NPC
2. Rename the file to match your NPC's ID (e.g., `tourist_guide.yml`)
3. Fill in the required and optional fields
4. Validate your configuration: `python3 validate_npc.py your_npc.yml`
5. Add the NPC to the appropriate room's `npcs` list in `/data/rooms/*.yml`

## Required Fields

- **id**: Unique identifier (snake_case)
- **name**: Display name shown to players
- **description**: Appearance description for room display

## Optional Sections

### Dialogue
Defines NPC conversation responses:
- `greeting_new`: First-time player greeting
- `greeting_return`: Returning player greeting (supports `{player}` placeholder)
- `farewell`: NPC departure message
- `player_departure`: Response when players leave
- `player_arrival`: Response when players enter

### Keywords
Pattern-based responses to player messages:
```yaml
keywords:
  "hello|hi|hey": "Greetings, traveler!"
  "help|assist": "How can I help you?"
```

### Movement
Controls NPC movement between rooms:
- `allowed_rooms`: List of room IDs the NPC can visit
- `tick_interval`: Seconds between movement checks (default: 120)
- `movement_probability`: Chance of moving on tick (0.0-1.0)
- `schedule`: Time-based locations (morning/afternoon/evening/night)

### Ambient Actions
Random actions performed when players are present:
```yaml
ambient_actions:
  - "adjusts their hat"
  - "checks the time"
  - "hums a tune"
```

### Memory
Controls what NPCs remember about players:
- `remember_names`: Track player names
- `remember_topics`: Track conversation topics
- `remember_visit_count`: Count interactions
- `memory_duration`: Days to retain memories (default: 30)

## Validation

Run the validator to check your NPC configuration:
```bash
# Validate specific file
python3 validate_npc.py mariachi_band.yml

# Validate all NPC files
python3 validate_npc.py
```

## Best Practices

1. **Use descriptive IDs**: `mariachi_band` not `npc1`
2. **Write immersive descriptions**: Focus on appearance and demeanor
3. **Create varied dialogue**: Mix formal and casual responses
4. **Add cultural authenticity**: Use appropriate Spanish phrases for San Antonio NPCs
5. **Balance movement**: Don't make NPCs move too frequently (annoys players)
6. **Test keyword patterns**: Ensure common variations are covered
7. **Keep ambient actions subtle**: Avoid spammy or distracting behaviors

## Example NPCs

See the following files for well-structured examples:
- `tourist_guide.yml` - Basic stationary NPC with helpful responses
- `mariachi_band.yml` - Mobile NPC with schedule-based movement
- `food_vendor.yml` - Commerce-focused NPC with product descriptions

## Room Integration

After creating an NPC, add it to a room's spawn list:

```yaml
# In /data/rooms/historic.yml
rooms:
  alamo_plaza:
    npcs:
      - tourist_guide
      - photographer
```

NPCs will spawn in their designated rooms on server start and restore their positions from the database after restarts.