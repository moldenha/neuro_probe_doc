import tkinter as tk
from tkinter import ttk, colorchooser
from datetime import date

class NameColorDialog:
    def __init__(self, parent, default_name = "", default_color = "#ffffff"):
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("Add Date Point")
        self.window.transient(parent)
        self.window.grab_set()  # modality

        ttk.Label(self.window, text="Date (YYYY/MM/DD):").pack(padx=10, pady=(10, 2))
        # ttk.Label(self.window, text="Date:").pack(pady=(10, 0))

        self.date_var = tk.StringVar()
        self.date_var.set(default_name)
        self.date_entry = ttk.Entry(self.window, textvariable=self.date_var, width=15)
        self.date_entry.pack(padx=10, pady=5)
        tk.Button(self.window, text="Today", command=self.set_today).pack(pady=5)
        # self.name_entry = ttk.Entry(self.window)
        # self.name_entry.pack(padx=20, pady=5)

        self.color = default_color

        self.color_button = ttk.Button(
            self.window,
            text="Choose Color",
            command=self.choose_color
        )
        self.color_button.pack(pady=5)

        self.preview = tk.Canvas(self.window, width=40, height=20, highlightthickness=1)
        self.preview.pack(pady=5)
        self.preview.create_rectangle(0, 0, 40, 20, fill=self.color)

        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side="left", padx=5)

        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        self.date_entry.focus()

        # Wait until window closes
        parent.wait_window(self.window)
    
    def set_today(self):
        today_str = date.today().strftime("%Y/%m/%d")
        self.date_var.set(today_str)

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color)
        if color[1]:  # color[1] is hex string
            self.color = color[1]
            self.preview.delete("all")
            self.preview.create_rectangle(0, 0, 40, 20, fill=self.color)

    def save(self):
        name = self.date_var.get().strip()
        if name:
            self.result = (name, self.color)
        self.window.destroy()

    def cancel(self):
        self.result = None
        self.window.destroy()


def get_name_and_color(parent, name = '', color = '#ffffff'):
    dialog = NameColorDialog(parent, default_name = name, default_color = color)
    return dialog.result


