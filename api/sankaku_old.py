import re
import requests
import json
from pathlib import Path

# region Sankaku stuff
API_URL = "https://capi-v2.sankakucomplex.com/"
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
}

POST_SEQUENCE = "sequence"
POST_ID = "id"
POST_URL = "file_url"
POST_MIME = "file_type"
POST_SIZE = "file_size"
# endregion


class Sankaku:
    __session: requests.Session = None
    posts: list = []

    def __init__(
        self,
        tags: str,
        folder: str,
        custom_url: str,
        page_limit: str,
        access_token: str,
        print_fn: callable = None,
    ):
        self.tags = tags
        self.folder = Path(folder)
        self.custom_url = custom_url
        self.print = print_fn
        self.posts = []
        self.token = access_token
        self.minimum_page = 0
        self.__session = requests.Session()

        if self.token:
            self.output("[Sankaku] Token detected, using token!")
            self.__session.headers["Authorization"] = f"Bearer {self.token}"

        if not page_limit.isdigit():
            # Page Syntax
            self.output("[Sankaku] Using page syntax, parsing!")
            if len(items := page_limit.split("-")) >= 2:
                self.output(f"[Sankaku] min_page: {items[0]} - max_page: {items[1]}")
                self.minimum_page = max(int(items[0]), 1)
                self.page_limit = int(items[1])

                if self.minimum_page > self.page_limit:
                    self.output(
                        f"[Sankaku] min_page is higher than max_page, setting it to max_page - 1!"
                    )
                    self.minimum_page = self.page_limit - 1
            else:
                self.output("[Sankaku] Invalid syntax, settings to default value!")
                self.page_limit = 1
        else:
            self.output(
                f"[Sankaku] No custom syntax defined, page_limit is {page_limit}"
            )
            self.page_limit = max(int(page_limit), 1)

    @staticmethod
    def __getFileType(url: str):
        lastQuestionMark = url.rfind("?")
        lastDotBeforeQM = url.rfind(".", 0, lastQuestionMark)
        # remove everything before .:?
        return url[lastDotBeforeQM:lastQuestionMark]

    @staticmethod
    def make_safe_filename(name: str) -> str:
        return re.sub(r"(?u)[^-\w.]", " ", name.strip()).strip()

    def download_post(self, post: dict, folder: str):
        if post[POST_URL] == None:
            self.output(f"[Sankaku] Can't download: {post}")

        r = self.__session.get(post[POST_URL])
        target = (
            self.folder
            / f"{post.get(POST_SEQUENCE, post[POST_ID])}{self.__getFileType(post[POST_URL])}"
        )
        target.write_bytes(r.content)

    def get_info_from_id(self, id: int):
        #### Doujin api
        if (
            res := self.__session.get(
                f"https://capi-v2.sankakucomplex.com/pools/{id}?lang=en",
            )
        ).status_code != 200:
            self.output(
                f"[Sankaku] {id} is not a doujin/book, trying normal image api."
            )
        else:
            self.output(f"[Sankaku] {id} is a doujin/book, reading data!")

            data = res.json()
            posts = data["posts"]

            # crop posts based on min_page and max_page
            if self.minimum_page > 0:
                posts = posts[self.minimum_page - 1 : self.page_limit]
            return posts, data["name_en"]

        #### Normal api
        if (
            res := self.__session.get(
                f"https://capi-v2.sankakucomplex.com/posts?lang=en&page=1&limit=1&tags=id_range:{id}",
            )
        ).status_code != 200:
            return self.output(
                "[Sankaku] Failed to get data! It's either Invalid token or Invalid ID."
            )

        if len(res := res.json()) == 0:
            self.output("[Sankaku] API returns nothing, returning..."), None

        return [res[0]], None

    def get_posts(self):
        self.posts = []
        page = ""
        temp = []

        # get page to the max
        for i in range(self.page_limit):
            if page == None:
                break

            # check if index is equal or higher than minimum
            if i >= self.minimum_page - 1:
                temp = self._getPage(page)
                page = temp["meta"]["next"]
                self.posts.extend(temp["data"])

        return self.posts

    def _getPage(self, page: int = None):
        print(f"G({self.tags}): {page}")

        params = {"lang": "en", "limit": 40, "tags": self.tags}

        if page != None:
            params["next"] = page

        return json.loads(
            self.__session.get(
                API_URL + "posts/keyset",
                params=params,
            ).content
        )

    def output(self, string: str):
        if self.print:
            self.print(string)

    def download(self):
        self.__session.headers["User-Agent"] = HTTP_HEADERS["User-Agent"]

        # Check if theres custom url or some shit
        if len(self.custom_url) > 0:
            self.output("[Sankaku] Custom ID given, using that instead.")
            posts, folder_name = self.get_info_from_id(self.custom_url)

            if folder_name:
                self.output(f"[Sankaku] Saving downloads into {folder_name}")
                self.folder = self.folder / self.make_safe_filename(folder_name)

            if not posts:
                if not self.token:
                    self.output("[Sankaku] Warning: Content is locked behind account.")
                    self.output(
                        "[Sankaku] Warning: You might need to pass the token for this to work."
                    )
                    self.output(
                        '[Sankaku] You can get token from your browser cookies, its called "accessToken"'
                    )
                else:
                    self.output(
                        "[Sankaku] Warning: Invalid token! Please renew the token from your browser!"
                    )
        else:
            self.output("[Sankaku] No custom url given, downloading based off tags.")
            self.progress = 0
            posts = self.get_posts()

        # GOT DAMN
        if not posts:
            return self.output("[Sankaku] No Posts/Image found, returning.")

        if not self.folder.exists():
            self.output("[Sankaku] Download folder did not exists, creating!")
            self.folder.mkdir()

        total = len(posts)
        for i in range(total):
            self.output(
                f"[Sankaku] D({i+1}/{total}): {posts[i][POST_ID]} | {posts[i][POST_SIZE] // 1000}kb"
            )
            self.download_post(posts[i], self.folder)

        self.output("[Sankaku] Complete")
