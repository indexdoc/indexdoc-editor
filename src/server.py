
import SysUrl
from utils.JsonUtil import EkyJsonEncoder
import config
import logging
import json
import functools
import os
import tornado

# 设置json可以处理datetime格式
json.dumps = functools.partial(json.dumps, cls=EkyJsonEncoder)

# 对html的目录进行监听并自动重启
tornado.autoreload.watch(config.html_path)
for dirpath, dirnames, filenames in os.walk(config.html_path):
    for dirname in dirnames:
        full_path = os.path.join(dirpath, dirname)
        tornado.autoreload.watch(full_path)
    for filename in filenames:
        full_path = os.path.join(dirpath, filename)
        tornado.autoreload.watch(full_path)

# 获取各个模块的url路由
urls = [
    (r'/pc/static/(.*)', tornado.web.StaticFileHandler, {'path': config.static_path}),
    (r'/public/(.*)',tornado.web.StaticFileHandler,{'path': config.public_path}),
]


def custom_log_request(handler):
    status = handler.get_status()
    request_time = 1000.0 * handler.request.request_time()
    x_real_ip = handler.request.headers.get("X-Real-IP", "-")
    x_forwarded_for = handler.request.headers.get("X-Forwarded-For", "-")
    log_method = (logging.info if status < 400 else logging.warning if status < 500 else logging.error)
    log_method("%d %s (X-Real-IP=%s, X-Forwarded-For=%s) %.2fms",status,handler._request_summary(),x_real_ip,x_forwarded_for,request_time)


# settings参数说明
"""
一般设置(General settings):
autoreload: 如果为 True, 服务进程将会在任意资源文件 改变的时候重启, 正如 Debug模式和自动重载中描述的那样. 这个选项是Tornado 3.2中新增的; 在这之前这个功能是由 debug 设置控制的.
debug: 一些调试模式设置的速记, 正如 Debug模式和自动重载 中描述的那样. debug=True 设置等同于 autoreload=True, compiled_template_cache=False, static_hash_cache=False, serve_traceback=True.
default_handler_class 和 default_handler_args: 如果没有发现其他匹配则会使用这个处理程序; 使用这个来实现自 定义404页面(Tornado 3.2新增).
compress_response: 如果为 True, 以文本格式的响应 将被自动压缩. Tornado 4.0新增.
gzip: 不推荐使用的 compress_response 别名自从 Tornado 4.0.
log_function: 这个函数将在每次请求结束的时候调用以记录 结果(有一次参数, 该 RequestHandler 对象). 默认实现是写入 logging 模块的根logger. 也可以通过复写 Application.log_request 自定义.
serve_traceback: 如果为true, 默认的错误页将包含错误信息 的回溯. 这个选项是在Tornado 3.2中新增的; 在此之前这个功能 由 debug 设置控制.
ui_modules 和 ui_methods: 可以被设置为 UIModule 或UI methods 的映射提供给模板. 可以被设置为一个模块, 字典, 或一个模块的列表和/或字典. 参见 UI 模块 了解更多 细节.

认证和安全设置(Authentication and security settings):
cookie_secret: 被 RequestHandler.get_secure_cookie 使用, set_secure_cookie 用来给cookies签名.
key_version: 被requestHandler set_secure_cookie 使用一个特殊的key给cookie签名当 cookie_secret 是一个 key字典.
login_url: authenticated 装饰器将会重定向到这个url 如果该用户没有登陆. 更多自定义特性可以通过复写 RequestHandler.get_login_url 实现
xsrf_cookies: 如果true, 跨站请求伪造(防护) 将被开启.
xsrf_cookie_version: 控制由该server产生的新XSRF cookie的版本. 一般应在默认情况下(这将是最高支持的版本), 但是可以被暂时设置为一个较低的值, 在版本切换之间. 在Tornado 3.2.2 中新增, 这里引入了XSRF cookie 版本2.
xsrf_cookie_kwargs: 可设置为额外的参数字典传递给 RequestHandler.set_cookie 为该XSRF cookie.
twitter_consumer_key, twitter_consumer_secret, friendfeed_consumer_key, friendfeed_consumer_secret, google_consumer_key, google_consumer_secret, facebook_api_key, facebook_secret: 在 tornado.auth 模块中使用来验证各种APIs.

模板设置:
autoescape: 控制对模板的自动转义. 可以被设置为 None 以禁止转义, 或设置为一个所有输出都该传递过去的函数 name . 默认是 "xhtml_escape". 可以在每个模板中改变使用 {% autoescape %} 指令.
compiled_template_cache: 默认是 True; 如果是 False 模板将会在每次请求重新编译. 这个选项是Tornado 3.2中新增的; 在这之前这个功能由 debug 设置控制.
template_path: 包含模板文件的文件夹. 可以通过复写 RequestHandler.get_template_path 进一步定制
template_loader: 分配给 tornado.template.BaseLoader 的一个实例自定义模板加载. 如果使用了此设置, 则 template_path 和 autoescape 设置都会被忽略. 可 通过复写 RequestHandler.create_template_loader 进一步 定制.
template_whitespace: 控制处理模板中的空格; 参见 tornado.template.filter_whitespace 查看允许的值. 在Tornado 4.3中新增.

静态文件设置:
static_hash_cache: 默认为 True; 如果是 False 静态url将会在每次请求重新计算. 这个选项是Tornado 3.2中 新增的; 在这之前这个功能由 debug 设置控制.
static_path: 将被提供服务的静态文件所在的文件夹.
static_url_prefix: 静态文件的Url前缀, 默认是 "/static/".
static_handler_class, static_handler_args: 可 设置成为静态文件使用不同的处理程序代替默认的tornado.web.StaticFileHandler. static_handler_args, 如果设置, 应该是一个关键字参数的字典传递给处理程序 的 initialize 方法.
"""
settings = {
    'handlers': urls+SysUrl.urls,
    "log_function": custom_log_request,
    # 'template_path': template_path,
    'debug': True,
    'autoreload': True,
    'cookie_secret': '089883748324238429492348ssaasdfsdc',
}

# 也可以重载Application，实现更多自定义功能
app = tornado.web.Application(**settings)

try:
    logging.info("Tornado Web Server Starting ......")
    # 绑定监听端口号
    app.listen(config.port)
    logging.info("Tornado Web Server Start at Port %s" % (config.port,))
    # 启动监听
    tornado.ioloop.IOLoop.current().start()
except KeyboardInterrupt as e:
    logging.info('Tornado Web Server Stop By KeyboardInterrupt!')
    os._exit(0)
