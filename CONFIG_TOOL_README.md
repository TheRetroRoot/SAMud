# SAMUD Configuration Tool

A cross-platform graphical editor for San Antonio MUD room and NPC configurations. Works on Windows, Linux, and macOS.

## Features

### Room Editor
- **Visual Room Graph**: Drag-and-drop room nodes to visualize connections
- **Room Management**: Add, delete, and duplicate rooms
- **Exit Configuration**: Create directional exits between rooms with bidirectional support
- **NPC Spawning**: Assign NPCs to spawn in specific rooms
- **ASCII Art Support**: Link ASCII art files to rooms
- **Zone Organization**: Manage rooms by zones (Historic, Riverwalk, Modern, etc.)

### NPC Editor
- **Complete NPC Configuration**: Edit all NPC properties in organized tabs
- **Dialogue System**: Configure greetings, farewells, and contextual responses
- **Keyword Responses**: Set up keyword-triggered dialogue with alternatives (hello|hi|greetings)
- **Movement System**: Define allowed rooms, movement probability, and schedules
- **Ambient Actions**: Add periodic ambient behaviors
- **Memory Settings**: Configure NPC memory for player interactions
- **Context Awareness**: Set up time-based and crowd-based behaviors

### Validation System
- **Connectivity Check**: Find unreachable rooms
- **Exit Validation**: Detect broken exits and missing return paths
- **NPC Validation**: Find NPCs referencing non-existent rooms
- **ID Validation**: Ensure proper formatting for room and NPC IDs

### Safety Features
- **Automatic Backups**: Creates timestamped backups before saving
- **Unsaved Changes Warning**: Prompts before closing with unsaved changes
- **Validation Before Save**: Option to validate configuration before saving

## Requirements

- Python 3.10 or higher
- Tkinter (included with most Python installations)

### Installing Tkinter

**macOS**: Tkinter should be included with Python

**Windows**: Tkinter should be included with Python

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-tk
```

**Fedora/RHEL**:
```bash
sudo dnf install python3-tkinter
```

## Usage

### Starting the Tool

```bash
# From the SAMUD root directory
python3 config_tool.py

# Or make it executable
chmod +x config_tool.py
./config_tool.py
```

### Basic Workflow

1. **Launch the tool**: The tool automatically loads existing configuration files
2. **Select a tab**: Choose between Room Editor and NPC Editor
3. **Make changes**: Use the visual interface to modify rooms and NPCs
4. **Validate**: Click "Validate" to check for errors
5. **Save**: Click "Save" to write changes (creates automatic backup)

### Room Editor Guide

1. **Select a zone** from the dropdown (Historic, Riverwalk, etc.)
2. **View the room graph** in the center panel
3. **Click and drag rooms** to reposition them
4. **Select a room** to edit its properties
5. **Add exits** using the Exits tab
6. **Assign NPCs** using the NPCs tab

### NPC Editor Guide

1. **Select an NPC** from the left panel
2. **Edit basic properties** (name, description, personality)
3. **Configure dialogue** in the Dialogue tab
4. **Add keyword responses** in the Keywords tab
5. **Set up movement** in the Movement tab
6. **Add ambient actions** in the Ambient tab
7. **Configure memory** in the Memory/Context tab

### Keyboard Shortcuts

- **Ctrl+O**: Load/reload configuration
- **Ctrl+S**: Save configuration
- **Ctrl+F**: Find room
- **Ctrl+V**: Validate all

## File Structure

The tool works with the following file structure:

```
data/
├── rooms/
│   ├── zones.yml        # Zone configuration
│   ├── historic.yml     # Historic zone rooms
│   ├── riverwalk.yml    # Riverwalk zone rooms
│   └── modern.yml       # Modern zone rooms
├── npcs/
│   ├── tourist_guide.yml
│   ├── mariachi.yml
│   └── ...
└── backups/             # Automatic backups
    └── zones_YYYYMMDD_HHMMSS.yml
```

## Tips

### Room Design
- Start with major landmarks as anchor rooms
- Create logical connections between areas
- Use the auto-layout feature to organize rooms initially
- Group related rooms in the same zone

### NPC Design
- Give NPCs distinct personalities
- Use {player} placeholder in dialogue for personalization
- Set appropriate movement intervals (120 seconds default)
- Consider time-based schedules for realistic behavior

### Best Practices
- Validate before saving to catch errors early
- Use descriptive IDs (alamo_plaza, not room1)
- Make exits bidirectional for easier navigation
- Test NPCs in their spawn rooms after configuration

## Troubleshooting

### Tool won't start
- Ensure Python 3.10+ is installed
- Install Tkinter if missing
- Check file permissions

### Can't save changes
- Ensure write permissions on data/ directory
- Check disk space for backups
- Validate configuration for errors

### Room graph issues
- Use "Auto Layout" to reset positions
- Use "Center View" if rooms are off-screen
- Drag rooms to reposition manually

## Advanced Features

### Import/Export (Coming Soon)
- Export individual rooms or NPCs as templates
- Import templates for quick content creation
- Share content with other SAMUD instances

### Batch Operations
- Search across all rooms and NPCs
- Bulk updates to room properties
- Mass NPC assignment to rooms

## Support

For issues or questions about the configuration tool:
1. Check this README first
2. Validate your configuration for errors
3. Check the backups directory if you need to restore
4. Report issues in the SAMUD repository