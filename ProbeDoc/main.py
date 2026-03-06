from .utils.safety import resource_check, ask_external_sync
from .gui.main_gui import MainGui

def main():
    resource_check()
    def on_close():
        ask_external_sync()
        root.destroy()
    root = MainGui()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
