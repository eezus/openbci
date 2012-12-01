#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:
#     Mateusz Kruszyński <mateusz.kruszynski@gmail.com>
#     Joanna Tustanowska <joanna.tustanowska@titanis.pl>

"""Module defines a single method get_logger that returns logger with
set logging level. Change logging.INFO lines to change logging level."""
import os
import logging
import logging.handlers
import log_mx_handler

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


MAX_FILE_SIZE_B = 1000000
LOG_BUFFER_SIZE_B = 5000
BACKUP_COUNT = 2

def console_formatter():
    return logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def file_formatter():
    return logging.Formatter(
                    "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")

def mx_formatter():
    return logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")



def get_dummy_logger(p_name, p_level='info'):
    """Return logger with p_name as name. And logging level p_level.
    p_level should be in (starting with the most talkactive):
    'debug', 'info', 'warning', 'error', 'critical'."""
    logger = logging.getLogger(p_name)
    if len(logger.handlers) == 0:
        # Some module migh be imported few times. In every get_logger call 
        # with p_name = "X" we return the same instance of logger, bu we must
        # ensure, that the logger has no more than one handler.
        handler = logging.StreamHandler()
        
        level = LEVELS[p_level]
        logger.setLevel(level)
        handler.setLevel(level)
        
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def get_logger(name, file_level='debug', stream_level='warning', 
                            mx_level='warning', conn=None, log_dir=None):
    """Return logger with name as name. And logging level p_level.
    p_level should be in (starting with the most talkactive):
    'debug', 'info', 'warning', 'error', 'critical'."""
    logger = logging.getLogger(name)
    if len(logger.handlers) == 0:
        # Some module migh be imported few times. In every get_logger call 
        # with name = "X" we return the same instance of logger, bu we must
        # ensure, that the logger has no more than one handler.
        
        level = LEVELS['debug']
        logger.setLevel(level)
        formatter = console_formatter()

        shandler = logging.StreamHandler()
        shandler.setFormatter(formatter)
        stream_level = stream_level or 'warning'
        file_level = file_level or 'debug'
        mx_level = mx_level or 'warning'
        shandler.setLevel(LEVELS[stream_level])
        logger.addHandler(shandler)
        
        if conn is not None:
            mxhandler = log_mx_handler.LogMXHandler(conn)
            mxhandler.setLevel(LEVELS[mx_level])
            mxhandler.setFormatter(mx_formatter())
            logger.addHandler(mxhandler)


        if log_dir is not None:
            log_dir = os.path.expanduser(log_dir)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            fhandler = logging.handlers.RotatingFileHandler(
                                    os.path.join(log_dir, name + ".log"), 
                                    maxBytes=MAX_FILE_SIZE_B,
                                    backupCount=BACKUP_COUNT)
            fhandler.setFormatter(formatter)
            fhandler.setLevel(LEVELS[file_level])
            fhandler.setFormatter(file_formatter())
            # memhandler = logging.handlers.MemoryHandler(LOG_BUFFER_SIZE_B, 
            #                                     flushLevel=LEVELS['warning'],
            #                                            target=fhandler)
            # memhandler.setLevel(LEVELS file_level])
            logger.addHandler(fhandler)

    return logger
