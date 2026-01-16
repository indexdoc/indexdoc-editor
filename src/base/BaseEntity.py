import json
class BaseEntity:
    def to_dict(self, recursive = True):
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith('__') and not callable(value):
                if isinstance(value, list):  # 如果类型是list
                    _ls = list()
                    for _sub_v in value:
                        if isinstance(_sub_v, BaseEntity):
                            if recursive:
                                _ls.append(_sub_v.to_dict(recursive = False))
                            else:
                                _ls.append(_sub_v.get_name())
                        else:
                            _ls.append(_sub_v)
                    value = _ls
                elif isinstance(value, BaseEntity):  # 如果是entity
                    if recursive:
                        value = value.to_dict(recursive = False)
                    else:
                        value = value.get_name()
                pr[name] = value
        return pr
    def to_json(self):
        return json.dumps(self.to_dict())

    def get_name(self):
        return None
