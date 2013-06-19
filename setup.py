#coding:utf-8
from distutils.core import setup
import py2exe

setup(
    console=['f5.py'],
    options={
        'py2exe': {
            'bundle_files': 1,
            'excludes': [
                'pyreadline', 'difflib', 'doctest', 'optparse',
                'pickle', 'pdb', 'unittest',
            ],
            'compressed': True,
            'dll_excludes': ['msvcr71.dll'],
        }
    },
    zipfile=None
)