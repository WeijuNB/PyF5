#coding:utf-8
import os
import sys
from pyf5.utils import config_path

VERSION = '4.2.0'

RELOADER_TAG = '<script id="_f5_script" src="/_/js/reloader.js"></script>'

DEFAULT_MUTE_LIST = [
    '.git',
    '.idea',
]

PRODUCTION_MODE = 'production'
DEVELOPMENT_MODE = 'development'
CURRENT_MODE = PRODUCTION_MODE if hasattr(sys, "frozen") else DEVELOPMENT_MODE

APP_FOLDER = None
if CURRENT_MODE == PRODUCTION_MODE:
    APP_FOLDER = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
    APP_FOLDER = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

RESOURCE_FOLDER = os.path.join(APP_FOLDER, '_')

CONFIG_PATH = config_path(APP_FOLDER)
