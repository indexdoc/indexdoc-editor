from domain import SysHandler
from domain.md_domain.handler.MdHandler import urls as md_urls
import client_config
import logging
import tornado

# 获取各个模块的url路由
urls = [
    (r'/client/public/(.*)', tornado.web.StaticFileHandler, {'path': client_config.public_path}),
    ('/', SysHandler.DefaultIndexHandler),
]
urls += SysHandler.urls
# 新增：添加 md 相关路由
urls += md_urls

settings = {
    # 注意：Tornado Application 不接受 'handlers' 参数，这是关键错误！
    # 'handlers': urls,  # 删掉这行
    'debug': True,
    'autoreload': False,
    'cookie_secret': '089883748324238429492348ssaasdfsdc',
    'default_handler_class': SysHandler.MyErrortHandler,
}
# 修正：handlers 应该作为第一个参数传入，而不是放在 settings 里
app = tornado.web.Application(urls, **settings)

def start_tornado(port, a):
    """ 启动 Tornado 服务器 """
    try:
        app.listen(port)
        logging.info(f"Tornado Web Server Start at Port {port}")
        tornado.ioloop.IOLoop.current().start()
    except Exception as e:
        pass
        logging.error(f"服务器启动失败: {e}")