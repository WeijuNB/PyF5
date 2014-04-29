#coding:utf-8
import os
import sys
from pyf5.utils import config_path

VERSION = '4.3.1'
RELOADER_TAG = '<script id="_f5_script" src="/_/js/reloader.js"></script>'

# 默认不监控变更的文件/目录
DEFAULT_MUTE_LIST = [
    '.git',
    '.idea',
]

APP_FOLDER = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
RESOURCE_FOLDER = os.path.join(APP_FOLDER, '_')
CONFIG_PATH = config_path(APP_FOLDER)