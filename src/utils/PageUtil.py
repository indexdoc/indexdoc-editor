import json

from utils import EntityUtil


def to_tabledata(total_count:int,entity_list:list):
    return to_tabledata_layui(total_count,entity_list)

def to_tabledata_layui(total_count:int,entity_list:list):
    _dict = {
        'code':0,
        'msg':None,
        'count':total_count,
        'data':None
    }
    _datadict = {}
    _ls = []
    for _e in entity_list:
        # _ls.append(_e.to_dict())
        _ls.append(EntityUtil.entity_to_dict(_e))

    _dict['data'] = _ls
    return _dict

