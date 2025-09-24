"""
NPC editor with property panels
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, List

from .models import NPC, NPCDialogue, NPCMovement, NPCMemory, NPCContext
from .components import SearchableListbox, TextEditor, KeyValueEditor, RoomPicker
from .utils import validate_npc_id, format_npc_display_name


class NPCEditor(tk.Frame):
    """NPC editing interface"""

    def __init__(self, parent, world_data, on_change_callback: Callable):
        super().__init__(parent)
        self.world_data = world_data
        self.on_change = on_change_callback
        self.current_npc = None

        self._create_ui()
        self.refresh()

    def _create_ui(self):
        """Create the user interface"""
        # Main paned window
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - NPC list
        left_panel = tk.Frame(paned)
        paned.add(left_panel, width=300)

        tk.Label(left_panel, text="NPCs:").pack(anchor=tk.W, padx=5, pady=5)
        self.npc_list = SearchableListbox(left_panel, height=20)
        self.npc_list.pack(fill=tk.BOTH, expand=True)
        self.npc_list.bind_select(self._on_npc_selected)

        # NPC buttons
        button_frame = tk.Frame(left_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="Add", command=self.add_npc).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Delete", command=self._delete_npc).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Duplicate", command=self._duplicate_npc).pack(side=tk.LEFT, padx=2)

        # Right panel - NPC properties
        right_panel = tk.Frame(paned)
        paned.add(right_panel)

        # Create notebook for properties
        self.prop_notebook = ttk.Notebook(right_panel)
        self.prop_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self._create_basic_tab()
        self._create_dialogue_tab()
        self._create_keywords_tab()
        self._create_movement_tab()
        self._create_ambient_tab()
        self._create_memory_tab()

    def _create_basic_tab(self):
        """Create basic properties tab"""
        basic_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(basic_frame, text="Basic")

        # NPC ID
        tk.Label(basic_frame, text="NPC ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.id_var = tk.StringVar()
        self.id_entry = tk.Entry(basic_frame, textvariable=self.id_var, state="readonly")
        self.id_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # NPC name
        tk.Label(basic_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(basic_frame, textvariable=self.name_var)
        self.name_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.name_var.trace_add('write', lambda *args: self._on_property_changed())

        # Description
        tk.Label(basic_frame, text="Description:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.desc_text = TextEditor(basic_frame, height=6)
        self.desc_text.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=5)

        # Personality
        tk.Label(basic_frame, text="Personality:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.personality_var = tk.StringVar()
        self.personality_entry = tk.Entry(basic_frame, textvariable=self.personality_var)
        self.personality_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        self.personality_var.trace_add('write', lambda *args: self._on_property_changed())

        basic_frame.grid_columnconfigure(1, weight=1)
        basic_frame.grid_rowconfigure(2, weight=1)

    def _create_dialogue_tab(self):
        """Create dialogue tab"""
        dialogue_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(dialogue_frame, text="Dialogue")

        # Create scrollable frame
        canvas = tk.Canvas(dialogue_frame)
        scrollbar = tk.Scrollbar(dialogue_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Dialogue fields
        tk.Label(scrollable_frame, text="Greeting (New Player):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.greeting_new_text = TextEditor(scrollable_frame, height=3)
        self.greeting_new_text.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Greeting (Return):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.greeting_return_text = TextEditor(scrollable_frame, height=3)
        self.greeting_return_text.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Farewell:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.farewell_text = TextEditor(scrollable_frame, height=3)
        self.farewell_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Player Arrival:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.player_arrival_text = TextEditor(scrollable_frame, height=3)
        self.player_arrival_text.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Player Departure:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.player_departure_text = TextEditor(scrollable_frame, height=3)
        self.player_departure_text.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)

        tk.Label(scrollable_frame, text="Use {player} for player name", fg="gray").grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        scrollable_frame.grid_columnconfigure(1, weight=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_keywords_tab(self):
        """Create keywords tab"""
        keywords_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(keywords_frame, text="Keywords")

        tk.Label(keywords_frame, text="Keywords and Responses:").pack(anchor=tk.W, padx=5, pady=5)
        tk.Label(keywords_frame, text="Use | to separate keyword alternatives (e.g., 'hello|hi|greetings')", fg="gray").pack(anchor=tk.W, padx=5)

        self.keywords_editor = KeyValueEditor(keywords_frame)
        self.keywords_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_movement_tab(self):
        """Create movement tab"""
        movement_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(movement_frame, text="Movement")

        # Movement settings
        settings_frame = tk.LabelFrame(movement_frame, text="Movement Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(settings_frame, text="Tick Interval (seconds):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.tick_interval_var = tk.IntVar(value=120)
        self.tick_interval_spin = tk.Spinbox(settings_frame, from_=30, to=600, textvariable=self.tick_interval_var)
        self.tick_interval_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        tk.Label(settings_frame, text="Movement Probability:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.movement_prob_var = tk.DoubleVar(value=0.3)
        self.movement_prob_spin = tk.Spinbox(settings_frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.movement_prob_var)
        self.movement_prob_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Allowed rooms
        rooms_frame = tk.LabelFrame(movement_frame, text="Allowed Rooms")
        rooms_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls
        control_frame = tk.Frame(rooms_frame)
        control_frame.pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Add Room", command=self._add_allowed_room).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Remove Room", command=self._remove_allowed_room).pack(side=tk.LEFT, padx=5)

        # Room list
        self.allowed_rooms_listbox = tk.Listbox(rooms_frame, height=8)
        self.allowed_rooms_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Schedule
        schedule_frame = tk.LabelFrame(movement_frame, text="Schedule (Optional)")
        schedule_frame.pack(fill=tk.X, padx=5, pady=5)

        self.schedule_entries = {}
        for i, time_slot in enumerate(['morning', 'afternoon', 'evening', 'night']):
            tk.Label(schedule_frame, text=f"{time_slot.capitalize()}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar()
            entry = tk.Entry(schedule_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
            self.schedule_entries[time_slot] = var

        schedule_frame.grid_columnconfigure(1, weight=1)

    def _create_ambient_tab(self):
        """Create ambient actions tab"""
        ambient_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(ambient_frame, text="Ambient")

        tk.Label(ambient_frame, text="Ambient Actions (one per line):").pack(anchor=tk.W, padx=5, pady=5)
        self.ambient_text = TextEditor(ambient_frame, height=10)
        self.ambient_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(ambient_frame, text="These actions will be randomly displayed periodically", fg="gray").pack(anchor=tk.W, padx=5, pady=5)

    def _create_memory_tab(self):
        """Create memory/context tab"""
        memory_frame = tk.Frame(self.prop_notebook)
        self.prop_notebook.add(memory_frame, text="Memory/Context")

        # Memory settings
        memory_group = tk.LabelFrame(memory_frame, text="Memory Settings")
        memory_group.pack(fill=tk.X, padx=5, pady=5)

        self.remember_names_var = tk.BooleanVar(value=True)
        tk.Checkbutton(memory_group, text="Remember player names", variable=self.remember_names_var).pack(anchor=tk.W, padx=5, pady=2)

        self.remember_topics_var = tk.BooleanVar(value=True)
        tk.Checkbutton(memory_group, text="Remember conversation topics", variable=self.remember_topics_var).pack(anchor=tk.W, padx=5, pady=2)

        tk.Label(memory_group, text="Memory duration (days):").pack(side=tk.LEFT, padx=5, pady=5)
        self.memory_duration_var = tk.IntVar(value=30)
        tk.Spinbox(memory_group, from_=1, to=365, textvariable=self.memory_duration_var).pack(side=tk.LEFT, padx=5, pady=5)

        # Context awareness
        context_group = tk.LabelFrame(memory_frame, text="Context Awareness")
        context_group.pack(fill=tk.X, padx=5, pady=5)

        self.time_aware_var = tk.BooleanVar(value=False)
        tk.Checkbutton(context_group, text="Time aware (responds differently based on time)", variable=self.time_aware_var).pack(anchor=tk.W, padx=5, pady=2)

        self.crowd_aware_var = tk.BooleanVar(value=False)
        tk.Checkbutton(context_group, text="Crowd aware (responds differently based on room population)", variable=self.crowd_aware_var).pack(anchor=tk.W, padx=5, pady=2)

        # Crowd reactions
        crowd_frame = tk.LabelFrame(memory_frame, text="Crowd Reactions")
        crowd_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.crowd_reaction_entries = {}
        for i, (crowd_level, default) in enumerate([('empty', 'Alone behavior'), ('few', 'Small group behavior'), ('many', 'Crowd behavior')]):
            tk.Label(crowd_frame, text=f"{crowd_level.capitalize()}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar()
            entry = tk.Entry(crowd_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
            self.crowd_reaction_entries[crowd_level] = var

        crowd_frame.grid_columnconfigure(1, weight=1)

    def refresh(self):
        """Refresh the display"""
        self._update_npc_list()

    def _update_npc_list(self):
        """Update the NPC list"""
        npc_names = [format_npc_display_name(npc) for npc in self.world_data.npcs.values()]
        self.npc_list.set_items(npc_names)

    def _on_npc_selected(self):
        """Handle NPC selection"""
        selected = self.npc_list.get_selected()
        if selected:
            # Extract NPC ID from display name
            npc_id = selected.split('(')[-1].rstrip(')')
            if npc_id in self.world_data.npcs:
                self.current_npc = self.world_data.npcs[npc_id]
                self._update_properties()

    def _update_properties(self):
        """Update property fields with current NPC data"""
        if not self.current_npc:
            return

        # Basic properties
        self.id_var.set(self.current_npc.id)
        self.name_var.set(self.current_npc.name)
        self.desc_text.set_content(self.current_npc.description)
        self.personality_var.set(self.current_npc.personality)

        # Dialogue
        self.greeting_new_text.set_content(self.current_npc.dialogue.greeting_new)
        self.greeting_return_text.set_content(self.current_npc.dialogue.greeting_return)
        self.farewell_text.set_content(self.current_npc.dialogue.farewell)
        self.player_arrival_text.set_content(self.current_npc.dialogue.player_arrival)
        self.player_departure_text.set_content(self.current_npc.dialogue.player_departure)

        # Keywords
        self.keywords_editor.set_pairs(self.current_npc.keywords)

        # Movement
        self.tick_interval_var.set(self.current_npc.movement.tick_interval)
        self.movement_prob_var.set(self.current_npc.movement.movement_probability)

        # Allowed rooms
        self.allowed_rooms_listbox.delete(0, tk.END)
        for room_id in self.current_npc.movement.allowed_rooms:
            self.allowed_rooms_listbox.insert(tk.END, room_id)

        # Schedule
        for time_slot, var in self.schedule_entries.items():
            var.set(self.current_npc.movement.schedule.get(time_slot, ""))

        # Ambient actions
        ambient_text = "\n".join(self.current_npc.ambient_actions)
        self.ambient_text.set_content(ambient_text)

        # Memory
        self.remember_names_var.set(self.current_npc.memory.remember_names)
        self.remember_topics_var.set(self.current_npc.memory.remember_topics)
        self.memory_duration_var.set(self.current_npc.memory.memory_duration)

        # Context
        self.time_aware_var.set(self.current_npc.context.time_aware)
        self.crowd_aware_var.set(self.current_npc.context.crowd_aware)

        # Crowd reactions
        for crowd_level, var in self.crowd_reaction_entries.items():
            var.set(self.current_npc.context.crowd_reactions.get(crowd_level, ""))

    def _on_property_changed(self):
        """Handle property changes"""
        if not self.current_npc:
            return

        # Update NPC data
        self.current_npc.name = self.name_var.get()
        self.current_npc.description = self.desc_text.get_content()
        self.current_npc.personality = self.personality_var.get()

        # Dialogue
        self.current_npc.dialogue.greeting_new = self.greeting_new_text.get_content()
        self.current_npc.dialogue.greeting_return = self.greeting_return_text.get_content()
        self.current_npc.dialogue.farewell = self.farewell_text.get_content()
        self.current_npc.dialogue.player_arrival = self.player_arrival_text.get_content()
        self.current_npc.dialogue.player_departure = self.player_departure_text.get_content()

        # Keywords
        self.current_npc.keywords = self.keywords_editor.get_pairs()

        # Movement
        self.current_npc.movement.tick_interval = self.tick_interval_var.get()
        self.current_npc.movement.movement_probability = self.movement_prob_var.get()

        # Schedule
        schedule = {}
        for time_slot, var in self.schedule_entries.items():
            value = var.get().strip()
            if value:
                schedule[time_slot] = value
        self.current_npc.movement.schedule = schedule

        # Ambient actions
        ambient_text = self.ambient_text.get_content()
        self.current_npc.ambient_actions = [line.strip() for line in ambient_text.split('\n') if line.strip()]

        # Memory
        self.current_npc.memory.remember_names = self.remember_names_var.get()
        self.current_npc.memory.remember_topics = self.remember_topics_var.get()
        self.current_npc.memory.memory_duration = self.memory_duration_var.get()

        # Context
        self.current_npc.context.time_aware = self.time_aware_var.get()
        self.current_npc.context.crowd_aware = self.crowd_aware_var.get()

        # Crowd reactions
        crowd_reactions = {}
        for crowd_level, var in self.crowd_reaction_entries.items():
            value = var.get().strip()
            if value:
                crowd_reactions[crowd_level] = value
        self.current_npc.context.crowd_reactions = crowd_reactions

        # Mark as changed
        self.on_change()
        self._update_npc_list()

    def add_npc(self):
        """Add a new NPC"""
        # Get NPC ID from user
        npc_id = simpledialog.askstring("New NPC", "Enter NPC ID:")
        if not npc_id:
            return

        # Validate ID
        if not validate_npc_id(npc_id):
            messagebox.showerror("Invalid ID", "NPC ID can only contain letters, numbers, and underscores")
            return

        # Check for duplicate
        if npc_id in self.world_data.npcs:
            messagebox.showerror("Duplicate ID", f"NPC '{npc_id}' already exists")
            return

        # Create new NPC
        new_npc = NPC(
            id=npc_id,
            name=f"New NPC {npc_id}",
            description="A new NPC.",
            dialogue=NPCDialogue(),
            movement=NPCMovement(),
            memory=NPCMemory(),
            context=NPCContext()
        )

        self.world_data.npcs[npc_id] = new_npc

        # Update UI
        self.on_change()
        self._update_npc_list()

        # Select the new NPC
        self.current_npc = new_npc
        self._update_properties()

    def _delete_npc(self):
        """Delete selected NPC"""
        if not self.current_npc:
            messagebox.showwarning("No Selection", "Please select an NPC to delete")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete NPC '{self.current_npc.name}' ({self.current_npc.id})?\n\n"
            "This will also remove the NPC from all room spawn lists."
        )

        if result:
            npc_id = self.current_npc.id

            # Remove from NPCs
            del self.world_data.npcs[npc_id]

            # Remove from room spawn lists
            all_rooms = self.world_data.get_all_rooms()
            for room in all_rooms.values():
                if npc_id in room.npcs:
                    room.npcs.remove(npc_id)

            # Clear selection
            self.current_npc = None

            # Update UI
            self.on_change()
            self._update_npc_list()

    def _duplicate_npc(self):
        """Duplicate selected NPC"""
        if not self.current_npc:
            messagebox.showwarning("No Selection", "Please select an NPC to duplicate")
            return

        # Get new ID
        npc_id = simpledialog.askstring(
            "Duplicate NPC",
            f"Enter ID for duplicate of '{self.current_npc.name}':"
        )
        if not npc_id:
            return

        # Validate ID
        if not validate_npc_id(npc_id):
            messagebox.showerror("Invalid ID", "NPC ID can only contain letters, numbers, and underscores")
            return

        # Check for duplicate
        if npc_id in self.world_data.npcs:
            messagebox.showerror("Duplicate ID", f"NPC '{npc_id}' already exists")
            return

        # Create duplicate
        new_npc = NPC(
            id=npc_id,
            name=f"{self.current_npc.name} (Copy)",
            description=self.current_npc.description,
            personality=self.current_npc.personality,
            dialogue=NPCDialogue(
                greeting_new=self.current_npc.dialogue.greeting_new,
                greeting_return=self.current_npc.dialogue.greeting_return,
                farewell=self.current_npc.dialogue.farewell,
                player_arrival=self.current_npc.dialogue.player_arrival,
                player_departure=self.current_npc.dialogue.player_departure
            ),
            keywords=self.current_npc.keywords.copy(),
            movement=NPCMovement(
                allowed_rooms=self.current_npc.movement.allowed_rooms.copy(),
                tick_interval=self.current_npc.movement.tick_interval,
                movement_probability=self.current_npc.movement.movement_probability,
                schedule=self.current_npc.movement.schedule.copy()
            ),
            ambient_actions=self.current_npc.ambient_actions.copy(),
            memory=NPCMemory(
                remember_names=self.current_npc.memory.remember_names,
                remember_topics=self.current_npc.memory.remember_topics,
                memory_duration=self.current_npc.memory.memory_duration
            ),
            context=NPCContext(
                time_aware=self.current_npc.context.time_aware,
                crowd_aware=self.current_npc.context.crowd_aware,
                crowd_reactions=self.current_npc.context.crowd_reactions.copy()
            )
        )

        self.world_data.npcs[npc_id] = new_npc

        # Update UI
        self.on_change()
        self._update_npc_list()

    def _add_allowed_room(self):
        """Add a room to allowed rooms list"""
        if not self.current_npc:
            return

        # Show room picker
        all_rooms = self.world_data.get_all_rooms()
        dialog = RoomPicker(self, all_rooms, "Select Room")
        self.wait_window(dialog)

        if dialog.result:
            if dialog.result not in self.current_npc.movement.allowed_rooms:
                self.current_npc.movement.allowed_rooms.append(dialog.result)
                self.allowed_rooms_listbox.insert(tk.END, dialog.result)
                self.on_change()

    def _remove_allowed_room(self):
        """Remove selected room from allowed rooms"""
        selection = self.allowed_rooms_listbox.curselection()
        if selection and self.current_npc:
            index = selection[0]
            room_id = self.allowed_rooms_listbox.get(index)
            self.current_npc.movement.allowed_rooms.remove(room_id)
            self.allowed_rooms_listbox.delete(index)
            self.on_change()

    def show_search(self):
        """Show the search interface"""
        self.npc_list.search_entry.focus()