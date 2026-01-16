from copy import deepcopy

from base.BaseEntity import BaseEntity


def entitylist_to_tree(entity_list:list, entity_id_attrname, upper_id_attrname='upper_id',name_attrname = None):
    old_list = deepcopy(entity_list)
    new_list = list()
    for e in old_list:
        if getattr(e,upper_id_attrname) is None or getattr(e,upper_id_attrname) == 0:
            e.id_path = str(getattr(e,entity_id_attrname))
            if name_attrname is not None:
                e.name_path = getattr(e,name_attrname)
            else:
                e.name_path = None
            new_list.append(e)
    for e in new_list:
        old_list.remove(e)
    for e in new_list:
        _entitylist_get_child(e, old_list, entity_id_attrname, upper_id_attrname,name_attrname)
    return new_list

def _entitylist_get_child(entity:BaseEntity,old_list:list,entity_id_attrname,upper_id_attrname,name_attrname = None):
    entity_id = getattr(entity,entity_id_attrname)
    entity.child = list()
    for e in old_list:
        if getattr(e,upper_id_attrname)  ==  entity_id:
            e.id_path = getattr(entity,'id_path')+',' + str(getattr(e,entity_id_attrname))
            if name_attrname is not None:
                e.name_path = getattr(entity,'name_path') + ','+ str(getattr(e,name_attrname))
            else:
                e.name_path = None
            entity.child.append(e)
    for e in entity.child:
        old_list.remove(e)
    if len(old_list) == 0:
        return
    for e in entity.child:
        _entitylist_get_child(e,old_list,entity_id_attrname,upper_id_attrname,name_attrname)

def dictlist_to_tree(dict_list:list,entity_id_attrname,upper_id_attrname='upper_id',name_attrname = None):
    old_list = deepcopy(dict_list)
    new_list = list()
    for d in old_list:
        if d.get(upper_id_attrname) is None or d.get(upper_id_attrname)  == 0:
            new_list.append(d)
    for d in new_list:
        old_list.remove(d)
    for d in new_list:
        _dictlist_get_child(d, old_list, entity_id_attrname, upper_id_attrname,name_attrname)
    return new_list


def dictlist_to_tree2(dict_list:list,entity_id_attrname,upper_id_attrname='upper_id',up_id=0,name_attrname = None):
    old_list = deepcopy(dict_list)
    new_list = list()
    for d in old_list:
        if d.get(upper_id_attrname) is None or d.get(upper_id_attrname) == up_id:
            new_list.append(d)
    for d in new_list:
        old_list.remove(d)
    for d in new_list:
        _dictlist_get_child(d, old_list, entity_id_attrname, upper_id_attrname,name_attrname)
    return new_list

def _dictlist_get_child(dic:dict,old_list:list,entity_id_attrname,upper_id_attrname,name_attrname = None):
    entity_id = dic.get(entity_id_attrname)
    _child = list()
    for d in old_list:
        if d.get(upper_id_attrname)  ==  entity_id:
            _child.append(d)
    if len(_child) != 0:
        dic['child'] = _child
    for d in _child:
        old_list.remove(d)
    if len(old_list) == 0:
        return
    for d in _child:
        _dictlist_get_child(d,old_list,entity_id_attrname,upper_id_attrname,name_attrname)




