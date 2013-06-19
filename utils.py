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