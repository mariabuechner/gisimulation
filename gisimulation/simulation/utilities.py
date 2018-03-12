"""
Module with all helper classes and functions.

Classes
=======

    Struct:         Transform dictionaries into structs.
                    Parameters:
                        [**kwargs] (keyword arguments, dictionary)
                    Returns:
                        struct

Functions
=========

set_logger_level:   set level of logger.
                    Parameters:
                        logger
                        verbose [int]
                        default_level (logging.INFO)

@author: buechner_m <maria.buechner@gmail.com>
"""
import logging


# %% Functions


def get_logger_level(verbose, default_level=logging.INFO):
    """
    Gets the logging level dependent on verbosity.

    Parameters
    ==========

    verbose [int]:  1, 2, 3, 4
    default_level:  if verbose=None, set to default (logging.INFO)

    Notes
    =====

    1:  logging.ERROR
    2:  logging.WARNING
    3:  logging.INFO
    4:  logging.DEBUG


    """
    if verbose > 4:  # if more v's counted, do not default, but set to highest
        verbose = 4
    logging_level = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }.get(verbose, default_level)  # Default: logging.INFO
    return logging_level
