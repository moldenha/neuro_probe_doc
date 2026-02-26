# Source - https://stackoverflow.com/a/48137257
# Posted by FooBar167, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-20, License - CC BY-SA 4.0

'''
Sam Notes: The basis of some of the features was coppied from stack overflow

The reason that this was taken from someone else/stack overflow is because
this is safer for larger images, and I don't need to reinvent anything here

Obviously some stuff was changed:
- Scrolling to zoom in and out was taken out
- Buttons added for explicit zooming in and zooming out
- The cursor changes for the scrolling
- Tkinter cursors to use:
    "zoom-in" and "zoom-out"
- Added a motion defined magnifying glass for choosing a point
- A way to click and register the place of the image
- A way to get the coordinate of the place over the image clicked
- A way to have it magnify as the cursor moves over the image (use the function that auto scrolls)

Stuff to add:
    (if more features to add, will be described here)


'''


# -*- coding: utf-8 -*-
# Advanced zoom for images of various types from small to huge up to several GB
import math
import warnings
import tkinter as tk

from tkinter import ttk
from PIL import Image, ImageTk

class AutoScrollbar(ttk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Cannot use place with the widget ' + self.__class__.__name__)

class CanvasImage:
    """ Display and zoom image """
    def __init__(self, placeholder, path, given_frame = False):
        """ Initialize the ImageFrame """
        self.data_draw_points = []
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__delta = 1.3  # zoom magnitude
        self.__filter = Image.Resampling.LANCZOS  # LANCZOS used for highest quality resizing
        self.__previous_state = 0  # previous state of the keyboard
        self.path = path  # path to the image, should be public for outer classes
        # Create ImageFrame in placeholder widget
        if given_frame:
            self.__imframe = placeholder
        else:
            self.__imframe = ttk.Frame(placeholder)  # placeholder of the ImageFrame object
        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Create canvas and bind it with scrollbars. Public for outer classes
        
        # Cursors to put in: "zoom-in" and "zoom-in"
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        # # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.__show_image())  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>',     self.__move_to)  # move canvas to the new position
        # This is to focus the canvas when the mouse enters the canvas
        # self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        # self.canvas.bind_all('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        # self.canvas.bind('<Shift-MouseWheel>', self.__wheel)  # zoom for MacOS, but not Linux or Windows
        # self.canvas.bind('<Button-5>',   self.__wheel)  # zoom for Linux, wheel scroll down
        # self.canvas.bind('<Button-4>',   self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = 1000000000  # suppress DecompressionBombError for big images
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
           self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [self.__image.tile[0][0],  # it have to be 'raw'
                           [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                           self.__offset,
                           self.__image.tile[0][3]]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()  # show image on the canvas
        self.canvas.focus_set()  # set focus on the canvas
        self.zoom_in_option = False
        self.zoom_out_option = False
        self.pos_input_fcn = None



    def smaller(self):
        """ Resize image proportionally and return smaller image """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k)+1), self.__filter), (0, int(i * k)))
            i += band
            j += 1
        print('\r' + 30*' ' + '\r', end='')  # hide printed string
        return image

    def redraw_figures(self):
        """ Dummy function to redraw figures in the children classes """
        pass

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
            # print(self.data_draw_points)
            # for data_pt in self.data_draw_points:
            #     img_x, img_y, color = data_pt
            #     self.draw_data_point(img_x, img_y, color)
    
    def show_image(self): self.__show_image()

    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        # print(f"zoom options are {self.zoom_in_option} and {self.zoom_out_option}")
        self.canvas.scan_mark(event.x, event.y)
        if self.zoom_in_option or self.zoom_out_option:
            self.__handle_zoom_click(event)
        if hasattr(self, "magnifier_on"):
            if self.magnifier_on:
                if self.pos_input_fcn is not None:
                    canvas_x = self.canvas.canvasx(event.x)
                    canvas_y = self.canvas.canvasy(event.y)
                    self.pos_input_fcn(self.img_coords(canvas_x, canvas_y))
                    self.pos_input_fcn = None
                else:
                    print("pos input fcn is none :/")
                self.togle_motion_picker()

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        if self.zoom_in_option or self.zoom_out_option:
            # print("options were true")
            return
        # else:
        #     print("options were false")
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas
    
    def img_coords(self, x, y):
        """
        Convert canvas (x, y) to image pixel coordinates.
        Returns (img_x, img_y) or None if outside image.
        """

        bbox = self.canvas.coords(self.container)  # img_area -> [x1, y1, x2, y2]
        # print(f"bbox: {bbox}")
        if not (bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]):
            return None  # outside image

        # Convert canvas → image coords
        img_x = (x - bbox[0]) / self.imscale
        img_y = (y - bbox[1]) / self.imscale

        return int(img_x), int(img_y)        


    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area
    
    def __handle_zoom_click(self, event):
        """ Handles zooming in and zooming out"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return # zoom only inside image
        if self.zoom_out_option and self.zoom_in_option: return # invalid
        scale = 1.0
        if self.zoom_out_option:
            # zoom out and make smaller
            if round(self.__min_side * self.imscale) < 30: return # image less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        else:
            # zoom in
            # bit shift for fast * 2
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        k = self.imscale * self.__ratio # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()
    
    def motion_magnifier__(self, event):
        if not self.magnifier_on:
            return
        size = 120          # size of magnifier box
        zoom_factor = 2.5 * self.imscale   # magnification level
        half = size // 2

        # Convert canvas coords to image coords
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        # print(f"canvas x and y: {canvas_x}, {canvas_y}, vs event: {event.x}, {event.y}")
        if self.outside(canvas_x, canvas_y): return # zoom only inside image
        img_x, img_y = self.img_coords(canvas_x, canvas_y) # <- with zoom taken out
        # bbox = self.canvas.coords(self.container)  # [x1, y1, x2, y2]
        # # Convert canvas → image coords
        # img_x = int(canvas_x - bbox[0])
        # img_y = int(canvas_y - bbox[1])

        # Crop region from original image
        crop_size = int(size / zoom_factor)
        left = img_x - crop_size // 2
        top = img_y - crop_size // 2
        right = img_x + crop_size // 2
        bottom = img_y + crop_size // 2

        cropped = self.motion_image__.crop((left, top, right, bottom))
        resized = cropped.resize((size, size), self.__filter)
        
        self.magnifier_photo = ImageTk.PhotoImage(resized)

        # Remove old magnifier
        self.canvas.delete("magnifier")

        # Draw zoomed image
        self.canvas.create_image(
            canvas_x,
            canvas_y,
            image=self.magnifier_photo,
            anchor="center",
            tags="magnifier"
        )
        
        # Draw circular border
        self.canvas.create_oval(
            canvas_x - half,
            canvas_y - half,
            canvas_x + half,
            canvas_y + half,
            outline="black",
            width=2,
            tags="magnifier"
        )

    # NOTE: The reason this is a function to togle the event on and off instead of a variable inside of
    # self.motion_magnifier__ is for performance, this way the function is only called when absolutely needed
    # Stack calls in any language would add an un-needed performance hinderance
    def togle_motion_picker(self):
        print("togle motion picker called")
        self.zoom_in_option = False
        self.zoom_outoption = False
        if getattr(self, "magnifier_on", False):
            self.canvas.unbind("<Motion>")
            self.canvas.config(cursor="")
            self.canvas.delete("magnifier")
            self.magnifier_on = False
            self.motion_image__ = None
        else:
            self.canvas.bind("<Motion>", self.motion_magnifier__)
            self.canvas.config(cursor="crosshair")  # Big plus style
            self.magnifier_on = True
            self.motion_image__ = Image.open(self.path)

    def draw_data_point(self, img_x, img_y, color, radius=5):
        """
        Draw a colored dot at image pixel coordinate (img_x, img_y)
        """
        bbox = self.canvas.bbox(self.container)
        if bbox is None:
            return

        x1, y1 = bbox[0], bbox[1]

        # Convert image coords → canvas coords
        canvas_x = x1 + img_x * self.imscale
        canvas_y = y1 + img_y * self.imscale

        r = radius * self.imscale

        self.canvas.create_oval(
            canvas_x - r,
            canvas_y - r,
            canvas_x + r,
            canvas_y + r,
            fill=color,
            outline="black",
            width=1,
            tags=f"data_point_{img_x}_{img_y}_{color}"
        )

        # items = self.canvas.find_withtag(f"data_point_{img_x}_{img_y}_{color}")
        # print(items)
        # print(self.canvas.itemconfig(items[0]))
        # print(self.canvas.coords(items[0]))
        # c_x1, c_
        # print((x1, y1))

    def edit_data_point_radius(self, img_x, img_y, color, new_radius):
        items = self.canvas.find_withtag(f"data_point_{img_x}_{img_y}_{color}")
        if len(items) == 0: return
        item_id = items[0]
        c_x1, c_y1, c_x2, c_y2 = self.canvas.coords(item_id)
        cx = int((c_x2 + c_x1) / 2)
        cy = int((c_y2 + c_y1) / 2)
        r = new_radius * self.imscale
        self.canvas.coords(item_id, cx - r, cy - r, cx + r, cy + r)
    
    def edit_data_point_radius(self, item_id, new_radius):
        c_x1, c_y1, c_x2, c_y2 = self.canvas.coords(item_id)
        cx = int((c_x2 + c_x1) / 2)
        cy = int((c_y2 + c_y1) / 2)
        r = new_radius * self.imscale
        self.canvas.coords(item_id, cx - r, cy - r, cx + r, cy + r)

    
    def remove_data_point(self, img_x, img_y, color):
        self.canvas.delete(f"data_point_{img_x}_{img_y}_{color}") 

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        # print("Wheel event triggered")
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 39, 102]:  # scroll right: keys 'D', 'Right' or 'Numpad-6'
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:  # scroll left: keys 'A', 'Left' or 'Numpad-4'
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:  # scroll up: keys 'W', 'Up' or 'Numpad-8'
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:  # scroll down: keys 'S', 'Down' or 'Numpad-2'
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()

def debug_event(event):
    print("Type:", event.type)
    print("Widget:", event.widget)
    print("Keysym:", getattr(event, "keysym", None))
    print("Keycode:", getattr(event, "keycode", None))
    print("Char:", getattr(event, "char", None))
    print("Delta:", getattr(event, "delta", None))
    print("Num:", getattr(event, "num", None))
    print("-" * 40)


class MainWindow(ttk.Frame):
    """ Main window class """
    def __init__(self, mainframe, path):
        """ Initialize the main Frame """
        ttk.Frame.__init__(self, master=mainframe)
        self.master.title('Advanced Zoom v3.0')
        self.master.geometry('800x600')  # size of the main window
        self.master.rowconfigure(0, weight=1)  # make the CanvasImage widget expandable
        self.master.columnconfigure(0, weight=1)
        canvas = CanvasImage(self.master, path)  # create widget
        canvas.grid(row=0, column=0)  # show widget
        # self.master.bind("<Enter>", lambda e: self.master.focus_set())
        # self.master.bind("<Enter>", lambda e: self.master.bind("<MouseWheel>", debug_event))
        # self.master.bind("<Leave>", lambda e: self.master.unbind("<MouseWheel>"))
        # self.master.bindtags(
        #     (self.master, "Canvas", ".", "all")
        # )
        # self.master.bind("<MouseWheel>", debug_event, add="+")
        # self.master.bind_all("<Any-KeyPress>", debug_event)
        # self.master.bind_all("<Any-KeyRelease>", debug_event)
        # self.master.bind_all("<Any-ButtonPress>", debug_event)
        # self.master.bind_all("<Any-ButtonRelease>", debug_event)
        # # self.master.bind_all("<MouseWheel>", debug_event)
        # self.master.bind_all("<Button-4>", debug_event)   # Linux scroll up
        # self.master.bind_all("<Button-5>", debug_event)   # Linux scroll down
        # # self.master.bind_all("<<Scroll>>", debug_event)
        # # self.master.bind_all("<Shift-MouseWheel>", debug_event)
        # self.master.bind_all("<Button>", debug_event)
        # self.master.bind_all("<Any>", debug_event)


if __name__ == '__main__':
    filename = '/Users/sam/projects/Freiwald/ProbeDocu/resources/images/image.jpeg'  # place path to your image here
    #filename = 'd:/Data/yandex_z18_1-1.tif'  # huge TIFF file 1.4 GB
    #filename = 'd:/Data/The_Garden_of_Earthly_Delights_by_Bosch_High_Resolution.jpg'
    #filename = 'd:/Data/The_Garden_of_Earthly_Delights_by_Bosch_High_Resolution.tif'
    #filename = 'd:/Data/heic1502a.tif'
    #filename = 'd:/Data/land_shallow_topo_east.tif'
    #filename = 'd:/Data/X1D5_B0002594.3FR'
    app = MainWindow(tk.Tk(), path=filename)
    app.mainloop()

