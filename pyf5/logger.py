import logging

logger = logging.getLogger('pyf5')
logger.setLevel(logging.DEBUG)
FORMAT = '%(asctime)-15s %(levelname)-5s: %(message)s'
logging.basicConfig(format=FORMAT)


def debug(*args):
    msg = ' '.join([str(arg) for arg in args])
    logger.debug(msg)


def info(*args):
    msg = ' '.join([str(arg) for arg in args])
    logger.info(msg)


def warn(*args):
    msg = ' '.join([str(arg) for arg in args])
    logger.warn(msg)


def error(*args):
    msg = ' '.join([str(arg) for arg in args])
    logger.error(msg)


def critical(*args):
    msg = ' '.join([str(arg) for arg in args])
    logger.critical(msg)