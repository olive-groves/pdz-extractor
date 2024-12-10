"""Run the PDZ Extractor interface.
"""


from os import path
from platform import system
import tkinter as tk

from interfaces import PdzToolGui


VERSION = "1.0"


def main():
    window = tk.Tk()
    window.title("PDZ Extractor: GUI for pdz-tool")
    window.geometry('780x600')

    # Set icon based on operating system
    platformD = system()
    icon = None
    if platformD == 'Darwin':
        icon = 'icon.icns'
    elif platformD == 'Windows':
        icon = 'icon.ico'
    if icon:
        try:
            icon_path = path.abspath(path.join(path.dirname(__file__), icon))
            window.iconbitmap(icon_path)
        except:
            pass

    app = PdzToolGui(window=window, overwrite=False)
    app.mainloop()


if __name__ == "__main__":
    main()
