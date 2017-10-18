# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 17:41:28 2017

@author: mbuec
"""
import logging
logger = logging.getLogger(__name__)

# %% TEST


class InputError(Exception):
    pass


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
        logger.exception(error_message)
        logger.info("Raising InputError.")
        raise InputError(error_message)
