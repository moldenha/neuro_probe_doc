import tkinter as tk
from tkinter import ttk


# This is the note function on each individual data point
class CollapsableNote(tk.Frame):
    def __init__(self, parent, callback=None):
        super().__init__(parent)

        self.callback = callback
        self.expanded = False

        self.arrow = tk.Button(self, text="▼", width=2, command=self.toggle)
        self.arrow.pack(side="left")
        self.text = tk.Text(self, height=1, width=40)
        self.text.pack(side="left", fill="x", expand=True)



        # Bind return
        # self.text.bind("<Return>", self.expand)
        self.text.bind("<FocusOut>", self._commit)

    def toggle(self):
        if self.expanded:
            self.text.configure(height=1)
            self.arrow.configure(text="▼")
            self.expanded = False

            if self.callback:
                content = self.text.get("1.0", "end-1c")
                self.callback(content)

        else:
            self.text.configure(height=5)
            self.arrow.configure(text="▲")
            self.expanded = True

    def expand(self, event=None):
        if not self.expanded:
            self.toggle()
        return "break"  # prevents newline being inserted
    
    def _commit(self, event=None):
        text = self.text.get("1.0", tk.END)
        print("commit called with text", text)
        if self.callback:
            self.callback(text)


def note_changed(text):
    print("User finished writing:", text)

if __name__ == '__main__':
    root = tk.Tk()

    note = CollapsableNote(root, callback=note_changed)
    note.pack(fill="x", padx=10, pady=10)

    root.mainloop()

