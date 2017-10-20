# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 17:41:28 2017

@author: mbuec
"""
import logging
logger = logging.getLogger(__name__)

# %% TEST


class InputError(Exception):
    def __init__(self):
        """
        If logging logger is used, show no (empty) message.
        """
        if type(logger.root) is logging.RootLogger:
            self.message = ''


def check_input():
    """
    """
    try:
        logger.info("calling 'a'.")
        raise AttributeError("'Class' object has no attribute 'a'")
    except AttributeError as e:
        logger.info("Caught an exception in kivy_test.")
        error_message = "Input arguments missing: {}".format(
                         str(e).split()[-1])
        logger.error(error_message)
        logger.info("Raising InputError.")
        raise InputError(error_message)
