from bs4 import BeautifulSoup as BS
from urllib.parse import urljoin, urlparse, urlunparse
from WebParser import WebParser
from itertools import chain
import requests
import Utils
import os


class Spider:
    def __init__(self, url=None, path=None):
        self._url = "http://view.sdu.edu.cn/"
        self.set_url(url)
        self._host = "view.sdu.edu.cn"
        if Utils.is_path_exists_or_creatable(path):
            self._path = path
        else:
            self._path = "webCache"
        if not os.path.exists(self._path):
            os.mkdir(self._path)
        self._queue = []
        self._viewed = []
        self._counter = 0

    def _save_web(self, txt):
        web = WebParser()
        web.analyse(txt, self._url)

    def _prefetch(self):
        if self._url:
            return requests.head(self._url).headers['content-type'] == 'text/html'
        return False

    def _fetch(self):
        if self._prefetch():
            res = requests.get(self._url)
            self._viewed.append(self._url)
            if res.status_code == 200:
                self._counter += 1
                print('%d: %s' % (self._counter, self._url))
                html = res.content.decode('utf8')
                self._save_web(html)
                root = BS(html, 'lxml')
                for link in root.find_all('a'):
                    url = urljoin(self._url, link.get('href'))
                    parsed_url = urlparse(url)
                    url = urlunparse([*parsed_url[0:3], "", "", ""])
                    if Utils.is_valid_url(
                            url) and parsed_url.netloc == self._host and url not in chain(self._viewed, self._queue):
                        self._queue.append(url)
        elif self._url:
            self._viewed.append(self._url)

    def set_url(self, url):
        if Utils.is_valid_url(url):
            self._url = url

    def start(self):
        self._queue = []
        self._fetch()
        while len(self._queue):
            self._url = self._queue.pop(0)
            self._fetch()

    def start_from_url(self, url):
        self.set_url(url)
        self.start()


if __name__ == '__main__':
    sp = Spider()
    sp.start()
