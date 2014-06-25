#coding:utf-8
import os
import sys


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

    return os.path.join(f5_config_folder, 'f5config.json')


VERSION = '4.3.1'
RELOADER_TAG = '<script src="/_f5.js"></script>'

PUSH_CHANGES_DEBOUNCE_TIME = 0.3

# 默认监控变更的文件/目录
DEFAULT_EXTENSION_LIST = [
    '.js',
    '.css',
    '.png',
    '.jpg',
    '.htm',
    '.html',
    '.jade',
]

APP_FOLDER = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
RESOURCE_FOLDER = os.path.join(APP_FOLDER, '_')
CONFIG_PATH = config_path(APP_FOLDER)