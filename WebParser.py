from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse
from bs4.element import Comment
from bs4 import ResultSet
import jieba.analyse
import requests
import re


class WebParser:
    def __init__(self):
        self.title = "无标题"
        self.id = -1
        self.url = 'about:blank'
        self._tags = []

    def __repr__(self):
        return "<WebParser %d: %s>" % (self.id, self.title)

    def __str__(self):
        return ' '.join(self._tags)

    @staticmethod
    def _filter(element):
        if element.parent.name in ['select', 'input', 'textarea', 'style', 'script', 'head', 'title', 'meta',
                                   '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def _filter_and_tag(self, content):
        if isinstance(content, ResultSet):
            x_content = None
            for element in content:
                if x_content:
                    x_content += element.find_all(text=True)
                else:
                    x_content = element.find_all(text=True)
            content = x_content
        else:
            content = content.find_all(text=True)
        content = filter(self._filter, content)
        content = self.title + '\n' + '\n'.join(content)
        self._tags = jieba.analyse.extract_tags(content, topK=50)

    def _naive_analyse(self, root, url):
        main_body = root.find('div', attrs={'class': 'main_navbg'})
        if not main_body:
            print('lack template in url<%s>' % url)
            self._filter_and_tag(root)
        else:
            main_body = main_body.find_next('div', attrs={'class': 'le'})
            if not main_body:
                print('lack template in url<%s>' % url)
                self._filter_and_tag(root)
            else:
                self._filter_and_tag(main_body)

    def analyse(self, txt: str, url: str) -> list:
        if not txt or not url:
            print('empty content in url<%s>' % url)
            return []
        self.url = url
        parsed_url = urlparse(url)
        root = BS(txt, 'lxml')
        try:
            if parsed_url.path.startswith('/info/'):
                article = root.find('form', attrs={"name": "_newscontent_fromname"})
                self.title = article.find('h3').get_text()
                self._filter_and_tag(article.find('div', attrs={'class': 'news_content'}))
            elif parsed_url.path.startswith('/sdrw/'):
                main_body = root.find('div', attrs={'id': 'top'}).find_all_next('div', attrs={
                    'id': re.compile('wrap\d+')})
                self.title = root.find('div', attrs={'id': 'wrap_pos'}).find('h3').find_all('a')[-1].get_text()
                self._filter_and_tag(main_body)
            else:
                path_arr = parsed_url.path.split('/')
                self.title = root.title.get_text()
                if len(path_arr) == 2:
                    if path_arr[-1] in ['', 'index.htm']:
                        main_body = root.find('div', attrs={'class': 'w1000'}).find_all_previous('div',
                                                                                                 attrs={
                                                                                                     'class': 'w1012'})
                        self._filter_and_tag(main_body)
                    elif path_arr[-1] == 'sdrw.htm':
                        main_body = root.find('div', attrs={'id': 'top'}).find_all_next('div', attrs={
                            'id': re.compile('wrap\d+')})
                        self._filter_and_tag(main_body)
                    elif path_arr[-1] == 'xssdjt.htm':
                        main_body = root.find('div', attrs={'class': 'wrap'}).find('div', attrs={'class': None})
                        self._filter_and_tag(main_body)
                    elif path_arr[-1] in ['ypx.htm', 'zpx.htm']:
                        pageid = {
                            'ypx.htm': 125532,
                            'zpx.htm': 125531
                        }
                        res = requests.post('http://view.sdu.edu.cn/system/resource/js/news/hotdynpullnews.jsp',
                                            data={'owner': 1251758245, 'viewid': pageid[path_arr[-1]],
                                                  'actionmethod': 'getnewslist'})
                        if res.status_code == 200:
                            json = res.json()
                            json = map(lambda x: x['title'], json)
                            self._tags = jieba.analyse.extract_tags('\n'.join(json), topK=50)
                    else:
                        self._naive_analyse(root, url)
                else:
                    self._naive_analyse(root, url)
        except AttributeError:
            self._naive_analyse(root, url)
        self._tags = list(filter(lambda x: not re.compile('^(\.+)$').match(x), self._tags))
        return self._tags
