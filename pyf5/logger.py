import logging

logger = logging.getLogger('pyf5')
logger.setLevel(logging.DEBUG)
FORMAT = '%(asctime)-15s %(levelname)-5s: %(message)s'
logging.basicConfig(format=FORMAT)


def safe_string(item):
    try:
        if type(item) == unicode:
            return item.encode('utf-8')
        elif type(item) == str:
            return item
        else:
            return str(item)
    except Exception as e:
        print item


def debug(*args):
    msg = ' '.join([safe_string(arg) for arg in args])
    logger.debug(msg)


def info(*args):
    msg = ' '.join([safe_string(arg) for arg in args])
    logger.info(msg)


def warn(*args):
    msg = ' '.join([safe_string(arg) for arg in args])
    logger.warn(msg)


def error(*args):
    msg = ' '.join([safe_string(arg) for arg in args])
    logger.error(msg)


def critical(*args):
    msg = ' '.join([safe_string(arg) for arg in args])
    logger.critical(msg)