import json
import tkinter
from pathlib import Path
from datetime import datetime

from api.sankaku import Sankaku

# Const
settings_path = Path("settings.json")
formatted_time = lambda: datetime.now().strftime("%I:%M:%S%p")


class SankakuDownloaderWindow(tkinter.Tk):
    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)

        # Set title and shit
        self.title("SankakuDownloader-Rewrite")
        self.geometry("640x360")
        self.minsize(640, 360)

        # ATTRs
        self.first_time: bool = False
        self.settings: dict = {}
        self.sankaku: Sankaku = None

        #
        self.load_settings()
        self.initialize_gui()

        if self.first_time:
            self.first_time_setup()

        self.finalize_gui()

    def save_settings(self) -> None:
        settings_path.write_text(json.dumps(self.settings, indent=4))

    def load_settings(self) -> None:
        settings: dict = {
            "download_folder": "downloads/",
            "access_token": "",
            "pages": "",
        }

        if not (settings_path).exists():
            # Make default settings
            print("[App] settings.json not found, creating one.")
            self.first_time = True
            self.settings.update(settings)
            self.save_settings()
        else:
            # File exists, load as is
            print("[App] settings.json found, reading.")
            self.settings = json.loads(settings_path.read_text())

    def initialize_gui(self) -> None:
        # Parent
        self.parent = tkinter.Frame(self, padx=10, pady=5)
        self.parent.pack(fill="x")
        self.parent.grid_columnconfigure(index=1, weight=1)

        # Top label for warning or something
        self.top_label = tkinter.Label(self.parent, text="doing your mom")
        self.top_label.grid(row=0, column=0, padx=2, columnspan=2, pady=5)

        # Query
        self.query_label = tkinter.Label(self.parent, text="Query:")
        self.query_entry = tkinter.Entry(self.parent)
        self.query_label.grid(row=1, column=0, sticky="w", padx=2)
        self.query_entry.grid(row=1, column=1, sticky="we", padx=2, columnspan=2)

        # Access Token
        self.access_token_label = tkinter.Label(self.parent, text="Token:")
        self.access_token_entry = tkinter.Entry(self.parent)
        self.access_token_label.grid(row=2, column=0, padx=2)
        self.access_token_entry.grid(row=2, column=1, padx=2, sticky="we")

        # Page
        self.page_label = tkinter.Label(self.parent, text="Page:")
        self.page_entry = tkinter.Entry(self.parent)
        self.page_label.grid(row=3, column=0, sticky="w", padx=2)
        self.page_entry.grid(row=3, column=1, sticky="w", padx=2, columnspan=2)

        # Download folder
        self.download_folder_label = tkinter.Label(self.parent, text="Folder:")
        self.download_folder_entry = tkinter.Entry(self.parent)
        self.download_folder_label.grid(row=4, column=0, padx=2)
        self.download_folder_entry.grid(row=4, column=1, padx=2, sticky="w")

        # Download button
        self.download_button = tkinter.Button(self.parent)
        self.download_button.configure(
            text="Download", command=self.on_click_download_button
        )
        self.download_button.grid(row=4, column=2)

        # "Logging"
        self.logging_text = tkinter.Text(self)
        self.logging_text.configure(state=tkinter.DISABLED)
        self.logging_text.pack(expand=tkinter.YES, fil=tkinter.BOTH)

    def log(self, *text: str) -> None:
        self.logging_text.configure(state=tkinter.NORMAL)
        self.logging_text.insert(
            tkinter.END, f"[{formatted_time()}] {' '.join(str(t) for t in text)}\n"
        )
        self.logging_text.see(tkinter.END)
        self.logging_text.configure(state=tkinter.DISABLED)

    def first_time_setup(self) -> None:
        #
        print("[App] First time running, doing some shit.")

        # Top label
        self.top_label.configure(
            text="Welcome to SankakuDownloader-Rewrite, please fill in the required textbox. \nThx :3"
        )

    def finalize_gui(self) -> None:
        """
        Just incase
        """
        if not self.settings["access_token"] and not self.first_time:
            self.top_label.configure(
                text="hey buddy you might want to fill in the access_token so everything works fine."
            )

        # Set
        self.page_entry.insert(0, self.settings["pages"])
        self.access_token_entry.insert(0, self.settings["access_token"])
        self.download_folder_entry.insert(0, self.settings["download_folder"])

        # Setup sankaku
        self.sankaku = Sankaku(self.settings["access_token"], logging_cb=self.log)

        # Done
        self.log("App launched!")

    # Events
    def on_click_download_button(self) -> None:
        # Save when downloading
        self.settings["download_folder"] = self.download_folder_entry.get()
        self.settings["access_token"] = self.access_token_entry.get()
        self.settings["pages"] = self.page_entry.get()
        self.save_settings()

        self.sankaku.update_access_token(self.settings["access_token"])

        # Not the best way to do this but itll do for now
        if (query := self.query_entry.get()).isnumeric():
            self.log("[App] Getting from ID!")
            posts = self.sankaku.get_from_id(query)
        else:
            self.log("[App] Getting from tags!")
            posts = self.sankaku.get_from_tags(query)

        if posts:
            self.sankaku.download_from(posts, self.settings["download_folder"])
        else:
            self.log("[App] Nothing found.")


if __name__ == "__main__":
    SankakuDownloaderWindow().mainloop()
