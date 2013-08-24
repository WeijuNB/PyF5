#coding:utf-8
import os
import sys
import time
from datetime import datetime
from types import NoneType
from schematics.models import Model


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
    """ 将对象转化为能直接json_encode的对象
    """
    if isinstance(o, dict):
        d = {}
        for key in o:
            d[key] = jsonable(o[key])
        return d
    elif type(o) in [list, tuple]:
        li = []
        for i, item in enumerate(o):
            li.append(jsonable(item))
        return li
    elif type(o) in [str, unicode, NoneType, bool, int, long, float]:
        return o
    elif type(o) == datetime:
        return time.mktime(o.timetuple())
    elif isinstance(o, Model):
        return o.dict()
    else:
        raise Exception('cant jsonable')


def config_path(app_folder):
    f5_config_folder = app_folder
    if sys.platform == 'win32':
        app_data_folder = os.getenv('APPDATA')
        if app_data_folder:
            f5_config_folder = os.path.join(app_data_folder, 'F5')
        elif os.path.expanduser("~"):
            f5_config_folder = os.path.join(app_data_folder, os.path.expanduser("~"))
    elif sys.platform in ('linux2', 'darwin'):
        if os.getenv('HOME'):
            f5_config_folder = os.getenv('HOME')

    if not os.path.exists(f5_config_folder):
        os.makedirs(f5_config_folder)

    return os.path.join(f5_config_folder, '.f5config')


if __name__ == '__main__':
    print get_rel_path(u'assets://index.html', 'assets://')