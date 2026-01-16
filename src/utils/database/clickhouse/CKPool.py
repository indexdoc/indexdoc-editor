import time
import datetime
import threading
import clickhouse_driver
import logging
import traceback

from utils import IDUtil

MAX_IDLE_SECONDS = 60*5  # 连接空闲时间（秒），链接如果空闲超过这个时间，则对连接进行关闭
LOOP_CHECK_IDLE_OVER_SECONDS = MAX_IDLE_SECONDS / 2
CHECK_VALID_SECONDS = 60  # 如果连接未使用超过这个数字，则需要对连接进行检测是否有效
MAX_CONNECT_COUNT = 30  # 最大连接数


class MyClient(clickhouse_driver.Client):
    def __init__(self, host, port, database, user, password):
        self.last_use_time = datetime.datetime.now()
        self.isbusy = False
        self.connect_id = IDUtil.get_long()
        super().__init__(host=host, port=port, database=database, user=user, password=password)

    def execute(self, query, params=None):
        return super().execute(query, params)

    def disconnect(self):
        super().disconnect()


class CKPool:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        # self.pool = dict()
        self.clients = list()  # 按使用顺序排序的连接
        self.isbusy = False
        thread = threading.Thread(target=self.close_all_idle_over)
        thread.daemon = True
        thread.start()
        # print(f'pool{self}')

    def _create_client(self):
        client = MyClient(host=self.host, port=self.port, database=self.database, user=self.user, password=self.password)
        self.clients.append(client)
        return client

    def _close_con(self, client):
        try:
            self.clients.remove(client)
            client.disconnect()
        except Exception as e:
            logging.error("disconnect ck connect err:%s" % e.__str__())
            logging.error("disconnect ck connect err:%s" % traceback.format_exc())

    def _is_idle_over(self, client):
        if datetime.datetime.now() - client.last_use_time > datetime.timedelta(seconds=MAX_IDLE_SECONDS):
            return True
        return False

    def close_all_idle_over(self):
        while True:
            time.sleep(LOOP_CHECK_IDLE_OVER_SECONDS)
            self.__check_pool_busy()
            self.isbusy = True
            idles = list()
            i = 0
            for i in reversed(range(len(self.clients))):
                _client = self.clients[i]
                if self._is_idle_over(_client) is True and _client.isbusy is False:
                    idles.append(_client)
            for _client in idles:
                _client.disconnect()
                self.clients.remove(_client)
            logging.debug('ckpool close idle client :%d / %d' % (len(idles),len(idles)+len(self.clients)))
            self.isbusy = False


    def __check_pool_busy(self):
        while self.isbusy:
            time.sleep(0.1)

    def get_client(self):
        self.__check_pool_busy()
        self.isbusy = True
        for i in reversed(range(len(self.clients))):
            _client = self.clients[i]
            if _client.isbusy is False and self._is_idle_over(_client) is False:
                self.clients.remove(_client)
                self.clients.append(_client)
                _client.isbusy = True
                self.isbusy = False
                return _client
        if len(self.clients) < MAX_CONNECT_COUNT:
            _client = self._create_client()
            # _client.busy = True
            _client.last_use_time = datetime.datetime.now()
            _client.isbusy = True
            self.isbusy = False
            return _client
        self.isbusy = False
        time.sleep(0.1)
        return self.get_client()

    def put_client(self, client):
        self.clients.remove(client)
        self.clients.append(client)
        client.isbusy = False

    def get_idle_count(self):
        cnt = 0
        for _client in self.clients:
            if _client.isbusy is False:
                cnt += 1
        return cnt

    def exesql(self,sql,params = None):
        _time_begin = time.time()
        logging.debug('ck sql %f: %s' % (_time_begin,sql))
        logging.debug('ck sql %f: params:%s' % (_time_begin,str(params)))
        client = None
        try:
            client = self.get_client()
            rts = client.execute(sql,params)
            logging.debug('ck sql %f success: count %d, time %f '%(_time_begin,len(rts) if rts is not None and not isinstance(rts,int) else 0,time.time()-_time_begin))
            return rts
        except Exception as e:
            logging.error('ck sql %f fail:%s' % (_time_begin, str(e)))
            # logging.error(traceback.format_exc())
            raise e
        finally:
            if client is not None:
                client.last_use_time = datetime.datetime.now()
                self.put_client(client)

# pool = CKPool(host='eky.cc', port=30266, database='ekydw', user='ekyadmin', password='Abcd1230-ekyck')
#


# def testexecute(query, idx):
#     logging.debug('idx:%s execute begin,db pool size: %s,idle size:%s' % (idx, len(pool.clients),pool.get_idle_count()))
#     client = None
#     try:
#         client = pool.get_client()
#         cnt = len(client.execute(query))
#         logging.debug('idx:%s result %s'%(idx,cnt))
#     except Exception as e:
#         logging.error(traceback.format_exc())
#         raise e
#     finally:
#         if client is not None:
#             client.last_use_time = datetime.datetime.now()
#             pool.put_client(client)
#
#     logging.debug('idx:%s execute end,db pool size: %s,idle size:%s' % (idx, len(pool.clients),pool.get_idle_count()))
#
# def _subtest():
#     import threading
#     for i in range(0,1):
#         print('select index %s begin'%str(i))
#         t = threading.Thread(target=testexecute,args=("select * from sys_user",i)).start()
#         # testexecute("select * from sys_user",i)
#         print('select index %s end'%str(i))
#     time.sleep(10)
#     for i in range(i, 2):
#         print('select2 index %s begin' % str(i))
#         t = threading.Thread(target=testexecute, args=("select * from sys_user", i)).start()
#         print('select2 index %s end' % str(i))
#
#
# def test():
#     logger = logging.getLogger()
#     logger.setLevel('DEBUG')
#     DATE_FORMAT = '%Y%m%d %H%M%S'
#     BASIC_FORMAT = "%(asctime)s:%(levelname)s:FILE(%(filename)s %(funcName)s %(lineno)d):%(message)s"
#     formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
#     consolehandler = logging.StreamHandler()  # 输出到控制台的handler
#     consolehandler.setFormatter(formatter)
#     logger.addHandler(consolehandler)
#     print('subtest begin')
#     _subtest()
#     threading.Thread(target=pool.close_all_idle_over).start()
#     print('subtest end')
#
#
# def test2():
#     from clickhouse_driver import Client
#     logger = logging.getLogger()
#     logger.setLevel('DEBUG')
#     DATE_FORMAT = '%Y%m%d %H%M%S'
#     BASIC_FORMAT = "%(asctime)s:%(levelname)s:FILE(%(filename)s %(funcName)s %(lineno)d):%(message)s"
#     formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
#
#     consolehandler = logging.StreamHandler()  # 输出到控制台的handler
#     consolehandler.setFormatter(formatter)
#     logger.addHandler(consolehandler)
#     testclient = clickhouse_driver.Client(host='43.228.77.219', port=30266, database='ekydw', user='ekyadmin', password='Abcd1230-ekyck')
#     for i in range(0,100):
#         ans = client.execute('select * from sys_user')
#         print(len(ans))

# test()