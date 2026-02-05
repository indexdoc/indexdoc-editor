import threading
from tornado.web import RequestHandler

from domain import SysCache
import client_config

from domain.base_domain.BaseHandler import BasePageHandler
import os

lock = threading.RLock()


class DefaultIndexHandler(BasePageHandler):
    need_login = False

    def myget(self):
        self.set_header("Content-Type", "text/html")
        self.write(SysCache.default_index)


class MyErrortHandler(RequestHandler):
    error_content = None

    async def get(self):
        self.set_status(404)
        if self.__class__.error_content is None:
            with open(client_config.error_page_file, 'rb') as fr:
                self.__class__.error_content = fr.read()
        self.set_header("Content-Type", "text/html")
        self.write(self.__class__.error_content)


class FaviconHandler(BasePageHandler):
    need_login = False

    def myget(self):
        self.set_header("Content-Type", "image/vnd.microsoft.icon")
        self.write(SysCache.favicon)


class PageHandler(BasePageHandler):
    need_login = False

    def myget(self, *args, **kwargs):
        pagename: str = args[0]
        filepath = os.path.join(client_config.page_path, pagename)
        filepath = os.path.normpath(filepath)
        page_url = '/' + os.path.relpath(filepath, client_config.html_path)
        # 如果有文件名带数字的文件，则取带数字的文件，支持1-9的数字
        if pagename.endswith('.html'):
            _short_name = pagename[0:-5]
            for i in range(1, 10):
                _file_path = client_config.page_path + '/' + _short_name + str(i) + '.html'
                if os.path.exists(_file_path):
                    filepath = _file_path

        _content = SysCache.get_page(filepath)
        self.set_header("Content-Type", "text/html")
        self.write(_content)


class HtmlHandler(BasePageHandler):
    need_login = False

    def myget(self, *args, **kwargs):
        pagename: str = args[0]
        filepath = os.path.join(client_config.html_pc_path, pagename)
        filepath = os.path.normpath(filepath)
        page_url = '/' + os.path.relpath(filepath, client_config.html_path)
        # 如果有文件名带数字的文件，则取带数字的文件，支持1-9的数字
        if pagename.endswith('.html'):
            _short_name = pagename[0:-5]
            for i in range(1, 10):
                _file_path = client_config.page_path + '/' + _short_name + str(i) + '.html'
                if os.path.exists(_file_path):
                    filepath = _file_path

        _content = SysCache.get_page(filepath)
        self.set_header("Content-Type", "text/html")
        self.write(_content)


class SysPageHandler(BasePageHandler):
    page_content_dict = dict()

    def myget(self, *args, **kwargs):
        pagename = args[0]
        filepath = os.path.join(client_config.syspage_path, pagename)
        filepath = os.path.normpath(filepath)
        page_url = '/' + os.path.relpath(filepath, client_config.html_path)
        _content = SysCache.get_page(filepath)
        self.set_header("Content-Type", "text/html")
        self.write(_content)


urls = [
    (r'/pc/syspage/(.*)', SysPageHandler),
    ('/pc/404', MyErrortHandler),
    (r'/pc/page/(.*)', PageHandler),
    (r'/pc/(.*\.html)', HtmlHandler),
    ('/favicon.ico', FaviconHandler),
    ('/pc/favicon.ico', FaviconHandler),
]
