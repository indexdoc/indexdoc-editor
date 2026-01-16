import os

#PC端后台界面
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取上一级目录路径
# base_path = os.getcwd()  # 获取系统目录路径
html_path = os.path.join(base_path, 'html')
favicon_file = os.path.join(base_path, 'html/logo-indexdoc.ico')
static_path = os.path.join(base_path, 'html/pc/static')  # 无需登陆也可以访问的资源
public_path = os.path.join(base_path, 'html/pc/public')  # 需要用户登陆才能访问，但是不需要配置用户权限
tmp_path = os.path.join(base_path, 'tmp')
rpt_path = os.path.join(base_path, 'rpt')
user_file_path = os.path.join(base_path, 'user_file')  # 用户上传文件目录
log_path = os.path.join(base_path, 'log')
if not os.path.exists(tmp_path):
    os.makedirs(tmp_path)
if not os.path.exists(rpt_path):
    os.makedirs(rpt_path)
if not os.path.exists(user_file_path):
    os.makedirs(user_file_path)
if not os.path.exists(log_path):
    os.makedirs(log_path)

port = 50003
ck_config = {
    # 'host': os.environ.get('NL_DB_HOST'),
    # 'port': os.environ.get('NL_DB_PORT'),
    # 'host': '10.0.3.1',
    'host': '127.0.0.1',
    'port': '9000',
    'user': 'default',
    'password': '',
    'database': 'default'
}


# 设置线程池最大线程数量
from concurrent.futures import ThreadPoolExecutor
import asyncio

max_workers = 16  # 设置线程池的最大数量，系统默认为min(32, (os.cpu_count() or 1) + 4)
executor = ThreadPoolExecutor(max_workers=max_workers)
asyncio.get_event_loop().set_default_executor(executor)

# 设置日志输出
import logging

logger = logging.getLogger()
logger.setLevel('INFO')
DATE_FORMAT = '%Y%m%d %H%M%S'
BASIC_FORMAT = "%(asctime)s:%(levelname)s:FILE(%(filename)s %(funcName)s %(lineno)d):%(message)s"
formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
consolehandler = logging.StreamHandler()  # 输出到控制台的handler
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)
# 按天存放日志文件
from logging.handlers import TimedRotatingFileHandler

filehandler = TimedRotatingFileHandler(filename=log_path + '/server.log', when='midnight', interval=1, backupCount=365)
filehandler.setFormatter(formatter)
filehandler.setLevel(logging.DEBUG)
logger.addHandler(filehandler)
