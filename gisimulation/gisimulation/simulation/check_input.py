"""
Module to check the parsed input before starting the simulation.

Classes
=======

InputError:    does nothingm, parent: Exception

Functions
=========

check_input:    Checks the input parameters, logs errors and raises an
                InportError.
                Parameters:
                    parameters [struct]

@author: buechner_m <maria.buechner@gmail.com>
"""
import logging
logger = logging.getLogger(__name__)

# %% Classes


class InputError(Exception):
    """
    InputError, parent 'Exception'

    Notes
    =====

    Does nothing (pass)

    """
    pass

# %% Functions


def check_input(parameters):
    """
    """
    try:
        # General and connected parameters
        if parameters.sampling_rate == 0:
            logger.debug("Sampling rate is 0, set to pixel size * 1e-3")
            # Default to pixel_size *1e-3
            parameters.sampling_rate = parameters.pixel_size * 1e-4
        # GI parameters
#        if parameters.geometry == 'free':
#            test = parameters.fill_material_g1
    except AttributeError as e:
        logger.exception("Input arguments missing: {}".format(
                     str(e).split()[-1]), exc_info=True)
        raise InputError
