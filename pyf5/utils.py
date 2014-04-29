#coding:utf-8
import os
import sys
import time
from datetime import datetime

import six


def get_rel_path(path, start_path):
    return normalize_path(os.path.relpath(path, start_path))


def normalize_path(path):
    return path.replace('\\', '/')


def path_is_parent(parent_path, maybe_child_path):
    rel_path = os.path.relpath(maybe_child_path, parent_path)
    return False if '..' in rel_path else True


def run_cmd(cmd):
    if sys.platform.startswith('win'):
        os.system(cmd.replace('/', '\\'))
    else:
        os.system(cmd.replace('\\', '/'))


def jsonable(o):
    """ 将对象转化为能直接json_encode的对象 """
    if isinstance(o, dict):
        return {key: jsonable(val) for key, val in o.items()}
    elif type(o) in [list, tuple]:
        return [jsonable(item) for item in o]
    elif type(o) == datetime:
        return time.mktime(o.timetuple())
    elif type(o) == six.types.GeneratorType:
        return jsonable(list(o))
    else:
        return o





if __name__ == '__main__':
    print get_rel_path(u'assets://index.html', 'assets://')