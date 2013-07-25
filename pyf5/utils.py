#coding:utf-8
from datetime import datetime
import os
import sys
import time
from types import NoneType
from schematics.models import Model

PACKAGE_MODE = 'package'
FREEZE_MODE = 'freeze'
DEVELOP_MODE = 'develop'


def get_current_mode():
    if we_are_frozen():
        return FREEZE_MODE
    elif 'site-package' in module_path():
        return PACKAGE_MODE
    else:
        return DEVELOP_MODE


def get_rel_path(path, start_path):
    return normalize_path(os.path.relpath(path, start_path))


def normalize_path(path):
    return path.replace('\\', '/')


def we_are_frozen():
    return hasattr(sys, "frozen")


def app_path():
    if we_are_frozen():
        return unicode(sys.executable, sys.getfilesystemencoding())
    else:
        return unicode(__file__, sys.getfilesystemencoding())


def module_path():
    return os.path.dirname(app_path())


def config_path():
    f5_config_folder = module_path()
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


def path_is_parent(parent_path, maybe_child_path):
    rel_path = os.path.relpath(maybe_child_path, parent_path)
    return False if '..' in rel_path else True


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

if __name__ == '__main__':
    print get_rel_path(u'assets://index.html', 'assets://')