import inspect
import json

import config
from utils import IDUtil
from utils.TypeCvt import str_to_int
from utils.database.clickhouse.CKPool import CKPool
import threading
import time
import datetime

def exesql(sql,params = None,sys_user_id=None, op_type=''):
    #pool_exesql： 使用连接池
    _begin = time.time()
    _op_datetime = datetime.datetime.now()
    rts = pool_exesql(sql,params)
    _end = time.time()
    _duration = _end - _begin
    _current_user_id = _get_current_user_id()
    _op_type = _get_op_type()
    # todo 写数据库日志
    # threading.Thread(target=dblog, args=(sql, params,_op_datetime,_duration,rts,_current_user_id,_op_type)).start()
    return rts
    #simple_exesql：每次执行时重新连接
    # return simple_exesql(sql,params)
    #client_exesql ： 每次执行sql均使用同一个连接
    # return client_exesql(sql,params)

def dblog_file(sql,params,op_datetime,op_duration,sql_result,current_user_id,op_type):
    _sys_user_id = current_user_id
    _table_code,_sql_op_type = _get_table_code(sql)
    if _table_code == 'sys_db_log':
        return
    _op_type = _sql_op_type
    if _sql_op_type != 'SELECT' and op_type is not None:
        _op_type = op_type
    _data_id = _get_dataid(sql,params)
    _log_id = IDUtil.get_long()
    _dblog_params = [( _log_id,_sys_user_id,op_datetime ,op_duration ,_op_type ,_table_code ,_data_id ,\
                      sql ,json.dumps(params,ensure_ascii=False) if params is not None else None,json.dumps(sql_result,ensure_ascii=False) ,_log_id)]
    #todo save to file


def dblog(sql,params,op_datetime,op_duration,sql_result,current_user_id,op_type):
    dblog_sql = "insert into phy_sys_db_log(sys_db_log_id, sys_user_id, op_datetime, op_duration, op_type, table_code, data_id, sql_str, sql_param, sql_result,ver_id) values"
    _sys_user_id = current_user_id
    _table_code,_sql_op_type = _get_table_code(sql)
    if _table_code == 'sys_db_log':
        return
    _op_type = _sql_op_type
    if _sql_op_type != 'SELECT' and op_type is not None:
        _op_type = op_type
    _data_id = _get_dataid(sql,params)
    _log_id = IDUtil.get_long()
    _dblog_params = [( _log_id,_sys_user_id,op_datetime ,op_duration ,_op_type ,_table_code ,_data_id ,\
                      sql ,json.dumps(params,ensure_ascii=False) if params is not None else None,json.dumps(sql_result,ensure_ascii=False) ,_log_id)]
    pool_exesql(dblog_sql,_dblog_params)

def _get_dataid(sql,params):
    if isinstance(params,list) and len(params) > 0:
        if (isinstance(params[0],tuple) or isinstance(params[0],list)) and len(params[0])>0:
            _data_id = params[0][0]
            if isinstance(_data_id,int):
                return _data_id
            if isinstance(_data_id,str):
                return str_to_int(_data_id)
    if isinstance(params,dict) and len(params) > 0:
        for key in params:
            if str(key).endswith('_id'):
                _data_id = params.get(key)
                if isinstance(_data_id, int):
                    return _data_id
                if isinstance(_data_id, str):
                    return str_to_int(_data_id)
    if isinstance(params, int):
        return params
    if isinstance(params, str):
        return str_to_int(params)
    #如果参数中找不到数据ID，则从SQL语句中寻找
    _data_id = sql.rsplit('=')[-1].strip()
    if len(_data_id) == 16:
        return str_to_int(_data_id)
    return None

def _get_table_code(sql):
    _s_list = sql.split()
    op_type = None
    table_code = None
    if 'SELECT' == _s_list[0].upper():
        op_type = 'SELECT'
        for i in range(1,len(_s_list)):
            _s = _s_list[i].upper()
            if 'FROM' == _s:
                table_code = _s_list[i+1]
                break
    if 'INSERT' == _s_list[0].upper():
        op_type = 'INSERT'
        table_code = _s_list[2].split('(')[0]
    if table_code is not None:
        if table_code.startswith('vs_'):
            table_code = table_code[3:]
        elif table_code.startswith('v_'):
            table_code = table_code[2:]
        elif table_code.startswith('phy_'):
            table_code = table_code[4:]
    return table_code,op_type

def _get_myhandler():
    _framinfo = _search_stackframe('Handler.py')
    if _framinfo is not None:
        return _framinfo.frame.f_locals.get('self')
    return None

def _get_current_user_id():
    _myhandler = _get_myhandler()
    if _myhandler is not None:
        if hasattr(_myhandler,'user'):
            if _myhandler.user is not None:
                return _myhandler.user['sys_user_id']
    return None

def _get_op_type():
    _framinfo = _search_stackframe('DaoCK.py')
    if _framinfo is not None:
        _funname = _framinfo.function
        if _funname.find('update') != -1:
            return 'UPDATE'
        if _funname.find('delete') != -1:
            return 'DELETE'
        if _funname.find('insert') != -1:
            return 'INSERT'
        if _funname.find('select') != -1:
            return 'SELECT'
    return None

def _search_stackframe(filename):
    # print(inspect.stack())
    for _framinfo in reversed(inspect.stack()):
        if _framinfo.filename.endswith(filename):
            return _framinfo
    return None

#新起线程执行sql语句，无返回结果
def thread_exesql(sql,params = None):
    threading.Thread(target=exesql, args=(sql, params)).start()

pool = None
ck_config = config.ck_config
def pool_exesql(sql,params = None):
    global pool
    if pool is None:
        pool = CKPool(host=ck_config['host'], port=ck_config['port'], database=ck_config['database'], user=ck_config['user'],
                 password=ck_config['password'])
    return pool.exesql(sql,params)

def pool_client():
    return pool.get_client()

import logging
import time
import clickhouse_driver
import traceback
def simple_exesql(sql,params = None):
    _time_begin = time.time()
    logging.debug('ck sql %f: %s' % (_time_begin, sql))
    logging.debug('ck sql %f: params:%s' % (_time_begin, str(params)))
    client = None
    try:
        client = clickhouse_driver.Client(host=ck_config['host'], port=ck_config['port'],
                                          database=ck_config['database'], user=ck_config['user'],
                                          password=ck_config['password'])
        rts  = client.execute(sql, params)
        logging.debug('ck sql %f success: count %d, time %f ' % (
        _time_begin, len(rts) if rts is not None and not isinstance(rts, int) else 0, time.time() - _time_begin))
        return rts
    except Exception as e:
        logging.error('ck sql %f fail:%s' % (_time_begin, str(e)))
        # logging.error(traceback.format_exc())
        raise e
    finally:
        if client is not None:
            client.disconnect()

g_client = None
def client_exesql(sql,params = None):
    global  g_client
    _time_begin = time.time()
    # logging.debug('ck sql %f: %s' % (_time_begin, sql))
    # logging.debug('ck sql %f: params:%s' % (_time_begin, str(params)))
    client = None
    try:
        if g_client is None:
            g_client = clickhouse_driver.Client(host=ck_config['host'], port=ck_config['port'],
                                          database=ck_config['database'], user=ck_config['user'],
                                          password=ck_config['password'])
        client = g_client
        rts  = client.execute(sql, params)
        # logging.debug('ck sql %f success: count %d, time %f ' % (_time_begin, len(rts) if rts is not None and not isinstance(rts, int) else 0, time.time() - _time_begin))
        return rts
    except Exception as e:
        logging.error('ck sql %f fail:%s' % (_time_begin, str(e)))
        # logging.error(traceback.format_exc())
        raise e
def client_close():
    global g_client
    try:
        if g_client is not None:
            g_client.disconnect()
    except Exception as e:
        logging.error('ck close client fail:%s' % (str(e),))
        raise e
    finally:
        g_client = None

