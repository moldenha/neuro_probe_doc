from .utils.safety import resource_check
from .gui.main_gui import MainGui

if __name__ == '__main__':
    resource_check()
    root = MainGui()
    root.mainloop()

