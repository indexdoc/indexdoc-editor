import decimal
import datetime

from utils import DTUtil


def object_to_str(o):
    if o is None or o == '':
        return None
    if isinstance(o,datetime.datetime):
        return DTUtil.datetime2str(o)
    return str(o)

def str_to_datetime(instr):
    try:
        dt = DTUtil.str2datetime(instr)
        return dt
    except Exception as e:
        return None

def str_to_int(instr):
    try:
        _rtn = int(instr)
        return _rtn
    except Exception as e:
        return None

def str_to_float(instr):
    try:
        _rtn = float(instr)
        return _rtn
    except Exception as e:
        return None

def str_to_decimal(instr):
    try:
        _rtn = decimal.Decimal(instr)
        return _rtn
    except Exception as e:
        return None
