#coding:utf-8
import sys
from setuptools import setup

import py2exe

kwargs_py2exe = dict(
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
    zipfile=None,
)

if sys.argv[1] and sys.argv[1].lower() == 'py2exe':
    setup(**kwargs_py2exe)