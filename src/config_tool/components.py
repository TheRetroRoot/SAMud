"""
Shared UI components for the configuration tool
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Optional, List, Callable, Dict
from pathlib import Path


class SearchableListbox(tk.Frame):
    """A listbox with search functionality"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        # Search bar
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search_changed)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Listbox with scrollbar
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, **kwargs)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.all_items = []
        self.filtered_items = []

    def set_items(self, items: List[str]):
        """Set the list of items"""
        self.all_items = items
        self._update_display()

    def _on_search_changed(self, *args):
        """Handle search text change"""
        self._update_display()

    def _update_display(self):
        """Update the listbox display based on search filter"""
        search_text = self.search_var.get().lower()

        if search_text:
            self.filtered_items = [
                item for item in self.all_items
                if search_text in item.lower()
            ]
        else:
            self.filtered_items = self.all_items.copy()

        self.listbox.delete(0, tk.END)
        for item in self.filtered_items:
            self.listbox.insert(tk.END, item)

    def get_selected(self) -> Optional[str]:
        """Get the currently selected item"""
        selection = self.listbox.curselection()
        if selection:
            return self.filtered_items[selection[0]]
        return None

    def bind_select(self, callback: Callable):
        """Bind a callback to selection changes"""
        self.listbox.bind('<<ListboxSelect>>', lambda e: callback())


class RoomPicker(tk.Toplevel):
    """Dialog for selecting a room"""

    def __init__(self, parent, rooms: Dict[str, any], title="Select Room"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x500")
        self.result = None

        # Room list
        self.room_list = SearchableListbox(self, height=15)
        self.room_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate rooms
        room_names = [f"{room.name} ({room_id})" for room_id, room in rooms.items()]
        self.room_list.set_items(room_names)
        self.room_ids = list(rooms.keys())

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="Select", command=self._on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _on_select(self):
        """Handle room selection"""
        selected = self.room_list.get_selected()
        if selected:
            # Extract room ID from display name
            room_id = selected.split('(')[-1].rstrip(')')
            self.result = room_id
            self.destroy()


class TextEditor(tk.Frame):
    """Text editor with line numbers and syntax highlighting"""

    def __init__(self, parent, height=10, **kwargs):
        super().__init__(parent)

        # Text widget with scrollbar
        text_frame = tk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(text_frame)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Changed wrap from tk.NONE to tk.WORD for word wrapping
        self.text = tk.Text(text_frame, height=height, wrap=tk.WORD,
                           yscrollcommand=y_scroll.set, **kwargs)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.config(command=self.text.yview)

        # No horizontal scrollbar needed with word wrapping

    def get_content(self) -> str:
        """Get the text content"""
        return self.text.get("1.0", tk.END).rstrip()

    def set_content(self, content: str):
        """Set the text content"""
        self.text.delete("1.0", tk.END)
        if content:
            self.text.insert("1.0", content)
        self.text.update_idletasks()  # Force UI update


class KeyValueEditor(tk.Frame):
    """Editor for key-value pairs (like NPC keywords)"""

    def __init__(self, parent):
        super().__init__(parent)

        # Controls
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, pady=5)

        tk.Button(control_frame, text="Add", command=self._add_pair).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Remove", command=self._remove_pair).pack(side=tk.LEFT, padx=5)

        # List of key-value pairs
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(list_frame, columns=('key', 'value'),
                                show='headings', yscrollcommand=scrollbar.set)
        self.tree.heading('key', text='Keywords')
        self.tree.heading('value', text='Response')
        self.tree.column('key', width=150)
        self.tree.column('value', width=300)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        self.tree.bind('<Double-1>', self._edit_pair)

    def _add_pair(self):
        """Add a new key-value pair"""
        dialog = KeyValueDialog(self, "Add Keyword")
        self.wait_window(dialog)
        if dialog.result:
            key, value = dialog.result
            self.tree.insert('', tk.END, values=(key, value))

    def _remove_pair(self):
        """Remove selected pair"""
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])

    def _edit_pair(self, event):
        """Edit selected pair"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            key, value = item['values']

            dialog = KeyValueDialog(self, "Edit Keyword", key, value)
            self.wait_window(dialog)
            if dialog.result:
                new_key, new_value = dialog.result
                self.tree.item(selection[0], values=(new_key, new_value))

    def get_pairs(self) -> Dict[str, str]:
        """Get all key-value pairs as dictionary"""
        result = {}
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            result[values[0]] = values[1]
        return result

    def set_pairs(self, pairs: Dict[str, str]):
        """Set key-value pairs from dictionary"""
        self.tree.delete(*self.tree.get_children())
        for key, value in pairs.items():
            self.tree.insert('', tk.END, values=(key, value))


class KeyValueDialog(tk.Toplevel):
    """Dialog for entering a key-value pair"""

    def __init__(self, parent, title, key="", value=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.result = None

        # Key entry
        tk.Label(self, text="Keywords (use | for alternatives):").pack(anchor=tk.W, padx=10, pady=5)
        self.key_entry = tk.Entry(self, width=50)
        self.key_entry.pack(padx=10, pady=5)
        self.key_entry.insert(0, key)

        # Value entry
        tk.Label(self, text="Response:").pack(anchor=tk.W, padx=10, pady=5)
        self.value_entry = tk.Entry(self, width=50)
        self.value_entry.pack(padx=10, pady=5)
        self.value_entry.insert(0, value)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _on_ok(self):
        """Save the key-value pair"""
        key = self.key_entry.get().strip()
        value = self.value_entry.get().strip()

        if key and value:
            self.result = (key, value)
            self.destroy()
        else:
            messagebox.showwarning("Invalid Input", "Both keywords and response are required")


class ValidationResultsDialog(tk.Toplevel):
    """Dialog showing validation results"""

    def __init__(self, parent, errors: List, error_count: int, warning_count: int):
        super().__init__(parent)
        self.title("Validation Results")
        self.geometry("600x400")

        # Summary
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        if error_count == 0 and warning_count == 0:
            tk.Label(summary_frame, text="✓ No issues found!",
                    font=('TkDefaultFont', 10, 'bold'),
                    fg='green').pack()
        else:
            if error_count > 0:
                tk.Label(summary_frame, text=f"❌ {error_count} errors",
                        fg='red').pack(side=tk.LEFT, padx=5)
            if warning_count > 0:
                tk.Label(summary_frame, text=f"⚠️ {warning_count} warnings",
                        fg='orange').pack(side=tk.LEFT, padx=5)

        # Results text
        text_frame = tk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.results_text = scrolledtext.ScrolledText(text_frame, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Add errors to text
        for error in errors:
            level_symbol = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(error.level, '')
            self.results_text.insert(tk.END, f"{level_symbol} [{error.level.upper()}] {error.category}: {error.message}\n")

        self.results_text.config(state=tk.DISABLED)

        # Close button
        tk.Button(self, text="Close", command=self.destroy).pack(pady=10)