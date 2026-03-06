# DEPRECIATION WARNING
# This class was previously a toggled drop down menu
# It has been remade to be a multi select column with different buttons

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image
import io

class MultiSelectDropdown:
    def __init__(self, parent, items, text = "Select Items", row=1, column=0):
        self.parent = parent
        self.items = items
        self.vars = {}

        # self.button = ttk.Button(parent, text=text, command=self.toggle_dropdown)
        # self.button.pack(side = 'left', padx=5, anchor="nw")

        self.sidebar = None
        self.bind_func = self.on_item_toggle
        self.edit_points_fcn = self.edit_button
        self.delete_points_fcn = self.delete_button
        self.make_dropdown(row=row, column=column)

    def make_dropdown(self, row=1, column=0):
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.destroy()
        
        self.sidebar = ttk.Frame(self.parent)
        self.sidebar.grid(row=row, column=column)
        # self.sidebar.grid(row=row, column=column)
        self.sidebar.grid(sticky="nw")
        self.sidebar.rowconfigure(0, weight=0)  
        self.sidebar.columnconfigure(0, weight=1) # only columns expandable
        # self.sidebar.pack(fill="both", expand=True)
         # ---- Select All ----
        select_all_var = tk.BooleanVar()

        def toggle_all():
            for var in self.vars.values():
                var.set(select_all_var.get())

        ttk.Checkbutton(
            self.sidebar,
            text="Select All",
            variable=select_all_var,
            command=toggle_all
        ).pack(anchor="w")

        ttk.Separator(self.sidebar).pack(fill="x", pady=5)

        # ---- Items ----
        for name, color in self.items:
            row = ttk.Frame(self.sidebar)
            row.pack(fill="x", padx=5, pady=2)
            
            if name not in self.vars:
                var = tk.BooleanVar()
                self.vars[name] = var
            else:
                var = self.vars[name]
                # print(var.trace_info())

            cb = ttk.Checkbutton(row, variable=var)
            cb.pack(side="left")

            # Color dot
            dot = tk.Canvas(row, width=12, height=12, highlightthickness=0)
            dot.create_oval(2, 2, 10, 10, fill=color)
            dot.pack(side="left", padx=5)

            ttk.Label(row, text=name).pack(side="left")
            delete_button = tk.Button(row, text="Delete", command = lambda n=name : self.delete_points_fcn(n))
            delete_button.pack(side="right")
            edit_button = tk.Button(row, text="Edit", command = lambda n=name : self.edit_points_fcn(n))
            edit_button.pack(side="right")


        self.bind(self.bind_func)


    def toggle_dropdown(self, row=0, column=1):
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.destroy()
            return
        
        self.make_dropdown(row=row, column=column)

    def bind(self, func):
        self.bind_func = func
        for name, color in self.items:
            var = self.vars[name]
            # going to clear previous traces here that are called "write"
            traces = var.trace_info()
            for trace in traces:
                # (('write',), '4737211392<lambda>')
                try:
                    mode = trace[0][0]
                    if mode != 'write': continue
                except:
                    continue
                cbname = trace[1]
                var.trace_remove(mode, cbname)

            var.trace_add("write", lambda *args, n=name: func(n))

    def on_item_toggle(self, name):
        state = self.vars[name].get()
        print(f"{name} is now {'ON' if state else 'OFF'}")

    def edit_button(self, name):
        print("going to edit", name)
        self.parent.edit_data_point(name)
    
    def delete_button(self, name):
        print("going to delete", name)


if __name__ == '__main__':
    # ---- Demo ----
    root = tk.Tk()
    items = [
        ("Apples", "#ff0000"),
        ("Limes", "#00ff00"),
        ("Blueberries", "#0000ff"),
    ]
    dropdown = MultiSelectDropdown(root, items)
    root.mainloop()

