from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup as BS
from WebParser import WebParser
from itertools import chain
import requests
import Utils
import json
import os


class Spider:
    def __init__(self, url=None, path=None):
        self._url = "http://view.sdu.edu.cn/index.htm"
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
        self._matrix = {}
        self._map = {}

    def _parse_web(self, txt):
        web = WebParser()
        web.id = self._counter
        tags = web.analyse(txt, self._url)
        self._map[web.id] = [self._url, web.title]
        for tag in tags:
            if self._matrix.get(tag, None) is None:
                self._matrix[tag] = []
            self._matrix[tag].append(web.id)

    def _prefetch(self):
        if self._url:
            return requests.head(self._url).headers['content-type'] == 'text/html'
        return False

    def _decode(self, string, codecs=None):
        if codecs is None:
            codecs = ['utf8', 'gb18030', 'gbk', 'gb2312', 'big5']
        for i in codecs:
            try:
                return string.decode(i)
            except UnicodeDecodeError:
                pass

    def _fetch(self):
        if self._prefetch():
            res = requests.get(self._url)
            self._viewed.append(self._url)
            if 200 <= res.status_code < 300:
                self._counter += 1
                html = self._decode(res.content)
                self._parse_web(html)
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

    def start(self, web_count=-1):
        self._queue = []
        self._fetch()
        while len(self._queue) and web_count != 0:
            web_count -= 1
            if web_count < 0:
                web_count += 1
            self._url = self._queue.pop(0)
            self._fetch()

    def start_from_url(self, url):
        self.set_url(url)
        self.start()

    def save(self):
        with open(os.path.join(self._path, 'tag_matrix.json'), 'w+') as f:
            f.write(json.dumps(self._matrix))
        with open(os.path.join(self._path, 'url_mapping.json'), 'w+') as f:
            f.write(json.dumps(self._map))


if __name__ == '__main__':
    sp = Spider()
    sp.start()
    sp.save()
    print('finish')
