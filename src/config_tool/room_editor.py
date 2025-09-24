"""
Room editor with visual graph
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable, Dict, Set
import math

from .models import Room, Zone
from .components import SearchableListbox, TextEditor, RoomPicker
from .utils import validate_room_id, get_direction_opposite, format_room_display_name


class RoomEditor(tk.Frame):
    """Room editing interface with visual graph"""

    def __init__(self, parent, world_data, on_change_callback: Callable):
        super().__init__(parent)
        self.world_data = world_data
        self.on_change = on_change_callback
        self.current_room = None
        self.current_zone = None

        # Room positions for visual graph
        self.room_positions = {}
        self.selected_room = None
        self.dragging_room = None
        self.drag_data = {"x": 0, "y": 0}

        self._create_ui()
        self.refresh()

    def _create_ui(self):
        """Create the user interface"""
        # Main paned window with resizable sashes
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED,
                               sashwidth=5, showhandle=True, handlesize=8)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Room list and zones
        left_panel = tk.Frame(paned)
        paned.add(left_panel, minsize=200, width=250)

        # Zone selector
        zone_frame = tk.Frame(left_panel)
        zone_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(zone_frame, text="Zone:").pack(side=tk.LEFT)
        self.zone_var = tk.StringVar()
        self.zone_combo = ttk.Combobox(zone_frame, textvariable=self.zone_var, state="readonly")
        self.zone_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.zone_combo.bind('<<ComboboxSelected>>', self._on_zone_changed)

        # Room list
        tk.Label(left_panel, text="Rooms:").pack(anchor=tk.W, padx=5)
        self.room_list = SearchableListbox(left_panel, height=15)
        self.room_list.pack(fill=tk.BOTH, expand=True)
        self.room_list.bind_select(self._on_room_selected)

        # Room buttons
        button_frame = tk.Frame(left_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="Add", command=self.add_room).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Delete", command=self._delete_room).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Duplicate", command=self._duplicate_room).pack(side=tk.LEFT, padx=2)

        # Middle panel - Visual graph
        middle_panel = tk.Frame(paned)
        paned.add(middle_panel, minsize=400, width=600)

        tk.Label(middle_panel, text="Room Graph:").pack(anchor=tk.W, padx=5, pady=5)

        # Canvas for room graph
        canvas_frame = tk.Frame(middle_panel, relief=tk.SUNKEN, bd=1)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Canvas scrollbars
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.config(scrollregion=(0, 0, 2000, 2000))

        # Canvas controls
        control_frame = tk.Frame(middle_panel)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(control_frame, text="Auto Layout", command=self._auto_layout).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Center View", command=self._center_view).pack(side=tk.LEFT, padx=2)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Right panel - Room properties
        right_panel = tk.Frame(paned)
        paned.add(right_panel, minsize=300, width=350)

        # Create notebook for properties
        self.prop_notebook = ttk.Notebook(right_panel)
        self.prop_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Basic properties tab
        self._create_basic_tab()

        # Exits tab
        self._create_exits_tab()

        # NPCs tab
        self._create_npcs_tab()

        # ASCII Art tab
        self._create_ascii_tab()

    def _create_basic_tab(self):
        """Create basic properties tab"""
        basic_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(basic_frame, text="Basic")

        # Room ID
        tk.Label(basic_frame, text="Room ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.id_var = tk.StringVar()
        self.id_entry = tk.Entry(basic_frame, textvariable=self.id_var, state="readonly")
        self.id_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Room name
        tk.Label(basic_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(basic_frame, textvariable=self.name_var)
        self.name_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.name_var.trace_add('write', lambda *args: self._on_property_changed())

        # Description
        tk.Label(basic_frame, text="Description:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.desc_text = TextEditor(basic_frame, height=8)
        self.desc_text.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=5)
        # Bind text change event - but only after initial load
        self._updating_properties = False
        self.desc_text.text.bind('<KeyRelease>', self._on_desc_changed)

        basic_frame.grid_columnconfigure(1, weight=1)
        basic_frame.grid_rowconfigure(2, weight=1)

    def _create_exits_tab(self):
        """Create exits tab"""
        exits_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(exits_frame, text="Exits")

        # Controls
        control_frame = tk.Frame(exits_frame)
        control_frame.pack(fill=tk.X, pady=5)

        tk.Button(control_frame, text="Add Exit", command=self._add_exit).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Remove Exit", command=self._remove_exit).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Make Bidirectional", command=self._make_bidirectional).pack(side=tk.LEFT, padx=5)

        # Exit list
        list_frame = tk.Frame(exits_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.exits_tree = ttk.Treeview(list_frame, columns=('direction', 'target'),
                                      show='headings', yscrollcommand=scrollbar.set)
        self.exits_tree.heading('direction', text='Direction')
        self.exits_tree.heading('target', text='Target Room')
        self.exits_tree.column('direction', width=100)
        self.exits_tree.column('target', width=200)
        self.exits_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.exits_tree.yview)

    def _create_npcs_tab(self):
        """Create NPCs tab"""
        npcs_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(npcs_frame, text="NPCs")

        tk.Label(npcs_frame, text="NPCs that spawn in this room:").pack(anchor=tk.W, padx=5, pady=5)

        # NPC checklist
        list_frame = tk.Frame(npcs_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.npc_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        self.npc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.npc_listbox.yview)

        # Update button
        tk.Button(npcs_frame, text="Update NPCs", command=self._update_room_npcs).pack(pady=5)

    def _create_ascii_tab(self):
        """Create ASCII art tab"""
        ascii_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(ascii_frame, text="ASCII Art")

        # ASCII art file
        file_frame = tk.Frame(ascii_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(file_frame, text="Art File:").pack(side=tk.LEFT)
        self.ascii_var = tk.StringVar()
        self.ascii_entry = tk.Entry(file_frame, textvariable=self.ascii_var)
        self.ascii_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.ascii_var.trace_add('write', lambda *args: self._on_ascii_changed())

        tk.Button(file_frame, text="Browse", command=self._browse_ascii).pack(side=tk.LEFT)

        # Preview
        tk.Label(ascii_frame, text="Preview:").pack(anchor=tk.W, padx=5, pady=5)
        self.ascii_preview = TextEditor(ascii_frame, height=10)
        self.ascii_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh(self):
        """Refresh the display"""
        # Update zone list with "All Zones" option
        zone_names = ['All Zones'] + list(self.world_data.zones.keys())
        self.zone_combo['values'] = zone_names
        if zone_names and not self.zone_var.get():
            self.zone_var.set('All Zones')
            self._on_zone_changed()

    def _on_zone_changed(self, event=None):
        """Handle zone selection change"""
        zone_id = self.zone_var.get()
        if zone_id == 'All Zones':
            # Show all rooms from all zones
            self.current_zone = None
            self._update_room_list()
            self._draw_graph()
        elif zone_id and zone_id in self.world_data.zones:
            self.current_zone = self.world_data.zones[zone_id]
            self._update_room_list()
            self._draw_graph()

    def _update_room_list(self):
        """Update the room list for current zone"""
        if self.current_zone is None:
            # Show all rooms from all zones
            room_names = []
            for zone in self.world_data.zones.values():
                for room in zone.rooms.values():
                    room_names.append(format_room_display_name(room))
        else:
            room_names = [format_room_display_name(room) for room in self.current_zone.rooms.values()]

        self.room_list.set_items(room_names)

    def _on_room_selected(self):
        """Handle room selection"""
        selected = self.room_list.get_selected()
        if selected:
            # Extract room ID from display name
            room_id = selected.split('(')[-1].rstrip(')')

            # Find the room in the appropriate zone
            if self.current_zone is None:
                # Search all zones
                for zone in self.world_data.zones.values():
                    if room_id in zone.rooms:
                        self.current_room = zone.rooms[room_id]
                        break
            else:
                if room_id in self.current_zone.rooms:
                    self.current_room = self.current_zone.rooms[room_id]

            if self.current_room:
                self._update_properties()
                self._highlight_room_on_canvas(room_id)

    def _update_properties(self):
        """Update property fields with current room data"""
        if not self.current_room:
            return

        # Set flag to prevent change events from firing
        self._updating_properties = True

        # Basic properties
        self.id_var.set(self.current_room.id)
        self.name_var.set(self.current_room.name)

        # Update description - schedule it to run after GUI updates
        def update_description():
            self.desc_text.text.delete("1.0", tk.END)
            if self.current_room and self.current_room.description:
                self.desc_text.text.insert("1.0", self.current_room.description)
                self.desc_text.text.update_idletasks()
            # Clear the flag after update
            self._updating_properties = False

        # Schedule the update
        self.after(10, update_description)

        # ASCII art
        self.ascii_var.set(self.current_room.ascii_art_file or "")
        self._preview_ascii_art()

        # Exits
        self.exits_tree.delete(*self.exits_tree.get_children())
        for direction, target in self.current_room.exits.items():
            self.exits_tree.insert('', tk.END, values=(direction, target))

        # NPCs
        self._update_npc_list()

    def _update_npc_list(self):
        """Update the NPC checklist"""
        self.npc_listbox.delete(0, tk.END)

        # Add all NPCs to list
        for npc_id, npc in self.world_data.npcs.items():
            display_name = f"{npc.name} ({npc_id})"
            self.npc_listbox.insert(tk.END, display_name)

            # Select if NPC is in this room
            if self.current_room and npc_id in self.current_room.npcs:
                self.npc_listbox.selection_set(tk.END)

    def _on_desc_changed(self, event=None):
        """Handle description text changes"""
        if not self.current_room or self._updating_properties:
            return

        # Update room data
        self.current_room.description = self.desc_text.get_content()

        # Mark as changed
        self.on_change()

    def _on_property_changed(self):
        """Handle property changes"""
        if not self.current_room or self._updating_properties:
            return

        # Update room data
        self.current_room.name = self.name_var.get()

        # Mark as changed
        self.on_change()
        self._update_room_list()

    def _on_ascii_changed(self):
        """Handle ASCII art file change"""
        if not self.current_room:
            return

        # Update room data
        self.current_room.ascii_art_file = self.ascii_var.get() or None

        # Preview the ASCII art
        self._preview_ascii_art()

        # Mark as changed
        self.on_change()

    def _draw_graph(self):
        """Draw the room graph on canvas"""
        self.canvas.delete("all")

        # Get rooms to draw
        if self.current_zone is None:
            # Draw all rooms from all zones
            rooms_to_draw = self.world_data.get_all_rooms()
        else:
            rooms_to_draw = self.current_zone.rooms

        if not rooms_to_draw:
            return

        # Generate positions if needed
        if not self.room_positions:
            self._auto_layout()

        # Draw connections first (so they appear behind rooms)
        for room_id, room in rooms_to_draw.items():
            if room_id in self.room_positions:
                x1, y1 = self.room_positions[room_id]

                for direction, target_id in room.exits.items():
                    if target_id in self.room_positions:
                        x2, y2 = self.room_positions[target_id]

                        # Draw arrow
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill="gray", width=2,
                            arrow=tk.LAST, arrowshape=(10, 12, 5),
                            tags=("connection", f"from_{room_id}", f"to_{target_id}")
                        )

        # Draw rooms
        for room_id, room in rooms_to_draw.items():
            if room_id in self.room_positions:
                x, y = self.room_positions[room_id]
                self._draw_room_node(room_id, room, x, y)

    def _draw_room_node(self, room_id: str, room: Room, x: int, y: int):
        """Draw a single room node"""
        width = 120
        height = 60

        # Determine color
        color = "#e0e0e0"
        if room_id == self.selected_room:
            color = "#ffcc00"

        # Draw rectangle
        rect = self.canvas.create_rectangle(
            x - width//2, y - height//2,
            x + width//2, y + height//2,
            fill=color, outline="black", width=2,
            tags=("room", room_id)
        )

        # Draw room name
        self.canvas.create_text(
            x, y - 10,
            text=room.name,
            font=("Arial", 10, "bold"),
            tags=("room_text", room_id)
        )

        # Draw room ID
        self.canvas.create_text(
            x, y + 10,
            text=f"({room_id})",
            font=("Arial", 8),
            fill="gray",
            tags=("room_text", room_id)
        )

    def _auto_layout(self):
        """Automatically layout rooms in a grid"""
        # Clear positions
        self.room_positions = {}

        # Get rooms to layout
        if self.current_zone is None:
            # Layout all rooms from all zones
            rooms = list(self.world_data.get_all_rooms().keys())
        else:
            rooms = list(self.current_zone.rooms.keys())

        if not rooms:
            return

        # Simple grid layout
        cols = max(3, int(math.sqrt(len(rooms))))

        for i, room_id in enumerate(rooms):
            row = i // cols
            col = i % cols
            x = 150 + col * 180
            y = 100 + row * 120
            self.room_positions[room_id] = (x, y)

        # Update canvas scroll region to fit all rooms
        if self.room_positions:
            max_x = max(pos[0] for pos in self.room_positions.values()) + 200
            max_y = max(pos[1] for pos in self.room_positions.values()) + 200
            self.canvas.config(scrollregion=(0, 0, max_x, max_y))

        self._draw_graph()

    def _center_view(self):
        """Center the canvas view"""
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _on_canvas_click(self, event):
        """Handle canvas click"""
        # Get clicked item
        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        for item in clicked:
            tags = self.canvas.gettags(item)
            if "room" in tags:
                # Found a room
                for tag in tags:
                    if tag != "room" and tag != "room_text":
                        self.selected_room = tag
                        self.dragging_room = tag
                        self.drag_data["x"] = event.x
                        self.drag_data["y"] = event.y

                        # Select in list
                        room = None
                        if self.current_zone is None:
                            # Find room in all zones
                            for zone in self.world_data.zones.values():
                                if self.selected_room in zone.rooms:
                                    room = zone.rooms[self.selected_room]
                                    break
                        elif self.selected_room in self.current_zone.rooms:
                            room = self.current_zone.rooms[self.selected_room]

                        if room:
                            display_name = format_room_display_name(room)
                            # Find and select in list
                            for i, item in enumerate(self.room_list.filtered_items):
                                if item == display_name:
                                    self.room_list.listbox.selection_clear(0, tk.END)
                                    self.room_list.listbox.selection_set(i)
                                    self._on_room_selected()
                                    break

                        self._draw_graph()
                        return

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.dragging_room and self.dragging_room in self.room_positions:
            # Update position
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            old_x, old_y = self.room_positions[self.dragging_room]
            self.room_positions[self.dragging_room] = (old_x + dx, old_y + dy)

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

            self._draw_graph()

    def _on_canvas_release(self, event):
        """Handle canvas release"""
        self.dragging_room = None

    def _highlight_room_on_canvas(self, room_id: str):
        """Highlight a room on the canvas"""
        self.selected_room = room_id
        self._draw_graph()

    def add_room(self):
        """Add a new room"""
        if not self.current_zone:
            messagebox.showwarning("No Zone", "Please select a zone first")
            return

        # Get room ID from user
        room_id = simpledialog.askstring("New Room", "Enter room ID:")
        if not room_id:
            return

        # Validate ID
        if not validate_room_id(room_id):
            messagebox.showerror("Invalid ID", "Room ID can only contain letters, numbers, and underscores")
            return

        # Check for duplicate
        if room_id in self.current_zone.rooms:
            messagebox.showerror("Duplicate ID", f"Room '{room_id}' already exists in this zone")
            return

        # Create new room
        new_room = Room(
            id=room_id,
            name=f"New Room {room_id}",
            description="A new room."
        )

        self.current_zone.rooms[room_id] = new_room

        # Add to graph
        if self.room_positions:
            # Place near center
            x = 400
            y = 300
            self.room_positions[room_id] = (x, y)

        # Update UI
        self.on_change()
        self._update_room_list()
        self._draw_graph()

        # Select the new room
        self.current_room = new_room
        self._update_properties()

    def _delete_room(self):
        """Delete selected room"""
        if not self.current_room:
            messagebox.showwarning("No Selection", "Please select a room to delete")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete room '{self.current_room.name}' ({self.current_room.id})?\n\n"
            "This will also remove all exits pointing to this room."
        )

        if result:
            room_id = self.current_room.id

            # Remove from zone
            del self.current_zone.rooms[room_id]

            # Remove from positions
            if room_id in self.room_positions:
                del self.room_positions[room_id]

            # Remove exits pointing to this room
            for room in self.current_zone.rooms.values():
                exits_to_remove = [
                    direction for direction, target in room.exits.items()
                    if target == room_id
                ]
                for direction in exits_to_remove:
                    del room.exits[direction]

            # Clear selection
            self.current_room = None
            self.selected_room = None

            # Update UI
            self.on_change()
            self._update_room_list()
            self._draw_graph()

    def _duplicate_room(self):
        """Duplicate selected room"""
        if not self.current_room:
            messagebox.showwarning("No Selection", "Please select a room to duplicate")
            return

        # Get new ID
        room_id = simpledialog.askstring(
            "Duplicate Room",
            f"Enter ID for duplicate of '{self.current_room.name}':"
        )
        if not room_id:
            return

        # Validate ID
        if not validate_room_id(room_id):
            messagebox.showerror("Invalid ID", "Room ID can only contain letters, numbers, and underscores")
            return

        # Check for duplicate
        if room_id in self.current_zone.rooms:
            messagebox.showerror("Duplicate ID", f"Room '{room_id}' already exists")
            return

        # Create duplicate
        new_room = Room(
            id=room_id,
            name=f"{self.current_room.name} (Copy)",
            description=self.current_room.description,
            ascii_art_file=self.current_room.ascii_art_file,
            exits={},  # Don't copy exits
            npcs=self.current_room.npcs.copy()
        )

        self.current_zone.rooms[room_id] = new_room

        # Update UI
        self.on_change()
        self._update_room_list()
        self._draw_graph()

    def _add_exit(self):
        """Add an exit to current room"""
        if not self.current_room:
            messagebox.showwarning("No Room", "Please select a room first")
            return

        # Get direction
        directions = ["north", "south", "east", "west", "northeast", "northwest",
                     "southeast", "southwest", "up", "down", "in", "out"]

        dialog = ExitDialog(self, directions, self.world_data.get_all_rooms())
        self.wait_window(dialog)

        if dialog.result:
            direction, target_id = dialog.result

            # Add exit
            self.current_room.exits[direction] = target_id

            # Update UI
            self.on_change()
            self._update_properties()
            self._draw_graph()

    def _remove_exit(self):
        """Remove selected exit"""
        selection = self.exits_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an exit to remove")
            return

        item = self.exits_tree.item(selection[0])
        direction = item['values'][0]

        # Remove exit
        if direction in self.current_room.exits:
            del self.current_room.exits[direction]

            # Update UI
            self.on_change()
            self._update_properties()
            self._draw_graph()

    def _make_bidirectional(self):
        """Make selected exit bidirectional"""
        selection = self.exits_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an exit to make bidirectional")
            return

        item = self.exits_tree.item(selection[0])
        direction, target_id = item['values']

        # Get opposite direction
        opposite = get_direction_opposite(direction)
        if not opposite:
            messagebox.showwarning("No Opposite", f"No opposite direction for '{direction}'")
            return

        # Find target room
        target_room = self.world_data.get_room_by_id(target_id)
        if not target_room:
            messagebox.showerror("Room Not Found", f"Target room '{target_id}' not found")
            return

        # Check if opposite already exists
        if opposite in target_room.exits:
            messagebox.showinfo("Already Exists", f"Room '{target_id}' already has '{opposite}' exit")
            return

        # Add opposite exit
        target_room.exits[opposite] = self.current_room.id

        # Update UI
        self.on_change()
        self._draw_graph()
        messagebox.showinfo("Success", f"Added '{opposite}' exit from '{target_id}' to '{self.current_room.id}'")

    def _update_room_npcs(self):
        """Update NPCs for current room"""
        if not self.current_room:
            return

        # Get selected NPCs
        selected_indices = self.npc_listbox.curselection()
        selected_npcs = []

        for index in selected_indices:
            display_name = self.npc_listbox.get(index)
            # Extract NPC ID
            npc_id = display_name.split('(')[-1].rstrip(')')
            selected_npcs.append(npc_id)

        # Update room
        self.current_room.npcs = selected_npcs

        # Update UI
        self.on_change()
        messagebox.showinfo("Updated", f"Room now has {len(selected_npcs)} NPCs")

    def _browse_ascii(self):
        """Browse for ASCII art file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select ASCII Art File",
            initialdir="data/rooms/art",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            # Make relative to data/rooms/art if possible
            from pathlib import Path
            art_dir = Path("data/rooms/art")
            file_path = Path(filename)

            try:
                relative = file_path.relative_to(art_dir)
                self.ascii_var.set(str(relative))
            except:
                self.ascii_var.set(filename)

            # Preview the selected file
            self._preview_ascii_art()

    def _preview_ascii_art(self):
        """Preview ASCII art file content"""
        ascii_file = self.ascii_var.get()
        if not ascii_file:
            self.ascii_preview.set_content("")
            return

        # Try to load the ASCII art file
        from pathlib import Path

        # Check common paths
        possible_paths = [
            Path(f"data/rooms/art/{ascii_file}"),
            Path(f"data/rooms/art/{ascii_file}.txt") if not ascii_file.endswith('.txt') else None,
            Path(ascii_file)
        ]

        for path in possible_paths:
            if path and path.exists():
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                        self.ascii_preview.set_content(content)
                        return
                except Exception as e:
                    pass

        # File not found
        self.ascii_preview.set_content(f"[ASCII art file not found: {ascii_file}]")

    def show_search(self):
        """Show the search interface"""
        self.room_list.search_entry.focus()


class ExitDialog(tk.Toplevel):
    """Dialog for adding an exit"""

    def __init__(self, parent, directions: list, rooms: dict):
        super().__init__(parent)
        self.title("Add Exit")
        self.geometry("400x200")
        self.result = None

        # Direction
        tk.Label(self, text="Direction:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.direction_var = tk.StringVar()
        self.direction_combo = ttk.Combobox(self, textvariable=self.direction_var,
                                           values=directions, state="readonly")
        self.direction_combo.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)

        # Target room
        tk.Label(self, text="Target Room:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.target_var = tk.StringVar()
        room_names = [f"{room.name} ({room_id})" for room_id, room in rooms.items()]
        self.target_combo = ttk.Combobox(self, textvariable=self.target_var,
                                        values=room_names, state="readonly")
        self.target_combo.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.grid_columnconfigure(1, weight=1)

    def _on_ok(self):
        """Save the exit"""
        direction = self.direction_var.get()
        target = self.target_var.get()

        if direction and target:
            # Extract room ID
            target_id = target.split('(')[-1].rstrip(')')
            self.result = (direction, target_id)
            self.destroy()
        else:
            messagebox.showwarning("Incomplete", "Please select both direction and target room")