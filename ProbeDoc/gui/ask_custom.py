# This is meant to be like the tkinter.messagebox.askquestion
# But with custom options

import tkinter as tk

def askcustom(parent, title, message, option1='yes', option2='no'):
    result = {"value" : None}
    
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text=message, padx=20, pady=20).pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def choose(val):
        result["value"] = val
        win.destroy()

    tk.Button(btn_frame, text=option1, width=10,
              command = lambda: choose(option1)).pack(side="left", padx=5)
    tk.Button(btn_frame, text=option2, width=10,
              command = lambda: choose(option2)).pack(side="left", padx=5)
    parent.wait_window(win)

    return result["value"]

