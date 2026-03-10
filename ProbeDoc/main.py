from .utils.safety import resource_check, ask_external_sync
from .gui.main_gui import MainGui

def main():
    resource_check()
    def on_close():
        ask_external_sync()
        root.destroy()
    root = MainGui()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind_all("<Button-1>", lambda event: event.widget.focus_set())
    root.mainloop()


if __name__ == '__main__':
    main()
