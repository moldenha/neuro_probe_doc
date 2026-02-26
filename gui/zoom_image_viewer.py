import tkinter as tk
from PIL import Image, ImageTk
# from ..test import some_func
from ..utils.safety import get_data_points

class ZoomImageViewer(tk.Frame):
    def __init__(self, master, image_path):
        super().__init__(master)
        self.master = master
        # self.pack(fill=tk.BOTH, expand=True, side = "top")

        # Canvas
        self.canvas = tk.Canvas(self, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Load image
        self.original_image = Image.open(image_path)
        self.current_image = self.original_image.copy()

        self.zoom = 1.0
        self.image_id = None
        self.tk_image = None

        # Draw first image
        self._update_image()
        
        # Make canvas focusable
        self.canvas.configure(highlightthickness=0)
        self.canvas.focus_set()
        # This makes sure that the canvas width is correct on the window
        self.canvas.bind("<Configure>", self._update_image)

        # # Bind scroll to root window
        # self.master.bind_all("<MouseWheel>", self._on_mousewheel)

        # # Bind mouse wheel for zoom
        # self.canvas.bind("<MouseWheel>", self._on_mousewheel)      # Windows/Mac
        # self.canvas.bind("<Button-4>", self._on_mousewheel)        # Linux scroll up
        # self.canvas.bind("<Button-5>", self._on_mousewheel)        # Linux scroll down
    
    def zoom_image(self, x, y):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        img_w, img_h = self.original_image.size

        # Size of region to crop (smaller region = more zoom)
        crop_w = int(canvas_w / self.zoom)
        crop_h = int(canvas_h / self.zoom)

        # Center crop around (x, y)
        left = int(x - crop_w / 2)
        top = int(y - crop_h / 2)
        right = int(x + crop_w / 2)
        bottom = int(y + crop_h / 2)

        # Clamp to image bounds
        left = max(0, left)
        top = max(0, top)
        right = min(img_w, right)
        bottom = min(img_h, bottom)

        cropped = self.original_image.crop((left, top, right, bottom))

        # Resize cropped region back to canvas size
        self.current_image = cropped.resize((canvas_w, canvas_h), Image.LANCZOS)


    def _update_image(self, event = None):
        # width = int(self.original_image.width * self.zoom)
        # height = int(self.original_image.height * self.zoom)
        width = int(self.canvas.winfo_width() * self.zoom)
        height = int(self.canvas.winfo_height() * self.zoom)
        # print("width:", width)

        self.current_image = self.original_image.resize(
            (width, height), Image.LANCZOS
        )
        self.tk_image = ImageTk.PhotoImage(self.current_image)

        if self.image_id is None:
            self.image_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self.tk_image
            )
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)

        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
    
    def _bind_mouse(self, event):
        print("binding mouse")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)   # Windows & macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)     # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)     # Linux scroll down

    def _unbind_mouse(self, event):
        print("unbinding mouse")
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # Windows / macOS
        print("got event")
        if event.delta:
            if event.delta > 0:
                self.zoom *= 1.1
            else:
                self.zoom /= 1.1

        # Linux
        elif event.num == 4:
            self.zoom *= 1.1
        elif event.num == 5:
            self.zoom /= 1.1

        # Clamp zoom
        self.zoom = max(0.1, min(self.zoom, 10))
        self._update_image()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Zoom Image Viewer")
    root.geometry("800x600")

    viewer = ZoomImageViewer(root, "/Users/sam/Projects/Freiwald/ProbeDocu/resources/image.jpeg")
    root.mainloop()
