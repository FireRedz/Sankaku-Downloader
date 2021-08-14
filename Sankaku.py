import requests
import json
from pathlib import Path

# region Sankaku stuff
API_URL = "https://capi-v2.sankakucomplex.com/"
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'}

POST_ID = "id"
POST_URL = "file_url"
POST_MIME = "file_type"
# endregion

class Sankaku:
    __session: requests.Session = None
    posts: list = []


    def __init__(self, tags: str, folder: str, custom_url: str, page_limit: str, print_fn: callable = None):
        self.tags = tags
        self.folder = Path(folder)
        self.custom_url = custom_url
        self.print = print_fn
        self.posts = []
        self.__session = requests.Session()

        if not page_limit.isdigit():
            self.output('[Sankaku] Invalid Page Limit Number, setting it to 1 instead.')
            self.page_limit = 1
        else:
            self.output(f'[Sankaku] Maximum page for query is {page_limit}')
            self.page_limit = int(page_limit)

    @staticmethod
    def __getFileType(url: str): 
        lastQuestionMark = url.rfind('?')
        lastDotBeforeQM = url.rfind('.',0,lastQuestionMark)
        #remove everything before .:?
        return url[lastDotBeforeQM:lastQuestionMark]

    def download_post(self, post: dict, folder: str):
        if(post[POST_URL] == None):
            self.output(f"[Sankaku] Can't download: {post}")

        r = self.__session.get(post[POST_URL])
        #open(folder+"\\"+str(post[POST_ID]) + self.__getFileType(post[POST_URL]), 'wb').write(r.content)
        target = self.folder / f'{post[POST_ID]}{self.__getFileType(post[POST_URL])}'
        target.write_bytes(r.content)

    def get_info_from_id(self, id: int):
        # either returns a list of images or just one
        # Check the doujin api first before the normal one image post
        #### Doujin api
        res = self.__session.get(f'https://capi-v2.sankakucomplex.com/pools/{id}?lang=en')

        if res.status_code != 200:
            self.output(f'[Sankaku] {id} is not a doujin/book, trying normal image api.')
        else:
            self.output(f'[Sankaku] {id} is a doujin/book, reading data!')

            data = res.json()
            
            return data['posts'], data['name_en']

        #### Normal api
        res = self.__session.get(f'https://capi-v2.sankakucomplex.com/posts?lang=en&page=1&limit=1&tags=id_range:{id}')
        
        if res.status_code != 200:
            return self.output('[Sankaku] Failed to get api data even on normal api, prolly an invalid id... Returning!')

        res = res.json()

        if len(res) == 0:
            return self.output('[Sankaku] API returns nothing, returning...'), None

        return [res[0]], None

    def get_posts(self):
        self.posts = []
        page = ""
        temp = []

        for _ in range(self.page_limit):
            if page == None:
                break

            temp = self._getPage(page)
            page = temp['meta']['next']
            self.posts.extend(temp['data'])

        return self.posts

    def _getPage(self, page: int = None):
        print(f'G({self.tags}): {page}')

        params = {
            'lang':'en',
            'limit':40,
            'tags':self.tags
        }

        if (page != None):
            params['next'] = page

        return json.loads(self.__session.get(API_URL + 'posts/keyset', params = params).content)

    def output(self, string: str):
        if self.print:
            self.print(string)

    def download(self):
        self.__session.headers['User-Agent'] = HTTP_HEADERS['User-Agent']

        # Check if theres custom url or some shit
        if len(self.custom_url) > 0:
            self.output('[Sankaku] Custom ID given, using that instead.')
            posts, folder_name = self.get_info_from_id(self.custom_url)

            if folder_name:
                self.output(f'[Sankaku] Saving downloads into {folder_name}')
                self.folder = self.folder / folder_name
        else:
            self.output('[Sankaku] No custom url given, downloading based off tags.')
            self.progress = 0
            posts = self.get_posts()

        # GOT DAMN
        if not posts:
            return self.output('[Sankaku] No Posts/Image found, returning.')

        if not self.folder.exists():
            self.output('[Sankaku] Download folder did not exists, creating!')
            self.folder.mkdir()

        total = len(posts)
        for i in range(total):
            self.output(f'[Sankaku] D({i+1}/{total}): {posts[i][POST_ID]}')
            self.download_post(posts[i],self.folder)

        self.output("[Sankaku] Complete")
