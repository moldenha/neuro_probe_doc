import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
from .zoom_image_viewer import ZoomImageViewer
from .canvas_img import CanvasImage
from .multi_selector_dropdown import MultiSelectDropdown
from .name_color_dialog import get_name_and_color
from ..utils.safety import set_always_sync_on_startup, backup_from_sync, set_external_sync, external_sync, get_data_points, save_data_points, load_image_paths, add_image, get_image_path
from ..utils.config import config
from pathlib import Path
from PIL import Image, ImageTk
from functools import partial


class MainGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Neuropixel Probe Location Documentation")
        self.geometry("800x600")
        self.toolbar = tk.Frame(self)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        # self.toolbar.pack(side="top", fill="x")
        # .name would give you with the extension
        # .stem would give you without the extension
        self.images = [Path(file_path).stem for file_path in load_image_paths()]
        self.data_points = get_data_points()
        self.selected_image = None
        self.combo_box = None
        if self.images == {} or len(self.images) == 0:
            self.images = []
            self.register_new_image()
        assert len(self.images) == len(set(self.images)), "Error, you have an image in resources and in the images list that is duplicated"
        self.update_image_selector()
        self.check_data_points()
        self.data_point_selector = MultiSelectDropdown(self.toolbar, [], "View Points")
        self.data_point_selector.bind_func = self.draw_data_point
        self.data_point_selector.edit_points_fcn = self.edit_data_point
        self.data_point_selector.delete_points_fcn = self.delete_data_point
        self.update_data_point_selector()
        self.add_point_button = ttk.Button(self.toolbar, text="Add Point", command=self.add_data_point)
        self.add_point_button.pack(side = 'left', padx=5, anchor="nw")
        self.add_image_button = ttk.Button(self.toolbar, text = "Add Image", command=self.register_new_image)
        self.add_image_button.pack(side = 'left', padx=5, anchor='nw')
        zoom_in_img = Image.open(config["ZoomInImg"]).resize((18, 18))
        self.zoom_in_icon = ImageTk.PhotoImage(zoom_in_img)
        self.zoom_in_button = tk.Button(self.toolbar, image=self.zoom_in_icon, command=self.zoom_in__)
        self.zoom_in_button.pack(side = 'left', padx=5, anchor="nw")
        zoom_out_img = Image.open(config["ZoomOutImg"]).resize((18, 18))
        self.zoom_out_icon = ImageTk.PhotoImage(zoom_out_img)
        self.zoom_out_button = tk.Button(self.toolbar, image=self.zoom_out_icon, command=self.zoom_out__)
        self.zoom_out_button.pack(side = 'left', padx=5, anchor="nw")
        self.image_viewer = None
        self.grid_rowconfigure(0, weight=0)   # toolbar does NOT expand
        self.grid_rowconfigure(1, weight=1)   # viewer expands
        self.grid_columnconfigure(0, weight=1)
        self.display_new_image()
        self.point_radius = tk.Scale(self.toolbar,
                                     from_ = 0.0,
                                     to = 50.0,
                                     orient = tk.HORIZONTAL,
                                     resolution = 0.3,
                                     command = self.update_data_point_size
        )
        self.point_radius.pack(side = 'left', padx=5, anchor="nw")
        self.point_radius.set(5.0)
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.options_menu = tk.Menu(self.menubar, tearoff=0)
        self.options_menu.add_command(label="Set External Sync", command=set_external_sync)
        self.options_menu.add_command(label="Sync", command= lambda f=True: external_sync(f))
        self.options_menu.add_command(label="Backup From Sync", command=lambda f=True: backup_from_sync)
        self.option_always_sync_on_startup_var = tk.BooleanVar()
        self.option_always_sync_on_startup_var.set(config.get("StartupBackupSync", False))
        # self.option_always_sync_on_startup_var.trace_add("write", lambda *args, n=self.option_always_sync_on_startup_var: set_always_sync_on_startup(n.get()))
        self.options_menu.add_checkbutton(label="Always Backup From Sync on Start",
                                          variable = self.option_always_sync_on_startup_var,
                                          command = lambda n=self.option_always_sync_on_startup_var: set_always_sync_on_startup(n))
        
        self.menubar.add_cascade(label="Options", menu=self.options_menu)


    def update_data_point_selector(self):
        l = self.data_points[self.selected_image.get()]
        if len(l) == 0:
            self.data_point_selector.items = []
        
        self.data_point_selector.vars = {}
        self.data_point_selector.items = [(item["name"], item["color"]) for item in l]
        self.data_point_selector.items = sorted(self.data_point_selector.items, key = lambda item: item[0])
        
    
    def delete_data_point(self, name):
        l = self.data_points[self.selected_image.get()]
        indexes = [i for i, x in enumerate(l) if x["name"] == name]
        if len(indexes) == 0:
            return
        toggle = False
        if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
            self.data_point_selector.popup.destroy()
            toggle = True
        item = self.data_points[self.selected_image.get()][indexes[0]]
        if self.image_viewer:
            self.image_viewer.remove_data_point(item["pos"][0], item["pos"][1], item["color"])
        self.data_points[self.selected_image.get()].pop(indexes[0])
        save_data_points(self.data_points)
        self.update_data_point_selector()
        self.data_point_selector.toggle_dropdown()

    def data_point_selector_add__(self, name, color):
        self.data_point_selector.items.append((name, color))
        self.data_point_selector.items = sorted(self.data_point_selector.items, key = lambda item: item[0])

    
    def handle_final_data_point_adder__(self, img, name, color, pos):
        # print(f"handle final data point adder called {img}, {name}, {color}, {pos}")
        if pos is None: return
        for item in self.data_points[img]:
            if item["name"] == name:
                messagebox.showwarning("Duplicate Name", "You are trying to register a date twice under the same image (please change name/date)")
                return # because the name already exists
        self.data_point_selector_add__(name, color)
        self.data_points[img].append({"name" : name, "color" : color, "pos" : pos})
        save_data_points(self.data_points)

    def handle_final_data_point_editer__(self, index, img, name, color, pos):
        # print(f"handle final data point adder called {img}, {name}, {color}, {pos}")
        if pos is None: return
        self.data_points[img][index] = {"name" : name, "color" : color, "pos" : pos }
        save_data_points(self.data_points)
        self.update_data_point_selector()


    def add_data_point(self, event=None):
        if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
            self.data_point_selector.popup.destroy()
        result = get_name_and_color(self)
        if result:
            name, color = result
            img = self.selected_image.get()
            pos_func = partial(
                self.handle_final_data_point_adder__,
                img,
                name,
                color
            )
            self.image_viewer.pos_input_fcn = pos_func
            self.toggle_data_points_off()
            self.image_viewer.togle_motion_picker()

    def edit_data_point(self, name):
        img = self.selected_image.get()
        print("going to edit", name)
        index = -1
        for i in range(len(self.data_points[img])):
            if self.data_points[img][i]["name"] == name:
                index = i
                break
        if index == -1: return
        print("index is", index)
        print(self.data_points[img][index])
        if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
            self.data_point_selector.popup.destroy()
        self.data_point_selector.vars[name].set(False)
        result = get_name_and_color(self, name = name, color = self.data_points[img][index]["color"])
        if result:
            name, color = result
            pos_func = partial(
                self.handle_final_data_point_editer__,
                index,
                img,
                name,
                color
            )
            self.image_viewer.pos_input_fcn = pos_func
            self.image_viewer.togle_motion_picker()
    
    def update_data_point_size(self, value):
        radi = float(value)
        if self.image_viewer is None: return
        all_item_ids = self.image_viewer.canvas.find_all()
        # print(all_item_ids)
        for item_id in all_item_ids:
            tags = self.image_viewer.canvas.gettags(item_id)
            # print(tags)
            if len(tags) > 0 and tags[0].startswith("data_point"):
                self.image_viewer.edit_data_point_radius(item_id, radi)
    
    def draw_data_point(self, name):
        state = self.data_point_selector.vars[name].get()
        print(f"{name} is now {'ON' if state else 'OFF'}")
        if self.image_viewer is None: return
        img = self.selected_image.get()
        data = None
        for pt in self.data_points[img]:
            if name == pt["name"]:
                data = pt
                break
        if data is None: return
        if not state:
            if (data['pos'][0], data['pos'][1], data['color']) in self.image_viewer.data_draw_points:
                self.image_viewer.data_draw_points.remove((data['pos'][0], data['pos'][1], data['color']))
                self.image_viewer.remove_data_point(data['pos'][0], data['pos'][1], data['color']) 
                
        else:
            if (data['pos'][0], data['pos'][1], data['color']) not in self.image_viewer.data_draw_points:
                self.image_viewer.data_draw_points.append((data['pos'][0], data['pos'][1], data['color']))
                self.image_viewer.draw_data_point(data['pos'][0], data['pos'][1], data['color'], radius = self.point_radius.get()) 
        # self.image_viewer.show_image()
    
    def toggle_data_points_off(self):
        for var in self.data_point_selector.vars.values():
            var.set(False)

    def check_data_points(self):
        save = False
        for image in self.images:
            if image not in self.data_points.keys():
                save = True
                self.data_points[image] = []
        
        if save:
            save_data_points(self.data_points)
    
    def update_image_selector(self):
        if self.combo_box is None:
            self.make_image_selector()
            return
        self.combo_box["values"] = self.images
        

    def make_image_selector(self):
        selected = tk.StringVar()
        update_option = (self.selected_image is None)
        if update_option:
            self.selected_image = tk.StringVar()
        self.combo_box = ttk.Combobox(
            self.toolbar,
            textvariable=self.selected_image,
            values=self.images,
            state="readonly"
        )
        if update_option:
            self.selected_image.set(self.images[0])
        # self.combo_box.grid(row=0, column=0)
        self.combo_box.pack(side="left", padx=5, anchor="nw")
        self.combo_box.bind("<<ComboboxSelected>>", self.on_image_selection__)
    
    def display_new_image(self):
        self.toggle_data_points_off()
        img_path = get_image_path(self.selected_image.get())
        if img_path is None:
            messagebox.showwarning("Image Not Found", f"The image {img_path} does not exist!")
            return
        print("image path is", img_path)
        if self.image_viewer is not None:
            # destroy current zoom image viewer
            self.image_viewer.destroy()
        self.image_viewer = CanvasImage(self, img_path)
        self.image_viewer.grid(row=1, column=0)
        self.data_point_selector.vars = {}
        # self.image_viewer.pack(side="top", fill="both", expand=True)

    
    def zoom_in__(self, event = None):
        if self.image_viewer is None:
            return
        self.image_viewer.zoom_in_option = not self.image_viewer.zoom_in_option
        self.image_viewer.zoom_out_option = False
        try:
            self.image_viewer.canvas.config(cursor="zoom-in" if self.image_viewer.zoom_in_option else "")
        except tk.TclError:
            self.image_viewer.canvas.config(cursor=config["ZoomInCursorFallback"] if self.image_viewer.zoom_in_option else "")


    def zoom_out__(self, event = None):
        if self.image_viewer is None:
            return
        self.image_viewer.zoom_out_option = not self.image_viewer.zoom_out_option
        self.image_viewer.zoom_in_option = False
        try:
            self.image_viewer.canvas.config(cursor="zoom-out" if self.image_viewer.zoom_out_option else "")
        except tk.TclError:
            self.image_viewer.canvas.config(cursor=config["ZoomOutCursorFallback"] if self.image_viewer.zoom_out_option else "")


    def on_image_selection__(self, event):
        print(f"Selected: {self.selected_image.get()}")
        self.display_new_image()
        self.update_data_point_selector()

    def register_new_image(self):
        if hasattr(self, "data_point_selector") and self.data_point_selector is not None:
            if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
                self.data_point_selector.popup.destroy()
        filetypes = (
            ('Image files', ('*.png', '*.jpeg', '*.jpg', '*.tiff', '*.bmp', '*.webp', '*.ico', '*.ppm', '*.xbm')),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Load an Image',
            initialdir='.',
            filetypes=filetypes
        )
        if filename:
            new_image = add_image(filename)
            if new_image is not None:
                img_name = Path(new_image).stem
                if img_name in self.images:
                    messagebox.showwarning("Duplicate Image", "You are trying to register an image who's name already exists in the registrar!")
                    return
                self.images.append(Path(new_image).stem)
                self.update_image_selector()
                self.check_data_points()


if __name__ == '__main__':
    root = MainGui()
    root.mainloop()
