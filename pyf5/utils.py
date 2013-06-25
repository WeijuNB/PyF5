#coding:utf-8
import os
import sys


def get_rel_path(path, start_path):
    return os.path.relpath(path, start_path).replace('\\', '/')


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