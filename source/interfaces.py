from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo, showwarning
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog

from pdz_tool_extended.pdz_tool import PDZTool
from paths import create_folders, get_likenamed_filepaths_with_extension, get_filepaths_with_extension_in_directory


class BetterScrolledText(ScrolledText):
    def __init__(self, window=None):
        super().__init__(master=window)

    @property
    def is_disabled(self):
        is_disabled = True if 'disabled' in self["state"] else False
        return is_disabled

    def insert(self, position: str='end', text: str=""):
        """Override .insert() to allow for read-only insertion"""
        was_disabled = self.is_disabled
        if was_disabled:
            self.configure(state='normal')
        super().insert(position, text)
        if was_disabled:
            self.configure(state='disabled')

    def delete(self, start_val: str='1.0', end_val = tk.END):
        """Override .delete() to allow for read-only deletion"""
        was_disabled = self.is_disabled
        if was_disabled:
            self.configure(state='normal')
        super().delete(start_val, end_val)
        if was_disabled:
            self.configure(state='disabled')

    def replace(self, text: str=""):
        self.delete()
        self.insert('end', text)


class PdzToolGui(tk.Frame):
    def __init__(self, window=None, overwrite: bool=False):
        super().__init__(master=window)
        rowconfig = 2
        colconfig = 0

        window.grid_rowconfigure(rowconfig, weight=1)
        window.grid_columnconfigure(colconfig, weight=1)
        self._window = window

        self.grid()
        self.grid_rowconfigure(rowconfig, weight=1)
        self.grid_columnconfigure(colconfig, weight=1)

        self._pdz_file_paths = []
        self._pdz_folders = []
        self._csv_suffix = '.pdz'
        self._image_suffix = '-'
        self._image_record_name = 'Image Details'

        self.pdz_tools = []

        self._default_output_text = "No files or folder selected"

        self._save_csv = True
        self._save_jpg = True

        self._pad = (5, 5)

        row = -1

        # Draw Refresh and About box
        row += 1
        self.draw_about_button(row=row)

        # Draw Open buttons
        row += 1
        self.draw_open_buttons(row=row)

        # Draw output field
        row += 1
        self.draw_output(row=row)

        # Draw settings (include CSV's, include JPG's, overwrite)
        row += 1
        self.draw_settings(row=row, overwrite=overwrite)

        # Draw Extract & Save button
        row += 1
        self.draw_extract_and_save_button(row=row)

    def quit(self):
        self.destroy()

    @property
    def pdz_file_paths(self):
        return self._pdz_file_paths
    
    @pdz_file_paths.setter
    def pdz_file_paths(self, value: list=[]):
        self._pdz_file_paths = sorted(value)

    @property
    def pdz_folders(self):
        filepaths = self.pdz_file_paths
        folders = create_folders(paths=filepaths)
        return folders
    
    @property
    def predicted_output_filenames(self):
        filenames_pdzs = []
        pdzs = self.pdz_tools
        for pdz in pdzs:
            filenames = []
            stem_name = pdz.pdz_file_name

            csv_name = self.predict_csv_filename(stem_name)
            filenames.append(csv_name)

            image_record = pdz.parsed_data.get(self._image_record_name, 0)
            if not image_record:
                filenames.append("No images found in PDZ")
            else:
                n_images = image_record['num_images']
                image_names = self.predict_image_filenames(stem_name, n_images)
                filenames += image_names

            filenames_pdzs.append(filenames)

        return filenames_pdzs
    
    def predict_csv_filename(self, pdz_stem_name: str):
        suffix = self._csv_suffix
        predicted_name = pdz_stem_name + suffix + '.csv'
        return predicted_name
    
    def predict_image_filenames(self, pdz_stem_name: str, n: int):
        predicted_names = []
        suffix = self._image_suffix
        for i in range(n):
            predicted_names.append(pdz_stem_name + suffix + f'{i}.jpeg')
        return predicted_names
    
    @property
    def exists_output_filenames(self):
        predicted_filenames_by_pdz = self.predicted_output_filenames
        exists_filenames_by_pdz = []
        pdz_file_paths = self.pdz_file_paths
        for (i, pdz_file_path) in enumerate(pdz_file_paths):
            predicted_filenames = predicted_filenames_by_pdz[i]
            exists_filenames = []
            for predicted_filename in predicted_filenames:
                extension = predicted_filename.split(".")[-1]
                likenamed = get_likenamed_filepaths_with_extension(path=pdz_file_path, extension=extension)
                exists = any(predicted_filename in name for name in likenamed)
                exists_filenames.append(exists)
            exists_filenames_by_pdz.append(exists_filenames)

        return exists_filenames_by_pdz
    
    def draw_output(self, row: int):
        frame = tk.Frame(master=self._window)
        frame.grid(sticky="nsew",
                   column=0, row=row,
                   padx=(0,0), pady=(0,0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self._output_frame = frame

        text = self._default_output_text
        scroll = BetterScrolledText(frame)
        scroll.configure(state='disabled')
        scroll.grid(sticky="nswe",
                    column=0, row=0,
                    padx=self._pad, pady=self._pad)
        scroll.replace(text=text)
        self._scroll = scroll

    def update_exists_label(self):
        exists_filenames = self.exists_output_filenames
        label = self._exists_label
        if any(True in exists_filename for exists_filename in exists_filenames):
            text = "One or more output files already exist"
            foreground = "red"
        else:
            text = ""
            foreground = "black"
        label.config(text=text, foreground=foreground)

    def update_output(self):
        text = self._default_output_text
        folders = self.pdz_folders
        predicted_filenames = self.predicted_output_filenames
        exists_filenames = self.exists_output_filenames
        if folders:
            text = self.generate_output_text(folders, append_items=predicted_filenames, exists_items=exists_filenames)
        scroll = self._scroll
        scroll.replace(text=text)

    def update(self):
        self.update_output()
        self.update_exists_label()
        self.update_extract_and_save_button()

    def generate_output_text(self, folders: list=[], append_items: list=[], exists_items: list=[]):
        """Generate output text from a list of Folder objects, appended items, and whether those items exist."""
        folderbreak = "\n\n\n"
        filebreak = "\n\n"
        itembreak = "\n"
        tab = "    "
        text = ""
        exist_prefix_true = tab
        exist_prefix_false = tab[:-1] + "*"
        exist_suffix_true = tab + "-> File already exists"
        exist_suffix_false = ""
        a = -1
        for (i, folder) in enumerate(folders):
            level = 0
            lines = ""
            if i != 0:  # If not first, add paragraph break
                lines += folderbreak
            lines += folder.directory
            for (ii, filename) in enumerate(folder.filenames):
                a += 1
                level = 1
                lines += filebreak
                lines += tab*level
                lines += filename
                items = append_items[a]
                exists = exists_items[a]
                for (iii, item) in enumerate(items):
                    level = 2
                    exist = exists[iii]
                    if iii == 0:
                        lines += "\n"
                    lines += itembreak
                    lines += tab*(level-1)
                    if exist:
                        lines += exist_prefix_true
                    else:
                        lines += exist_prefix_false
                    lines += item
                    if exist:
                        lines += exist_suffix_true
                    else:
                        lines += exist_suffix_false

            text += lines

        return text

    def draw_open_buttons(self, row: int):
        frame = tk.Frame(master=self._window)
        frame.grid(sticky="ew",
                   column=0, row=row,
                   padx=(0,0), pady=(0,0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        self._open_frame = frame

        text = "Select File(s)..."
        button = ttk.Button(frame,
                            text=text,
                            command=self.clicked_open_files)
        button.grid(sticky="we",
                    column=0, row=0,
                    padx=self._pad, pady=self._pad)
        self._open_files = button
        Tooltip(button,
                text="Select individual PDZ file(s) to extract...""")

        label = ttk.Label(frame,
                          text="or")
        label.grid(sticky="",
                    column=1, row=0,
                    padx=self._pad, pady=self._pad)
        self._open_or = label

        text = "Select Folder... (Detect)"
        button = ttk.Button(frame,
                            text=text,
                            command=self.clicked_open_directory)
        button.grid(sticky="we",
                    column=2, row=0,
                    padx=self._pad, pady=self._pad)
        Tooltip(button,
                text="Select a folder containing PDZ files to detect and extract...""")
        self._open_folder = button

    def clicked_open_files(self):
        files = self.open_files_dialog()
        self.open_files(file_paths=files)

    def filter_list_by_endswith(self, list_of_str: list=[], ending: str=None):
        filtered_list = []
        for string in list_of_str:
            if string.endswith(ending):
                filtered_list.append(string)

        return filtered_list

    def open_files_dialog(self, initial_path: str=None):
        if not initial_path:
            existing_file_paths = self.pdz_file_paths
            initial_path = existing_file_paths[0] if existing_file_paths else None

        files = filedialog.askopenfilename(title="Select PDZ File(s)",
                                           multiple=True,
                                           initialdir=initial_path)
        return files

    def open_files(self, file_paths: str=[]):
        pdz_files = self.filter_list_by_endswith(file_paths, ending=".pdz")
        self.pdz_file_paths = pdz_files

        pdz_tools = []
        for file_path in self.pdz_file_paths:
            pdz_tool = PDZTool(file_path)
            pdz_tool.parse()
            pdz_tools.append(pdz_tool)
        
        self.pdz_tools = pdz_tools
        self.update()
        return True
    
    def clicked_open_directory(self):
        directory = self.open_directory_dialog()
        self.open_directory(directory=directory)

    def open_directory_dialog(self, initial_path: str=None):
        if not initial_path:
            existing_file_paths = self.pdz_file_paths
            initial_path = existing_file_paths[0] if existing_file_paths else None

        directory = filedialog.askdirectory(title="Select Folder with PDZ file(s)",
                                              initialdir=initial_path)
        return directory
    
    def open_directory(self, directory: str=[]):
        pdz_filepaths = get_filepaths_with_extension_in_directory(path=directory, extension=".pdz")
        self.open_files(pdz_filepaths)

    def draw_settings(self, row: int,
                           save_csv: bool=True,
                           save_jpg: bool=True,
                           overwrite: bool=False):
        frame = tk.Frame(master=self._window)
        frame.grid(sticky="sew",
                   column=0, row=row,
                   padx=(0,0), pady=(0,0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=0)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=0)
        self._settings_frame = frame
        col = -1

        col += 1
        self._save_csv_value = tk.BooleanVar(value=save_csv)
        checkbox = ttk.Checkbutton(
            frame,
            text="Include spectra and metadata (CSV)",
            variable=self._save_csv_value,
            onvalue=True,
            offvalue=False,
            command=self.update)
        checkbox.state(["selected"])
        checkbox.grid(sticky="w",
                      column=col, row=0,
                      padx=self._pad, pady=self._pad)
        Tooltip(checkbox,
                text="Save spectra during Extract & Save""")
        self._save_csv_checkbox = checkbox

        col += 1
        self._save_jpg_value = tk.BooleanVar(value=save_jpg)
        checkbox = ttk.Checkbutton(
            frame,
            text="Include images (JPEG)",
            variable=self._save_jpg_value,
            onvalue=True,
            offvalue=False,
            command=self.update)
        checkbox.state(["selected"])
        checkbox.grid(sticky="w",
                      column=col, row=0,
                      padx=self._pad, pady=self._pad)
        Tooltip(checkbox,
                text="Save images during Extract & Save""")
        self._save_jpg_checkbox = checkbox

        col += 1
        label = ttk.Label(frame,
                          text="",
                          foreground="red")
        label.grid(sticky="e",
                   column=col, row=0,
                   padx=self._pad, pady=self._pad)  
        self._exists_label = label
        
        col += 1
        self._overwrite_value = tk.BooleanVar(value=overwrite)
        checkbox = ttk.Checkbutton(
            frame,
            text="Overwrite existing?",
            variable=self._overwrite_value,
            onvalue=True,
            offvalue=False,
            command=self.update)
        if overwrite:
            checkbox.state([state])
        checkbox.grid(sticky="e",
                      column=col, row=0,
                      padx=self._pad, pady=self._pad)
        Tooltip(checkbox,
                text="Allow existing output spectra and image files to be overwritten during Extract & Save""")
        self._overwrite_checkbox = checkbox

    def draw_extract_and_save_button(self, row: int):
        text = "Extract & Save"
        button = ttk.Button(self._window,
                            text=text,
                            command=self.clicked_extract_and_save)
        button.grid(sticky="we",
                    column=0, row=row,
                    padx=self._pad, pady=self._pad)
        button.state(["disabled"])
        Tooltip(button, text="Extract output and save as files")
        self._extract_and_save_button = button

    def clicked_extract_and_save(self):
        pdzs = self.pdz_tools
        exists = self.exists_output_filenames
        overwrite = self.overwrite_value
        save_spectra = self.save_csv_value
        save_images = self.save_jpg_value
        saved, not_saved = self.save_files(
            pdzs=pdzs,
            exists=exists,
            overwrite=overwrite,
            save_spectra=save_spectra,
            save_images=save_images)
        title = self._window.title()
        n = len(saved) + len(not_saved)
        s = "s" if n > 1 else ""
        if saved:
            message = ""
            if n > 1:
                message += f"{len(saved)} of {n} "
            message += f"PDZ{s} successfully extracted and saved:\n\n"
            for file in saved:
                message += f"    {file}\n"
            message += "\n"
            showinfo(title, message)
        if not_saved:
            message = ""
            if n > 1:
                message += f"{len(not_saved)} of {n} "
            message += f"PDZ{s} not successfully extracted and saved:\n\n"
            for file in not_saved:
                message += f"    {file}\n"
            message += "\n"
            message += "Extraction is skipped if a CSV or JPEG from a PDZ already exists. Override this behavior by checking the 'Overwrite existing' box."
            showwarning(title, message)
        self.update()

    def save_files(self, pdzs: list=[], exists: list=[], overwrite: bool=False, save_spectra: bool=True, save_images: bool=True):
        saved = []
        not_saved = []
        if len(pdzs) != len(exists):
            not_saved = [(pdz.pdz_file_name + '.pdz') for pdz in pdzs]
            return saved, not_saved
        for pdz, exist in zip(pdzs, exists):
            file_name = (pdz.pdz_file_name + '.pdz')
            if any(exist) and not overwrite:
                not_saved.append(file_name)
            else:
                self.save_spectra_and_images(pdz, save_spectra, save_images)
                saved.append(file_name)
        return saved, not_saved
    
    @property
    def save_csv_value(self):
        return self._save_csv_value.get()
    
    @property
    def save_jpg_value(self):
        return self._save_jpg_value.get()
    
    @property
    def overwrite_value(self):
        return self._overwrite_value.get()

    def save_spectra_and_images(self, pdz: PDZTool, save_spectra: bool=True, save_images: bool=True):
        directory_path = Path(pdz.file_path).parent
        record_names = pdz.record_names
        parsed_data = pdz.parsed_data
        csv_suffix = self._csv_suffix
        image_suffix = self._image_suffix
        image_record_name = self._image_record_name

        if save_spectra:
            record_names_without_image = [x for x in record_names if x != image_record_name]
            pdz.save_csv(
                output_dir=directory_path,
                record_names=record_names_without_image,
                output_suffix=csv_suffix
                )
            
        if save_images:
            image_record = parsed_data.get(image_record_name, 0)
            if image_record:
                pdz.save_images(
                    output_dir=directory_path,
                    output_suffix=image_suffix
                    )

        
    def update_extract_and_save_button(self):
        button = self._extract_and_save_button

        files = self.pdz_file_paths

        save_csv = self.save_csv_value
        save_jpg = self.save_jpg_value
        
        overwrite_existing = self.overwrite_value
        existing_csv = False
        existing_jpg = False
        
        if files and any([save_csv, save_jpg]):
            if any([existing_csv, existing_jpg]) and not overwrite_existing:
                button.state(["disabled"])
            else:
                button.state(["!disabled"])
        else:
            button.state(["disabled"])

    def draw_about_button(self, row: int):
        col = -1

        frame = tk.Frame(master=self._window)
        frame.grid(sticky="ew",
                   column=0, row=row,
                   padx=(0,0), pady=(0,0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        col += 1
        label = ttk.Label(frame,
                          text="Extract spectra, metadata, and images from PDZ files")
        label.grid(sticky="",
                   column=col, row=0,
                   padx=self._pad, pady=self._pad)

        col += 1
        text = "?"
        button = ttk.Button(frame,
                            text=text,
                            command=self.show_about,
                            width=len(text)+2)
        button.grid(sticky="e",
                    column=col, row=0,
                    padx=self._pad, pady=self._pad)
        self._about_button = button
        Tooltip(button, text="About pdz-tool GUI...")

    def show_about(self):
        title = self._window.title()
        showinfo(title,
                 """pdz-tool GUI

https://github.com/olive-groves/pdz-tool-gui

MIT License

pdz-tool Copyright (c) 2024 Bruno Ducraux (github.com/bducraux), changes made by Lars Maxfield (github.com/larsmaxfield)

Interface created by Lars Maxfield (github.com/larsmaxfield)

Image extraction adapted from read_pdz Copyright (c) 2024 Frank Ligterink (github.com/fligt)

Icon by Good Stuff Non Sense, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")


class Tooltip:
    '''Add a tooltip for a given widget as the mouse goes on it.

    From: https://stackoverflow.com/a/41381685/20921535

    see:

    http://stackoverflow.com/questions/3221956/
           what-is-the-simplest-way-to-make-tooltips-
           in-tkinter/36221216#36221216

    http://www.daniweb.com/programming/software-development/
           code/484591/a-tooltip-class-for-tkinter

    - Originally written by vegaseat on 2014.09.09.

    - Modified to include a delay time by Victor Zaccardo on 2016.03.25.

    - Modified
        - to correct extreme right and extreme bottom behavior,
        - to stay inside the screen whenever the tooltip might go out on
          the top but still the screen is higher than the tooltip,
        - to use the more flexible mouse positioning,
        - to add customizable background color, padding, waittime and
          wraplength on creation
      by Alberto Vassena on 2016.11.05.

      Tested on Ubuntu 16.04/16.10, running Python 3.5.2

    TODO: themes styles support
    '''

    def __init__(self, widget,
                 *,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='widget info',
                 waittime=400,
                 wraplength=250):

        self.waittime = waittime  # in miliseconds, originally 500
        self.wraplength = wraplength  # in pixels, originally 180
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        def tip_pos_calculator(widget, label,
                               *,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            w = widget

            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])

            mouse_x, mouse_y = w.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                # No further checks will be done.

                # TIP:
                # A further mod might automagically augment the
                # wraplength when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        widget = self.widget

        # creates a toplevel window
        self.tw = tk.Toplevel(widget)

        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)

        win = tk.Frame(self.tw,
                       background=bg,
                       borderwidth=0)
        label = tk.Label(win,
                          text=self.text,
                          justify=tk.LEFT,
                          background=bg,
                          relief=tk.SOLID,
                          borderwidth=0,
                          wraplength=self.wraplength)

        label.grid(padx=(pad[0], pad[2]),
                   pady=(pad[1], pad[3]),
                   sticky=tk.NSEW)
        win.grid()

        x, y = tip_pos_calculator(widget, label)

        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None
