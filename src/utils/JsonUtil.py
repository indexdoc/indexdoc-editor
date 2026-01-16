import datetime
import functools
import json
import decimal

from base.BaseEntity import BaseEntity


class EkyJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, datetime.time):
            return obj.strftime("%H:%M:%S")
        elif isinstance(obj,decimal.Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return json.dumps(obj)
        elif isinstance(obj,BaseEntity):
            return obj.to_dict()
        else:
            return json.JSONEncoder.default(self, obj)

#设置json可以处理datetime格式
json.dumps = functools.partial(json.dumps, cls=EkyJsonEncoder)

def entitylist_2_dictlist(entity_list: list):
    _ls: list = []
    for e in entity_list:
        _ls.append(e.to_dict())
    return _ls

def entitylist_2_json(entity_list: list):
    _ls: list = []
    for e in entity_list:
        _ls.append(e.to_dict())
    return json.dumps(_ls,cls=EkyJsonEncoder)

def rec_entitylist_2_json(entity_list: list):
    _ls = []
    _ls: list = []
    for e in entity_list:
        _ls.append(e.to_dict())
