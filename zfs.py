#coding:utf-8
from datetime import datetime
import os
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

from utils import get_rel_path

class ZipFileSystem(object):
    def __init__(self, zip_file):
        self.zip = ZipFile(zip_file, 'r')

    def read(self, rel_path):
        try:
            return self.zip.read(rel_path)
        except KeyError:
            return None

    def modified_at(self, rel_path):
        try:
            zip_info = self.zip.getinfo(rel_path)
            date_time = datetime(*zip_info.date_time)
            return time.mktime(date_time.timetuple())
        except KeyError:
            return None

    def file_size(self, rel_path):
        try:
            zip_info = self.zip.getinfo(rel_path)
            return zip_info.file_size
        except KeyError:
            return None

    @classmethod
    def make_zip_file_with_folder(cls, folder_path, zip_file_path):
        zip_file = ZipFile(zip_file_path, 'w', ZIP_DEFLATED)

        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                abs_path = os.path.join(root, file_name)
                rel_path = unicode(get_rel_path(abs_path, folder_path), sys.getfilesystemencoding())
                zip_file.write(abs_path, rel_path)
                print 'add...', rel_path
        zip_file.close()
        print 'done!'



if __name__ == '__main__':
    import base64
    zip_file_name = 'assets.zip'
    ZipFileSystem.make_zip_file_with_folder('assets', zip_file_name)

    assets_zip64 = base64.encodestring(open(zip_file_name, 'rb').read())
    wf = open('assets.py', 'w+')
    wf.write('assets_zip64 = """%s"""' % assets_zip64)
    wf.close()
    os.remove(zip_file_name)

    import StringIO
    assets_file = StringIO.StringIO(base64.decodestring(assets_zip64))

    zfs = ZipFileSystem(assets_file)
    rel_path = 'js/reloader.js'
    print zfs.read(rel_path)
    print zfs.modified_at(rel_path)




