import time
import traceback
from contextlib import contextmanager
import datetime
import threading
import psycopg2

import logging

from utils import IDUtil

MAX_IDLE_SECONDS = 60 * 5 #连接空闲时间（秒），链接如果空闲超过这个时间，则对连接进行关闭
CHECK_VALID_DURATION = 60 #如果连接未使用超过这个数字，则需要对连接进行检测是否有效
MAX_CONNECT_COUNT = 30 #最大连接数
LOOP_CHECK_IDLE_OVER_SECONDS = MAX_IDLE_SECONDS / 2

class MyConnect:
    def __init__(self,conn):
        self.conn = conn
        self.conn.autocommit = True
        self.last_use_time = datetime.datetime.now()
        self.busy = False
        self.connect_id = IDUtil.get_long()
    def cursor(self):
        return self.conn.cursor()
    def close(self):
        return self.conn.close()

class PGPool:
    def __init__(self, host,port,database,user,password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connects = list() #按顺序排的连接
        self.busy = False
        thread = threading.Thread(target=self.close_all_idle_over)
        thread.daemon = True
        thread.start()

    def _create_con(self):
        self.__check_pool_busy()
        self.busy = True
        conn = MyConnect(psycopg2.connect(host=self.host,port=self.port,database=self.database, user=self.user, password=self.password))
        self.connects.append(conn)
        self.busy = False
        return conn

    def _close_con(self,conn):
        try:
            conn.close()
            self.connects.remove(conn)
        except Exception as e:
            logging.error("close pg connect err:%s"%e.with_traceback())

    def _is_idle_over(self,conn):
        if datetime.datetime.now() - conn.last_use_time > datetime.timedelta(seconds=MAX_IDLE_SECONDS):
            return True
        return False

    def close_all_idle_over(self):
        while True:
            time.sleep(LOOP_CHECK_IDLE_OVER_SECONDS)
            self.__check_pool_busy()
            self.busy = True
            idles = []
            for _conn in self.connects:
                if _conn.busy is False and self._is_idle_over(_conn) is True:
                    idles.append(_conn)
            for _conn in idles:
                self._close_con(_conn)
            logging.debug('pgpool close idle connect :%s'%len(idles))
            self.busy = False

    def get_idle_count(self):
        cnt = 0
        for _conn in self.connects:
            if _conn.busy is False:
                cnt += 1
        return cnt

    def __check_pool_busy(self):
        while self.busy:
            time.sleep(0.1)

    def getconn(self):
        self.__check_pool_busy()
        self.busy = True
        for _conn in self.connects:
            if _conn.busy is False and self._is_idle_over(_conn) is False:
                _conn.busy = True
                _conn.last_use_time = datetime.datetime.now()
                self.busy = False
                return _conn
        self.busy = False
        if len(self.connects) <  MAX_CONNECT_COUNT:
            _conn = self._create_con()
            _conn.busy = True
            _conn.last_use_time = datetime.datetime.now()
            self.busy = False
            return _conn
        time.sleep(0.1)
        return self.getconn()

    def putconn(self, conn):
        self.connects.remove(conn)
        self.connects.append(conn)
        conn.busy = False
        conn.last_use_time = datetime.datetime.now()

    #批量执行语句时使用
    @contextmanager
    def get_cursor(self):
        con = None
        cursor = None
        try:
            con = self.getconn()
            cursor = con.cursor()
            yield cursor
        except psycopg2.Error as e:
            # logging.error(e)
            raise e
        finally:
            if cursor is not None:
                cursor.close()
            if con is not None:
                self.putconn(con)

    def exesql(self,sql,params = None):
        try:
            _time_begin = time.time()
            logging.debug('pg sql %f: %s' % (_time_begin, sql))
            logging.debug('pg sql %f: params:%s' % (_time_begin, str(params)))
            with self.get_cursor() as cursor:
                rts = cursor.execute(sql, params)
                logging.debug('ck sql %f success: count %d, time %f ' % (_time_begin, len(rts) if rts is not None else 0, time.time() - _time_begin))
                return rts
        except psycopg2.Error as e:
            logging.error('pg sql %f fail: %s' % (_time_begin, str(e)))
            logging.error(traceback.format_exc())
            raise e
        finally:
            pass

