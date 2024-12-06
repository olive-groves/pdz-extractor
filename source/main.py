"""Run the pdz-tool interface.
"""


from os import path
from platform import system
import tkinter as tk

from interfaces import PdzToolGui


def main():
    window = tk.Tk()
    window.title("pdz-tool GUI")
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
