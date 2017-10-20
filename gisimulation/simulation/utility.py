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

# %% Classes


class Struct:
    """
    Custom struct class to transform dictionaries into structs.

    Parameters
    ==========

    **entries [**kwargs]:   dictionary
    Notes
    =====

    dictionary:         dict['key']
                        >>> value
    struct:             struct = Struct(**dict)
                        struct.key
                        >>> value

    """
    def __init__(self, **entries):
        self.__dict__.update(entries)

# %% Functions
