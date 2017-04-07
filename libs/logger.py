#!/usr/bin/env python
# coding=utf-8

import logging

def init_log(log_file):
    '''Initialize logging module.
    '''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    #formatter = logging.Formatter('%(asctime)-15s - [%(levelname)s] [%(module)s: %(funcName)s] %(message)s')
    formatter = logging.Formatter('%(asctime)-15s - [%(levelname)s] [%(module)s] %(message)s')

    # Create a file handler to store error messages
    fhdr = logging.FileHandler(log_file, mode = 'w')
    fhdr.setLevel(logging.DEBUG)
    fhdr.setFormatter(formatter)

    # Create a stream handler to print all messages to console
    chdr = logging.StreamHandler()
    chdr.setFormatter(formatter)
    chdr.setLevel(logging.WARNING)

    logger.addHandler(fhdr)
    logger.addHandler(chdr)

    return logger

def close_log(logger):
    handlers = list(logger.handlers)
    for h in handlers:
        logger.removeHandler(h)
        h.flush()
        h.close()

if __name__ == '__main__':
    logger = init_log("test.log")
    logger.info("info message")
    logger.error("error message")
