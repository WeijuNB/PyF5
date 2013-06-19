#coding:utf-8
import os
import sys
import stat
from collections import namedtuple
from utils import get_rel_path


VirtualFile = namedtuple('VirtualFile', 'path, size, modified_at, created_at, bytes')


class VFS(object):
    def __init__(self, vf_dict):
        self.vf_dict = vf_dict

    def get_file(self, rel_path):
        return self.vf_dict.get(rel_path, None)

    @classmethod
    def make_VFS_dict(cls, root_path):
        root_path = os.path.abspath(root_path)
        data = {}
        for root, dirs, files in os.walk(root_path):
            for file_name in files:
                abs_path = os.path.join(root, file_name)
                rel_path = unicode(get_rel_path(abs_path, root_path), sys.getfilesystemencoding())
                data[rel_path] = cls.make_virtual_file(root_path, abs_path)
                print 'making...', rel_path
        return data

    @classmethod
    def make_virtual_file(cls, root_path, abs_path):
        _bytes = open(abs_path, 'rb').read()
        rel_path = get_rel_path(abs_path, root_path)
        stats = os.stat(abs_path)
        vf = VirtualFile(
            rel_path,
            len(_bytes),
            stats[stat.ST_MTIME],
            stats[stat.ST_CTIME],
            _bytes
        )
        return vf


if __name__ == '__main__':
    pass


