
def entity_to_dict(obj):
    pr = {}
    for name in dir(obj):
        value = getattr(obj, name)
        if not name.startswith('__') and not callable(value):
            pr[name] = value
    return pr

def entities_to_dict(entities:list):
    _ls = list()
    for e in entities:
        _ls.append(entity_to_dict(e))
    return _ls

def get_entity_attr(obj):
    attrs = []
    for name in dir(obj):
        value = getattr(obj, name)
        if not name.startswith('__') and not callable(value):
            attrs.append(name)
    return attrs

