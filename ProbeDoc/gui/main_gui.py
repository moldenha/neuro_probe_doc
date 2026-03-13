import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
from .zoom_image_viewer import ZoomImageViewer
from .canvas_img import CanvasImage
from .multi_selector_side_table import MultiSelectSideTable
from .name_color_dialog import get_name_and_color, get_name_and_color_edit
from .ask_custom import askcustom
from ..utils.safety import set_always_sync_on_startup, backup_from_sync, set_external_sync, external_sync, get_data_points, save_data_points, load_image_paths, add_image, get_image_path, delete_image
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
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        # self.toolbar.pack(side="top", fill="x")
        # .name would give you with the extension
        # .stem would give you without the extension
        self.images = [Path(file_path).stem for file_path in load_image_paths()]
        self.data_points = get_data_points()
        self.selected_image = None
        self.combo_box = None
        if self.images == {} or len(self.images) == 0:
            self.images = []
            img_or_sync = askcustom(self, "No Images Found", "No images have been registered yet, please either sync with an external directory that has images, or select an image",
                                    "Sync", "Select Image")
            if img_or_sync == "Sync":
                set_external_sync()
                backup_from_sync()
            else:
                self.register_new_image()
            if len(self.images) == 0:
                messagebox.showerror("No Images Found", 
                            "Error, no images have been registered, unable to continue, either sync a directory or choose an image")
        assert len(self.images) == len(set(self.images)), "Error, you have an image in resources and in the images list that is duplicated"
        self.update_image_selector()
        self.check_data_points()
        self.data_point_selector = MultiSelectSideTable(self, [], "View Points")
        self.data_point_selector.bind_func = self.draw_data_point
        self.data_point_selector.notes_callback = self.edit_note__
        self.data_point_selector.get_notes_callback = self.get_note__
        self.data_point_selector.edit_points_fcn = self.edit_data_point
        self.data_point_selector.delete_points_fcn = self.delete_data_point
        self.update_data_point_selector()
        self.add_image_button = ttk.Button(self.toolbar, text = "Add Image", command=self.register_new_image)
        self.add_image_button.pack(side = 'left', padx=5, anchor='nw')

        self.add_point_button = ttk.Button(self.toolbar, text="Add Point", command=self.add_data_point)
        self.add_point_button.pack(side = 'left', padx=5, anchor="nw")
        zoom_in_img = Image.open(config["ZoomInImg"]).resize((18, 18))
        zoom_in_img_activated = Image.open(config["ZoomInImgActivated"]).resize((18, 18))
        self.zoom_in_icon = ImageTk.PhotoImage(zoom_in_img)
        self.zoom_in_activated_icon = ImageTk.PhotoImage(zoom_in_img_activated)
        self.zoom_in_button = tk.Button(self.toolbar, image=self.zoom_in_icon, command=self.zoom_in__)
        self.zoom_in_button.pack(side = 'left', padx=5, anchor="nw")
        zoom_out_img = Image.open(config["ZoomOutImg"]).resize((18, 18))
        zoom_out_img_activated = Image.open(config["ZoomOutImgActivated"]).resize((18, 18))
        self.zoom_out_icon = ImageTk.PhotoImage(zoom_out_img)
        self.zoom_out_activated_icon = ImageTk.PhotoImage(zoom_out_img_activated)
        self.zoom_out_button = tk.Button(self.toolbar, image=self.zoom_out_icon, command=self.zoom_out__)
        self.zoom_out_button.pack(side = 'left', padx=5, anchor="nw")
        self.image_viewer = None
        # Make the main column expand
        self.grid_rowconfigure(0, weight=0)   # toolbar does NOT expand
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        # self.grid_rowconfigure(0, weight=0)   # toolbar does NOT expand
        # self.grid_rowconfigure(1, weight=1)   # viewer expands
        # self.grid_columnconfigure(0, weight=0) # Column point viewer does NOT expand
        # self.grid_columnconfigure(1, weight=1) # viewer expands
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
        
        self.options_menu.add_separator()

        self.delete_menu = tk.Menu(self.options_menu, tearoff=0)
        for img in self.images:
            self.delete_menu.add_command(label=img, command= lambda : self.delete_image__(img))
        self.options_menu.add_cascade(label="Delete Image", menu = self.delete_menu)


        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Export", command=self.save_canvas)
        
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Options", menu=self.options_menu)

        self.update_data_point_selector()
        self.status_window = None


    def update_data_point_selector(self):
        var_cpy = {}
        for key in self.data_point_selector.vars.keys():
            var_cpy[key] = self.data_point_selector.vars[key].get()
        self.toggle_data_points_off()
        l = self.data_points[self.selected_image.get()]
        if len(l) == 0:
            self.data_point_selector.items = []
        
        self.data_point_selector.vars = {}
        self.data_point_selector.items = [(item["name"], item["color"]) for item in l]
        self.data_point_selector.items = sorted(self.data_point_selector.items, key = lambda item: item[0])
        self.data_point_selector.make_dropdown()
        keys = self.data_point_selector.vars.keys()
        for key in var_cpy.keys():
            if key in keys:
                self.data_point_selector.vars[key].set(var_cpy[key])
        
    
    def delete_data_point(self, name):
        l = self.data_points[self.selected_image.get()]
        indexes = [i for i, x in enumerate(l) if x["name"] == name]
        if len(indexes) == 0:
            return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure that you would like to delete {name} data point?"):
            return
        item = self.data_points[self.selected_image.get()][indexes[0]]
        if self.image_viewer:
            self.image_viewer.remove_data_point(item["pos"][0], item["pos"][1], item["color"])
        self.data_points[self.selected_image.get()].pop(indexes[0])
        save_data_points(self.data_points)
        self.update_data_point_selector()
        # self.data_point_selector.toggle_dropdown()

    # def data_point_selector_add__(self, name, color):
    #     self.data_point_selector.items.append((name, color))
    #     self.data_point_selector.items = sorted(self.data_point_selector.items, key = lambda item: item[0])
    #     self.data_point_selector
    
    def edit_note__(self, name, note):
        l = self.data_points[self.selected_image.get()]
        indexes = [i for i, x in enumerate(l) if x["name"] == name]
        if len(indexes) == 0:
            return
        self.data_points[self.selected_image.get()][indexes[0]]["notes"] = note
        save_data_points(self.data_points)
    
    def get_note__(self, name):
        l = self.data_points[self.selected_image.get()]
        indexes = [i for i, x in enumerate(l) if x["name"] == name]
        if len(indexes) == 0:
            return ""
        return self.data_points[self.selected_image.get()][indexes[0]].get("notes", "")


    def handle_final_data_point_adder__(self, img, name, color, pos):
        # print(f"handle final data point adder called {img}, {name}, {color}, {pos}")
        if pos is None: return
        for item in self.data_points[img]:
            if item["name"] == name:
                messagebox.showwarning("Duplicate Name", "You are trying to register a date twice under the same image (please change name/date)")
                return # because the name already exists
        # self.data_point_selector_add__(name, color)
        self.data_points[img].append({"name" : name, "color" : color, "pos" : pos, "notes" : ""})
        save_data_points(self.data_points)
        self.update_data_point_selector() 
        self.hide_status()
        self.data_point_selector.vars[name].set(True)

    def handle_final_data_point_editer__(self, index, img, name, color, canvas_data_point, pos):
        # print(f"handle final data point adder called {img}, {name}, {color}, {pos}")
        print("handling final data point edit")
        if canvas_data_point is not None:
            self.manual_remove_data_point_on_canvas(*canvas_data_point)
        if pos is None: return
        print(self.data_points[img][index])
        n_notes = self.data_points[img][index].get("notes", "")
        print(n_notes)
        self.data_points[img][index] = {"name" : name, "color" : color, "pos" : pos, "notes" : n_notes}
        save_data_points(self.data_points)
        self.update_data_point_selector()
        self.data_point_selector.vars[name].set(True)
        self.hide_status()


    def add_data_point(self, event=None):
        # if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
        #     self.data_point_selector.popup.destroy()
        result = get_name_and_color(self)
        if result:
            name, color = result
            self.show_status(f"Currently adding point {name} position")
            self.image_viewer.canvas.focus_force()
            img = self.selected_image.get()
            pos_func = partial(
                self.handle_final_data_point_adder__,
                img,
                name,
                color
            )
            self.image_viewer.pos_input_fcn = pos_func
            # self.toggle_data_points_off()
            img = self.selected_image.get()
            data_pts = self.data_points[img]

            self.image_viewer.togle_motion_picker(self.point_radius.get(), data_pts)

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
        # if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
        #     self.data_point_selector.popup.destroy()
        canvas_data_point = self.find_canvas_point_data(name)
        if canvas_data_point is not None:
            canvas_data_point = (canvas_data_point["pos"][0], canvas_data_point["pos"][1], canvas_data_point["color"])
        
        self.data_point_selector.vars[name].set(False)
        if canvas_data_point is not None:
            self.manual_draw_data_point_on_canvas(*canvas_data_point, name) 
        result = get_name_and_color_edit(self, name = name, color = self.data_points[img][index]["color"])
        if result and result[2]:
            name, color, change_loc = result
            self.show_status(f"Currently editing point {name} position")
            self.image_viewer.canvas.focus_force()
            pos_func = partial(
                self.handle_final_data_point_editer__,
                index,
                img,
                name,
                color,
                canvas_data_point
            )
            self.image_viewer.pos_input_fcn = pos_func
            data_pts = self.data_points[img]
            self.image_viewer.togle_motion_picker(self.point_radius.get(), data_pts)
        if result and not result[2]:
            name, color, change_loc = result
            self.handle_final_data_point_editer__(index, img, name, color, canvas_data_point,
                                                  self.data_points[img][index]["pos"])
        else:
            self.update_data_point_selector()
    
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
    
    def find_canvas_point_data(self, name):
        if self.image_viewer is None: return None
        img = self.selected_image.get()
        for pt in self.data_points[img]:
            if name == pt["name"]:
                return pt
        return None

    def manual_remove_data_point_on_canvas(self, x, y, color):
        if (x, y, color) in self.image_viewer.data_draw_points:
            self.image_viewer.data_draw_points.remove((x, y, color))
            self.image_viewer.remove_data_point(x, y, color) 

    def manual_draw_data_point_on_canvas(self, x, y, color, name):
        if (x, y, color) not in self.image_viewer.data_draw_points:
            self.image_viewer.data_draw_points.append((x, y, color))
            self.image_viewer.draw_data_point(x, y, color, radius = self.point_radius.get(), name_tag=name) 

    def draw_data_point(self, name):
        state = self.data_point_selector.vars[name].get()
        print(f"{name} is now {'ON' if state else 'OFF'}")
        if self.image_viewer is None: return
        data = self.find_canvas_point_data(name)
        if data is None: return
        if not state:
            self.manual_remove_data_point_on_canvas(data['pos'][0], data['pos'][1], data['color'])
        else:
            self.manual_draw_data_point_on_canvas(data['pos'][0], data['pos'][1], data['color'], name)
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
        max_len = max(len(v) for v in self.images)
        self.combo_box.configure(width=max_len)

        
    def save_canvas(self):
        if self.image_viewer is None: return

        file_path = fd.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG file", "*.png"), ("All Files", "*.*")]
        )

        if not file_path:
            return
        
        img = self.selected_image.get()
        data_pts = self.data_points[img]

        img = self.image_viewer.get_image__(self.point_radius.get(), data_pts)
        img.save(file_path)

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
        max_len = max(len(v) for v in self.images)
        self.combo_box.configure(width=max_len)
        self.combo_box.pack(side="left", padx=5, anchor="nw")
        self.combo_box.bind("<<ComboboxSelected>>", self.on_image_selection__)
    
    def display_new_image(self):
        self.toggle_data_points_off()
        if not hasattr(self, "selected_image"):
            return
        img_path = get_image_path(self.selected_image.get())
        if img_path is None:
            messagebox.showwarning("Image Not Found", f"The image {img_path} does not exist!")
            return
        print("image path is", img_path)
        if self.image_viewer is not None:
            # destroy current zoom image viewer
            self.image_viewer.destroy()
        self.image_viewer = CanvasImage(self, img_path)
        self.image_viewer.grid(row=1, column=1)
        self.data_point_selector.vars = {}
        # self.image_viewer.pack(side="top", fill="both", expand=True)

    
    def zoom_in__(self, event = None):
        if self.image_viewer is None:
            return
        self.image_viewer.zoom_in_option = not self.image_viewer.zoom_in_option
        self.image_viewer.zoom_out_option = False
        self.zoom_out_button.config(image=self.zoom_out_icon)
        if(self.image_viewer.zoom_in_option):
            self.zoom_in_button.config(image=self.zoom_in_activated_icon)
        else:
            self.zoom_in_button.config(image=self.zoom_in_icon)

        try:
            self.image_viewer.canvas.config(cursor="zoom-in" if self.image_viewer.zoom_in_option else "")
        except tk.TclError:
            self.image_viewer.canvas.config(cursor=config["ZoomInCursorFallback"] if self.image_viewer.zoom_in_option else "")


    def zoom_out__(self, event = None):
        if self.image_viewer is None:
            return
        self.image_viewer.zoom_out_option = not self.image_viewer.zoom_out_option
        self.image_viewer.zoom_in_option = False
        self.zoom_in_button.config(image=self.zoom_in_icon)
        if(self.image_viewer.zoom_out_option):
            self.zoom_out_button.config(image=self.zoom_out_activated_icon)
        else:
            self.zoom_out_button.config(image=self.zoom_out_icon)
        try:
            self.image_viewer.canvas.config(cursor="zoom-out" if self.image_viewer.zoom_out_option else "")
        except tk.TclError:
            self.image_viewer.canvas.config(cursor=config["ZoomOutCursorFallback"] if self.image_viewer.zoom_out_option else "")


    def on_image_selection__(self, event):
        print(f"Selected: {self.selected_image.get()}")
        self.display_new_image()
        self.update_data_point_selector()
    
    def update_delete_images_menu(self):
        if not hasattr(self, "delete_menu"):
            return
        self.delete_menu.delete(0, tk.END)
        for img in self.images:
            self.delete_menu.add_command(label=img, command= lambda : self.delete_image__(img))


    def delete_image__(self, name):
        delete_image(name)
        self.images = [Path(file_path).stem for file_path in load_image_paths()]
        self.data_points = get_data_points()
        if self.images == {} or len(self.images) == 0:
            self.images = []
            img_or_sync = askcustom(self, "No Images Found", "No images have been registered yet, please either sync with an external directory that has images, or select an image",
                                    "Sync", "Select Image")
            if img_or_sync == "Sync":
                set_external_sync()
                backup_from_sync()
            else:
                self.register_new_image()
            if len(self.images) == 0:
                messagebox.showerror("No Images Found", 
                            "Error, no images have been registered, unable to continue, either sync a directory or choose an image")
        assert len(self.images) == len(set(self.images)), "Error, you have an image in resources and in the images list that is duplicated"
        if self.selected_image.get() == name:
            self.selected_image.set(self.images[0])
        self.combo_box.configure(values=self.images)
        self.update_image_selector()
        self.check_data_points()
        self.update_delete_images_menu()
        self.display_new_image()
        self.update_data_point_selector()
 

    def register_new_image(self):
        # if hasattr(self, "data_point_selector") and self.data_point_selector is not None:
        #     if self.data_point_selector.popup and self.data_point_selector.popup.winfo_exists():
        #         self.data_point_selector.popup.destroy()
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
                self.update_delete_images_menu()
                if hasattr(self, "selected_image"):
                    self.selected_image.set(Path(new_image).stem)
                    self.display_new_image()
                    self.update_data_point_selector()
    
    def show_status(self, text):
        if self.status_window and self.status_window.winfo_exists():
            return

        self.status_window = tk.Toplevel(self)

        self.status_window.overrideredirect(True)
        self.status_window.attributes("-topmost", True)

        label = ttk.Label(self.status_window, text=text, padding=20)
        label.pack()

        self.status_window.update_idletasks()

        w = label.winfo_reqwidth()
        h = label.winfo_reqheight()

        self.update_idletasks()

        # x = self.winfo_rootx()
        # y = self.winfo_rooty()
        parent_w = self.winfo_width()
        popup_x = (parent_w // 2) - (w // 2)
        # popup_x = x + (parent_w // 2) - (w // 2)
        # popup_y = y - h - 10

        self.status_window.geometry(f"{w}x{h}+{popup_x}+0")
        # keep above the main window
        self.status_window.transient(self)

    def hide_status(self):
        if self.status_window and self.status_window.winfo_exists():
            self.status_window.destroy()
            self.status_window = None


if __name__ == '__main__':
    root = MainGui()
    root.mainloop()
