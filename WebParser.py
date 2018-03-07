from bs4 import BeautifulSoup as BS
from bs4 import UnicodeDammit
from bs4.element import Comment
from urllib.parse import urlparse
import jieba.analyse


class WebParser:
    def __init__(self):
        self.title = "无标题"
        self.id = -1
        self._tags = []

    def __repr__(self):
        return "<WebParser %d: %s>" % (self.id, self.title)

    def __str__(self):
        return ' '.join(self._tags)

    @staticmethod
    def _filter(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def analyse(self, txt: str, url: str):
        parsed_url = urlparse(url)
        root = BS(txt)
        if parsed_url.path.startswith('/info/'):
            article = root.find('form', attrs={"name": "_newscontent_fromname"})
            self.title = article.find('h3').get_text()
            content = article.find('div', attrs={'class': 'news_content'})
            content = content.find_all(text=True)
            content = filter(self._filter, content)
            content = '\n'.join(content)
            self._tags = jieba.analyse.extract_tags(content, topK=50)
        else:
            self.title = root.title.get_text()
            content = root.find_all(text=True)
            content = filter(self._filter, content)
            content = '\n'.join(content)
            self._tags = jieba.analyse.extract_tags(content, topK=50)
        return self._tags
