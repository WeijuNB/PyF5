#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
import errno
import os
import time


@contextlib.contextmanager
def flock(path, wait_delay=.1):
  """
  Lock file used to prevent multiple instances of commands from running.

  :see: http://code.activestate.com/recipes/576572/
  :param path:
      The path to the lock file.
  :param wait_delay:
      Wait delay time (float).
  Usage::

      with flock('.lockfile') as fd:
          lockfile = os.fdopen(fd, 'r+')
  """
  while True:
    try:
      fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except OSError, e:
      if e.errno != errno.EEXIST:
        raise
      time.sleep(wait_delay)
      continue
    else:
      break
  try:
    yield fd
  finally:
    os.close(fd)
    os.unlink(path)
