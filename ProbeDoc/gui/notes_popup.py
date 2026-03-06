import tkinter as tk
from tkinter import ttk
from ..utils.safety import save_notes, load_notes
# from tkinter import filedialog

class NotesPopup:

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.button = ttk.Button(parent, text="Notes", command=self.open)
        self.button.pack(side = 'left', padx=5, anchor="nw")

    def open(self):

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Notes")
        self.window.geometry("400x300")

        frame = ttk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", pady=0)

        ttk.Button(button_row, text="Save", command=self.save_notes).pack(side="left")
        ttk.Button(button_row, text="Close", command=self.window.destroy).pack(side="left", padx=5)

        text_row = ttk.Frame(frame)
        text_row.pack(fill="both", expand=True)
        self.text = tk.Text(text_row, wrap="word")
        self.text.pack(fill="both", expand=True)
        self.text.insert("1.0", load_notes())



    def save_notes(self):

        content = self.text.get("1.0", "end-1c")
        save_notes(content)

