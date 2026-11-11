from .utils.safety import resource_check, ask_external_sync
from .gui.main_gui import MainGui
import tkinter as tk
def set_focus_safely(event):
    if isinstance(event.widget, tk.Misc):
        try:
            event.widget.focus_set()
        except tk.TclError:
            pass  # Ignore widgets that cannot take focus

def main():
    resource_check()
    def on_close():
        ask_external_sync()
        root.destroy()
    root = MainGui()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind_all("<Button-1>", lambda event: set_focus_safely(event))
    root.mainloop()


if __name__ == '__main__':
    main()
