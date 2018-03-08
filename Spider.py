from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup as BS
from WebParser import WebParser
from itertools import chain
from time import sleep
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
            return requests.head(self._url).headers.get('content-type') == 'text/html'
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
            if res.status_code == 200:
                self._counter += 1
                html = self._decode(res.content)
                self._parse_web(html)
                if not html:
                    return
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

    def _save(self, path, obj):
        with open(os.path.join(self._path, path), 'w+') as f:
            f.write(json.dumps(obj))

    def _restore(self, path, default):
        full_path = os.path.join(self._path, path)
        if os.path.exists(full_path):
            with open(full_path) as f:
                return json.loads(f.read())
        return default

    def set_url(self, url):
        if Utils.is_valid_url(url):
            self._url = url

    def start(self, web_count=-1):
        self._fetch()
        while len(self._queue) and web_count != 0:
            web_count -= 1
            if web_count < 0:
                web_count += 1
            self._url = self._queue.pop(0)
            self._fetch()
            if self._counter % 100 == 0:
                self.save()
            if self._counter % 500 == 0:
                sleep(10)

    def start_from_url(self, url):
        self.set_url(url)
        self.start()

    def save(self):
        self._save('tag_matrix.json', self._matrix)
        self._save('url_mapping.json', self._map)
        self._save('spider_queue.cache', self._queue)

    def restore(self):
        self._matrix = self._restore('tag_matrix.json', self._matrix)
        self._map=self._restore('url_mapping.json', self._map)
        self._queue=self._restore('spider_queue.cache', self._queue)
        self._viewed = list(map(lambda x: x[0], self._map.values()))
        if len(self._queue):
            self._url = self._queue.pop(0)
        if len(self._map):
            self._counter = max(map(lambda x: int(x), self._map.keys()))



if __name__ == '__main__':
    sp = Spider()
    sp.restore()
    sp.start()
    sp.save()
    print('finish')
