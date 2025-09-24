"""
Main window for the SAMUD Configuration Tool
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import sys

from .models import WorldData
from .room_editor import RoomEditor
from .npc_editor import NPCEditor
from .validators import validate_world_data
from .components import ValidationResultsDialog
from .utils import create_backup


class ConfigTool(tk.Tk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.title("SAMUD Configuration Tool")
        self.geometry("1200x800")

        # Data model
        self.world_data = WorldData()
        self.data_dir = Path("data")
        self.unsaved_changes = False

        # Create menu bar
        self._create_menu()

        # Create toolbar
        self._create_toolbar()

        # Create tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Room editor tab
        self.room_editor = RoomEditor(self.notebook, self.world_data, self._on_data_changed)
        self.notebook.add(self.room_editor, text="Room Editor")

        # NPC editor tab
        self.npc_editor = NPCEditor(self.notebook, self.world_data, self._on_data_changed)
        self.notebook.add(self.npc_editor, text="NPC Editor")

        # Status bar
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load data on startup
        self.after(100, self._load_data)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load", command=self._load_data, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_data, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Find Room...", command=self._find_room, accelerator="Ctrl+F")
        edit_menu.add_command(label="Find NPC...", command=self._find_npc)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Validate All", command=self._validate_all, accelerator="Ctrl+V")
        tools_menu.add_command(label="Check Connectivity", command=self._check_connectivity)
        tools_menu.add_separator()
        tools_menu.add_command(label="Import Room...", command=self._import_room)
        tools_menu.add_command(label="Export Room...", command=self._export_room)
        tools_menu.add_command(label="Import NPC...", command=self._import_npc)
        tools_menu.add_command(label="Export NPC...", command=self._export_npc)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

        # Bind keyboard shortcuts
        self.bind_all("<Control-o>", lambda e: self._load_data())
        self.bind_all("<Control-s>", lambda e: self._save_data())
        self.bind_all("<Control-f>", lambda e: self._find_room())
        self.bind_all("<Control-v>", lambda e: self._validate_all())

    def _create_toolbar(self):
        """Create the toolbar"""
        toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Toolbar buttons
        tk.Button(toolbar, text="Load", command=self._load_data).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Save", command=self._save_data).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        tk.Button(toolbar, text="Validate", command=self._validate_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        tk.Button(toolbar, text="Add Room", command=self._add_room).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Add NPC", command=self._add_npc).pack(side=tk.LEFT, padx=2)

    def _on_data_changed(self):
        """Called when data is modified"""
        self.unsaved_changes = True
        self._update_status("Modified")

    def _update_status(self, message: str):
        """Update the status bar"""
        if self.unsaved_changes:
            message = f"{message} *"
        self.status_bar.config(text=message)

    def _load_data(self):
        """Load world data from files"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before loading?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes, save first
                self._save_data()

        try:
            self.world_data.load_from_files(self.data_dir)
            self.room_editor.refresh()
            self.npc_editor.refresh()
            self.unsaved_changes = False
            self._update_status("Loaded successfully")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")
            self._update_status("Load failed")

    def _save_data(self):
        """Save world data to files"""
        try:
            # Create backups
            zones_file = self.data_dir / 'rooms' / 'zones.yml'
            if zones_file.exists():
                backup_path = create_backup(zones_file)
                if backup_path:
                    self._update_status(f"Backup created: {backup_path.name}")

            # Save data
            self.world_data.save_to_files(self.data_dir)
            self.unsaved_changes = False
            self._update_status("Saved successfully")
            messagebox.showinfo("Save Complete", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data:\n{str(e)}")
            self._update_status("Save failed")

    def _save_as(self):
        """Save to a different location"""
        directory = filedialog.askdirectory(
            title="Select Data Directory",
            initialdir=self.data_dir
        )
        if directory:
            self.data_dir = Path(directory)
            self._save_data()

    def _validate_all(self):
        """Validate all configuration data"""
        errors, error_count, warning_count = validate_world_data(self.world_data)

        # Show results dialog
        dialog = ValidationResultsDialog(self, errors, error_count, warning_count)
        self._update_status(f"Validation: {error_count} errors, {warning_count} warnings")

    def _check_connectivity(self):
        """Check room connectivity"""
        from .utils import find_unreachable_rooms

        all_rooms = self.world_data.get_all_rooms()
        if not all_rooms:
            messagebox.showinfo("No Rooms", "No rooms defined")
            return

        unreachable = find_unreachable_rooms(all_rooms)

        if unreachable:
            message = "The following rooms are unreachable:\n\n"
            message += "\n".join(unreachable[:20])  # Show first 20
            if len(unreachable) > 20:
                message += f"\n... and {len(unreachable) - 20} more"
            messagebox.showwarning("Unreachable Rooms", message)
        else:
            messagebox.showinfo("Connectivity OK", "All rooms are reachable!")

    def _find_room(self):
        """Find and select a room"""
        self.notebook.select(0)  # Switch to room editor tab
        self.room_editor.show_search()

    def _find_npc(self):
        """Find and select an NPC"""
        self.notebook.select(1)  # Switch to NPC editor tab
        self.npc_editor.show_search()

    def _add_room(self):
        """Add a new room"""
        self.notebook.select(0)  # Switch to room editor tab
        self.room_editor.add_room()

    def _add_npc(self):
        """Add a new NPC"""
        self.notebook.select(1)  # Switch to NPC editor tab
        self.npc_editor.add_npc()

    def _import_room(self):
        """Import a room from file"""
        messagebox.showinfo("Import Room", "Room import functionality coming soon!")

    def _export_room(self):
        """Export a room to file"""
        messagebox.showinfo("Export Room", "Room export functionality coming soon!")

    def _import_npc(self):
        """Import an NPC from file"""
        messagebox.showinfo("Import NPC", "NPC import functionality coming soon!")

    def _export_npc(self):
        """Export an NPC to file"""
        messagebox.showinfo("Export NPC", "NPC export functionality coming soon!")

    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About SAMUD Config Tool",
            "SAMUD Configuration Tool v1.0\n\n"
            "A graphical editor for San Antonio MUD\n"
            "room and NPC configurations.\n\n"
            "Built with Python and Tkinter"
        )

    def _on_closing(self):
        """Handle window close event"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes, save first
                self._save_data()

        self.quit()


def main():
    """Launch the configuration tool"""
    app = ConfigTool()
    app.mainloop()


if __name__ == "__main__":
    main()