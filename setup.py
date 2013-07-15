#coding:utf-8
import sys
from setuptools import setup, find_packages

try:
    import py2exe
except ImportError:
    pass

kwargs_py2exe = dict(
    console=['pyf5/f5.py'],
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

kwargs_egg = dict(
    name='pyf5',
    packages=find_packages(),
    package_data={
        'pyf5': ['_/*.*'],
    },
    include_package_data=True,
    version='0.9.1.1',
    author="luwenjin",
    author_email="luwenjin@gmail.com",
    url="http://getf5.com",
    description="Web page auto reloader for web developers.",
    # download_url="https://github.com/WeijuNB/PyF5",

    install_requires={
        "tornado": ['tornado>=3.1'],
        'watchdog': ['watchdog>=0.6'],
        },
    scripts=['f5.py']
)

if sys.argv[1] and sys.argv[1].lower() == 'py2exe':
    setup(**kwargs_py2exe)
else:
    setup(**kwargs_egg)