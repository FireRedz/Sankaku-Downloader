import time
import requests
import threading
from multiprocessing.pool import ThreadPool
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Name:
    en: str
    ja: str


@dataclass
class Url:
    sample: str
    preview: str
    file: str


@dataclass
class Post:
    id: int
    url: Url
    sequence: int  # For Doujin post

    @property
    def filename(self) -> str:
        if self.sequence:
            return f"{self.id}_{self.sequence}.{self.file_type}"

        return f"{self.id}.{self.file_type}"

    @property
    def file_type(self) -> str:
        # Assuming we're getting from the highest quality url
        return self.url.file.split("?", 1)[0].split(".")[-1]

    @property
    def download_url(self) -> str:
        """Kinda stupid cuz we already have `Post.url.x` but ok sure whatever"""
        return self.url.file

    @classmethod
    def from_dict(cls: "Post", data: dict) -> "Post":
        return cls(
            id=data["id"],
            url=Url(
                sample=data["sample_url"],
                preview=data["preview_url"],
                file=data["file_url"],
            ),
            sequence=data.get("sequence", 0),
        )


@dataclass
class Doujin:
    id: int
    name: Name
    description: str

    #
    is_public: bool
    is_active: bool
    is_flagged: bool

    #
    posts: list[Post]

    @property
    def download_urls(self) -> dict[int, str]:
        return {p.filename: p.download_url for p in self.posts}

    @classmethod
    def from_dict(cls: "Doujin", data: dict) -> "Doujin":
        # Convert name to Name object
        name = Name(en=data["name_en"], ja=data["name_ja"])

        # Convert posts to Post object
        posts = [Post.from_dict(post) for post in data["posts"]]

        # Done
        doujin = cls(
            id=data["id"],
            name=name,
            description=data["description"],
            posts=posts,
            is_public=data["is_public"],
            is_active=data["is_active"],
            is_flagged=data["is_flagged"],
        )

        return doujin


class Sankaku:
    API_URL: str = "https://capi-v2.sankakucomplex.com"
    API_HEADERS: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
    }

    # ATTRs
    session: requests.Session

    def __init__(self, access_token: str = None) -> None:
        # Init HTTP session
        self.session = requests.Session()
        self.session.headers.update(Sankaku.API_HEADERS)

        if access_token:
            self.session.headers["Authorization"] = f"Bearer {access_token}"

    def get_from_tags(self, tags: str) -> list[Post] | None:
        with self.session.get(
            f"{self.API_URL}/posts/keyset", params={"tags": tags}
        ) as res:
            if not res or res.status_code != 200:
                return print(f"[Sankaku] {tags} is Invalid.")

            # TODO: Page support

            posts = res.json()
            return [Post.from_dict(post) for post in posts["data"]]

    def get_from_id(self, id: int) -> Doujin | Post | None:
        with self.session.get(f"{self.API_URL}/pools/{id}") as res:
            if not res or res.status_code != 200:
                print("[Sankaku] Is not an Doujin, trying Post API.")
            else:
                print("[Sankaku] Found a doujin, reading!")

                doujin = Doujin.from_dict(res.json())

                # Print basic shit
                print(f"[Sankaku] Title: {doujin.name.en}")
                print(f"[Sankaku] Pages: {len(doujin.posts)} page")

                # Check for pages
                if not doujin.posts:
                    return print(
                        f"[Sankaku] API retrieved but no posts given, please use accessToken."
                    )

                return doujin  # Got what we want so lets fuck off

        # Fails on Doujin API, try post API
        with self.session.get(
            f"{self.API_URL}/posts",
            params={"page": 1, "limit": 1, "tags": f"id_range:{id}"},
        ) as res:
            if not res or res.status_code != 200:
                return print("[Sankaku] Failed to retrieved data even on post API!")
            else:
                # Sometimes Sankaku just returns nothing on "fucked up" posts so
                # check that too
                if not (res := res.json()):
                    return print(
                        "[Sankaku] API retrieved but no data received, please use accessToken."
                    )

                print(f"[Sankaku] Post retrieved!")

                # OK bruh
                res = res[0]

                return Post.from_dict(res)

    def download_from(
        self, doujin_or_post: Doujin | Post | list[Post], output_folder: Path = None
    ) -> None:
        if isinstance(doujin_or_post, Doujin):
            folder = doujin_or_post.name.en
            files_to_download = doujin_or_post.download_urls
        elif isinstance(doujin_or_post, list):
            folder = ""
            files_to_download = {post.id: post.filename for post in doujin_or_post}
        elif isinstance(doujin_or_post, Post):
            folder = ""
            files_to_download = {doujin_or_post.filename: doujin_or_post.download_url}
        else:
            print(type(doujin_or_post), "is not supported.")

        # Default download location
        if not output_folder:
            output_folder = Path("downloads") / folder

        # Make if doesnt exists
        if not output_folder.exists():
            output_folder.mkdir()

        def download_thread(
            session: requests.Session,
            files_to_download: dict[int, str],
            output_folder: Path,
        ) -> None:
            def download_process(args: list[object]) -> None:
                file, url = args
                with session.get(url) as res:
                    if not res or res.status_code != 200:
                        return print(f"[Sankaku] Failed to download file `{file}`")

                    # Save it
                    (output_folder / file).write_bytes(res.content)
                    print(f"[Sankaku] Donwloaded {file}!")

            ThreadPool(8).imap(
                download_process,
                [[file[0], file[1]] for file in files_to_download.items()],
            )

        thread = threading.Thread(
            target=download_thread,
            args=(self.session, files_to_download, output_folder),
            daemon=True,
        )
        thread.start()

        print("[Sankaku] Download thread started!")

        print("[Sankaku] Download thread finished!")


if __name__ == "__main__":
    # Doujin
    sankaku = Sankaku(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjE0MzUyMDgsInN1Ykx2bCI6MCwiaXNzIjoiaHR0cHM6Ly9jYXBpLXYyLnNhbmtha3Vjb21wbGV4LmNvbSIsInR5cGUiOiJCZWFyZXIiLCJhdWQiOiJjb21wbGV4Iiwic2NvcGUiOiJjb21wbGV4IiwiaWF0IjoxNjQwOTU1OTc5LCJleHAiOjE2NDExMjg3Nzl9.y4TkDX_ukr0vL_aDzgUAeJX2X0k3pMzZWWa8y3vgySk"
    )

    #
    print("> Doujin from ID")
    doujin = sankaku.get_from_id(441397)

    # Tagged posts
    print("> Tags")
    random_tag_post = sankaku.get_from_tags("sex")[-1]

    # Post
    print("> Post from ID")
    post = sankaku.get_from_id(29791343)

    # Try to download post
    print("> TEST: Downloading one image")
    sankaku.download_from(post)

    # Try to download doujin
    print("> TEST: Downloading doujin")
    sankaku.download_from(doujin)

    while True:
        ...
