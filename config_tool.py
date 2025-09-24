#!/usr/bin/env python3
"""
SAMUD Configuration Tool Launcher

A cross-platform graphical editor for room and NPC configurations.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def main():
    """Launch the configuration tool"""
    if not check_tkinter():
        print("Error: Tkinter is not available on your system.")
        print("\nPlease install Tkinter:")
        print("  - Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  - Fedora: sudo dnf install python3-tkinter")
        print("  - macOS: Tkinter should be included with Python")
        print("  - Windows: Tkinter should be included with Python")
        sys.exit(1)

    try:
        from config_tool.main import ConfigTool

        print("Starting SAMUD Configuration Tool...")
        print("This tool allows you to visually edit room and NPC configurations.")
        print("")

        app = ConfigTool()
        app.mainloop()

    except ImportError as e:
        print(f"Error importing configuration tool: {e}")
        print("Make sure all required files are present in src/config_tool/")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting configuration tool: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()