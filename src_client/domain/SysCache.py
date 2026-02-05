import os.path
import time
import tornado as tornado
from domain import SysTPL
import client_config
with open(client_config.favicon_file, 'rb') as fr:
    favicon = fr.read()

with open(client_config.default_index_file, 'rb') as fr:
    default_index = fr.read()
_page_map = dict()
_page_cache_time = time.time()
PAGE_CACHE_REFRESH_DURATION = 60  # 超过60秒，则清空缓冲
_loader = tornado.template.Loader(".")
def get_page(page_full_path: str):
    global _page_map, _loader
    if time.time() - _page_cache_time > PAGE_CACHE_REFRESH_DURATION:
        _page_map = dict()
    page_normpath = os.path.normpath(page_full_path)
    page_content = _page_map.get(page_normpath)
    if page_content is None:
        template = _loader.load(page_normpath)
        page_content = template.generate(tpldata=SysTPL.tpldata)
        _page_map[page_normpath] = page_content
    return page_content

