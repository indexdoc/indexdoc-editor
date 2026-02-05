import json
import time

#每1分钟自动刷新
REFRESH_DURATION = 60

class TPLData:
    def __init__(self):
        self._sys_dict_list = None
        self._last_select_time = time.time()

    def get_alldict(self):
        if self._sys_dict_list is None or time.time() - self._last_select_time > REFRESH_DURATION:
            self._sys_dict_list = []
            self._last_select_time = time.time()
        return self._sys_dict_list

    def get_dict(self,table_name, column_name, module_name=None):
        _dict_list = self.get_alldict()
        for e in _dict_list:
            if e.table_name == table_name and e.column_name == column_name and (
                    module_name is None or module_name == e.module_name):
                return e
        return None

    def json_decode(self,jsonstr):
        return json.loads(jsonstr)

tpldata = TPLData()
