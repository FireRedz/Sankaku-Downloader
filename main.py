import os
import sys
import json
import tkinter
import tkinter.filedialog
import threading

from tkinter import *
from Sankaku import Sankaku
from pathlib import Path


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
    tokenEntryString = None
    tokenEntry = None
    logTextArea = None
    # endregion

    # settings
    settings: Path = Path("settings.json")
    download_folder: str = "downloads/"
    pages_limit: str = "1"  # theres some syntax on doujin thats why its a string
    access_token: str = ""

    def __init__(self):
        super(MainWindow, self).__init__()
        self.load_shit_from_settings()
        self.init_gui()

    def load_shit_from_settings(self) -> None:
        self.output("[Sankaku] Loading settings.json")

        if not self.settings.exists():
            self.output("[Sankaku] settings.json did not exists, creating one!")
            self.save_shit_into_settings()

        # load shit
        data = json.loads(self.settings.read_text())
        self.download_folder = data["download_folder"]
        self.access_token = data["access_token"]
        self.pages_limit = data["pages_limit"]

        self.output("[Sankaku] Loaded!")

    def save_shit_into_settings(self) -> None:
        self.output("[Sankaku] Saving shit into settings.json!")
        self.settings.write_text(
            json.dumps(
                {
                    "download_folder": self.download_folder,
                    "access_token": self.access_token,
                    "pages_limit": self.pages_limit,
                },
                indent=4,
            )
        )

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

        self.queryLimit = Entry(
            parent, textvariable=StringVar(self, value=self.pages_limit)
        )
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

        self.downloadFolderString = StringVar(self, value=self.download_folder)
        self.downloadFolderEntry = Entry(parent, textvariable=self.downloadFolderString)
        self.downloadFolderEntry.grid(row=3, column=1, sticky="we", padx=gridpadding)

        self.browseButton = Button(
            parent, text="Select", command=self.browseButton_Click
        )
        self.browseButton.grid(row=3, column=2, sticky="e", padx=gridpadding)
        # endregion

        # fucken token
        temp = Label(parent, text="Token:")
        temp.grid(row=4, column=0, sticky="w", padx=gridpadding)

        self.tokenEntryString = StringVar(self, value=self.access_token)
        self.tokenEntry = Entry(parent, textvariable=self.tokenEntryString)
        self.tokenEntry.grid(
            row=4, column=1, sticky="we", padx=gridpadding, columnspan=2
        )
        # endregion

        # region Download Button
        self.downloadButton = Button(parent)
        self.downloadButton.configure(
            text="Download", command=self.downloadButton_Click
        )
        self.downloadButton.grid(row=5, column=0, sticky="w", padx=gridpadding)
        # endregion

        self.logTextArea = Text(self)
        self.logTextArea.pack(expand=YES, fill=BOTH)

        # start window
        self.mainloop()

    def downloadButton_Click(self):
        # check if the path exists
        if not os.path.exists(self.downloadFolderEntry.get()):
            os.mkdir(self.downloadFolderEntry.get())

        # save shit into json
        self.download_folder = self.downloadFolderEntry.get().strip()
        self.access_token = self.tokenEntry.get().strip()
        self.pages_limit = self.queryLimit.get().strip()
        #
        self.save_shit_into_settings()

        task = Sankaku(
            self.queryEntry.get().strip(),
            self.download_folder,
            self.idEntry.get().strip(),
            self.pages_limit,
            self.access_token,
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
        if self.logTextArea:
            self.logTextArea.insert(END, string + "\r\n")
            self.logTextArea.see(END)
        else:
            print(string)


if __name__ == "__main__":
    MainWindow()
