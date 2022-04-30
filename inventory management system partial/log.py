import logging


def get_logger(log_name, log_level='DEBUG', add_stream_handler=True, log_file=None):
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = LOG_LEVELS[log_level]

    # Create a custom logger
    logger = logging.getLogger(log_name)

    # Reset all existing handlers
    logger.handlers = []

    logger.setLevel(log_level)

    # Create stream handler
    if add_stream_handler:
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(asctime)s %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

    # Create file handler
    if log_file is not None:
        f_handler = logging.FileHandler(log_file)
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)

    return logger


def test_get_logger():
    logger = get_logger('Test', 'INFO')

    logger.debug('This is a debug')
    logger.warning('This is a warning')
    logger.error('This is an error')


if __name__ == '__main__':
    test_get_logger()
    