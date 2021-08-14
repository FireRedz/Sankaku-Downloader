import os
import sys
import tkinter
import tkinter.filedialog
import threading

from tkinter import *
from Sankaku import Sankaku


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = getattr(sys, "_MEIPASS")
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(Tk):
    # string vars
    downloadFolderString = None

    # region Controls
    queryEntry = None
    queryLimit = None
    idEntry = None
    browseButton = None
    downloadButton = None
    logTextArea = None
    # endregion

    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_gui()

    def init_gui(self):
        self.title("Sankaku Downloader | GOT DAMN EDITION")
        self.geometry("420x300")
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        # region icon
        datafile = "resources\\icon.ico"
        if not hasattr(sys, "frozen"):
            datafile = os.path.join(os.path.dirname(__file__), datafile)
        else:
            datafile = os.path.join(sys.prefix, datafile)
        # endregion

        self.iconbitmap(default=resource_path(datafile))

        # region Panel Input
        gridpadding = 2
        parent = Frame(self, padx=10, pady=6)
        parent.pack(fill="x")
        parent.grid_columnconfigure(1, weight=1)

        # region Query
        temp = Label(parent, text="Query:")
        temp.grid(row=0, column=0, sticky="w", padx=gridpadding)

        self.queryEntry = Entry(parent)
        self.queryEntry.grid(
            row=0, column=1, sticky="we", padx=gridpadding, columnspan=2
        )

        # QUERY LIMIT
        temp = Label(parent, text="Page Limit:")
        temp.grid(row=1, column=0, sticky="w", padx=gridpadding)

        self.queryLimit = Entry(parent)
        self.queryLimit.grid(
            row=1, column=1, sticky="we", padx=gridpadding, columnspan=2
        )
        # endregion

        # fucking uhhh custom id thingy
        temp = Label(parent, text="ID:")
        temp.grid(row=2, column=0, sticky="w", padx=gridpadding)

        self.idEntry = Entry(parent)
        self.idEntry.grid(row=2, column=1, sticky="we", padx=gridpadding, columnspan=2)

        # region Download Folder
        temp = Label(parent, text="Download Folder:")
        temp.grid(row=3, column=0, sticky="w", padx=gridpadding)

        self.downloadFolderString = StringVar(self, value="downloads")
        self.downloadFolderEntry = Entry(parent, textvariable=self.downloadFolderString)
        self.downloadFolderEntry.grid(row=3, column=1, sticky="we", padx=gridpadding)

        self.browseButton = Button(
            parent, text="Select", command=self.browseButton_Click
        )
        self.browseButton.grid(row=3, column=2, sticky="e", padx=gridpadding)
        # endregion

        # region Download Button
        self.downloadButton = Button(parent)
        self.downloadButton.configure(
            text="Download", command=self.downloadButton_Click
        )
        self.downloadButton.grid(row=4, column=0, sticky="w", padx=gridpadding)
        # endregion
        # endregion

        self.logTextArea = Text(self)
        self.logTextArea.pack(expand=YES, fill=BOTH)

        # start window
        self.mainloop()

    def downloadButton_Click(self):
        # check if the path exists
        if not os.path.exists(self.downloadFolderEntry.get()):
            os.mkdir(self.downloadFolderEntry.get())

        task = Sankaku(
            self.queryEntry.get().strip(),
            self.downloadFolderEntry.get().strip(),
            self.idEntry.get().strip(),
            self.queryLimit.get().strip(),
            self.output,
        )
        thread = threading.Thread(target=task.download)
        thread.daemon = True

        self.output("[Thread] Thread started.")
        thread.start()

    def browseButton_Click(self):
        directory = tkinter.filedialog.askdirectory(
            parent=self, title="Choose Download Folder"
        )
        if directory != "":
            self.downloadFolderString.set(directory)

    def output(self, string):
        self.logTextArea.insert(END, string + "\r\n")
        self.logTextArea.see(END)


if __name__ == "__main__":
    MainWindow()
