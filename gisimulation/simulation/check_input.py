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
import numpy as np
import simulation.utility  # if only Struct and only used here, include here!
import logging
logger = logging.getLogger(__name__)

# %% Classes


class InputError(Exception):
    """
    InputError, parent 'Exception'
    """
    pass

# %% Public checking functions


def check_input(parameters):
    """
    ToDo: spit sectional checking into sub-functions (!?)

    Parameters:
    """
    try:
        # % Minimal required inpuf for all scenarios

        # Source:


        # Detector:
        # if not rnge, set range min with threshold. else: check if they match


        # Spectrum:
        # Get spectrum
        [parameters.spectrum, min_energy, max_energy] = \
            get_spectrum(parameters.spectrum_file, parameters.spectrum_range,
                         parameters.range_step, parameters.design_energy)

        # Calculations:
        if parameters.sampling_rate == 0:
            try:
                logger.debug("Sampling rate is 0, set to pixel size * 1e-3.")
                # Default to pixel_size *1e-3
                parameters.sampling_rate = parameters.pixel_size * 1e-3
                logger.debug("Sampling rate is {0} um, with pixel size {1} "
                             "um..".format(parameters.sampling_rate,
                                           parameters.pixel_size))
            except TypeError:
                error_message = "Input arguments missing: 'pixel_size' " \
                                "('-pxs')."
                logger.error(error_message)
                raise InputError(error_message)

#        # General input
#        if parameters.geometry == 'free':
#            # =================================================================
#            # Requirements:
#            #     at least 1 grating
#            # =================================================================
#            pass

        # % Scenario specific requirements
        # General and connected parameters

    except AttributeError as e:  # For paramters.value and value not existing
                                 # NECESSARY??? (in the end?)
        error_message = "Input arguments missing: {}." \
                        .format(str(e).split()[-1])
        logger.error(error_message)
        raise InputError(error_message)

# %% Public utility functions


def get_spectrum(spectrum_file, range_, range_step, design_energy):
    """
    Load spectrum from file or define based on range (min, max). Returns
    energies and relative photons (normalized to 1 in total).

    Parameters
    ##########

    spectrum_file:              path to spectrum file
    range_ [keV, keV]:          [min, max]
    range_step [keV]
    design_energy [keV]

    Returns
    #######

    [spectrum, min, max]        spectrum: [energies, photons] [keV, relative]
                                min: minimal energy [keV]
                                max: maximal energy [keV]

    Notes
    #####

    if from file and range:
        range is set within loaded spectrum. Photons not rescaled.
    if range:
        range from min to max, step 1 keV. Homogenuous photons distribution.

    """
    # Read from file
    if spectrum_file is not None:
        logger.info("Reading spectrum from file at:\n{}..."
                    .format(spectrum_file))
        spectrum = read_spectrum(spectrum_file)
        # Set range
        if range_ is not None:
            # Min and max in right order?
            if range_[1] <= range_[0]:
                error_message = ("Energy range maximum value ({0} keV) must "
                                 "be larger than minimum value ({1} keV)."
                                 .format(range_[0], range_[1]))
                logger.error(error_message)
                raise InputError(error_message)
            # Check if within bounds of spectrum
            if range_[0] >= max(spectrum.energies):
                error_message = ("Energy range minimum value must be smaller "
                                 "than spectrum maximum ({0} keV)."
                                 .format(max(spectrum.energies)))
                logger.error(error_message)
                raise InputError(error_message)
            if range_[1] <= min(spectrum.energies):
                error_message = ("Energy range maximum value must be larger "
                                 "than spectrum minimum ({0} keV)."
                                 .format(min(spectrum.energies)))
                logger.error(error_message)
                raise InputError(error_message)

            # Find min and max closes to range min and max
            [min_energy, min_index] = _nearest_value(spectrum.energies,
                                                     range_[0])
            [max_energy, max_index] = _nearest_value(spectrum.energies,
                                                     range_[1])
            # More than 1 energy in spectrum?
            if min_energy == max_energy:
                error_message = ("Energy minimum value same as maximum. Range"
                                 "minimum {0} and maximum {1} too close "
                                 "together.".format(range_[0], range_[1]))
                logger.error(error_message)
                raise InputError(error_message)
            spectrum.energies = spectrum.energies[min_index:max_index+1]
            spectrum.photons = spectrum.photons[min_index:max_index+1]
            logger.debug("\tSet energy range from {0} to {1} keV."
                         .format(min_energy, max_energy))
        logger.info("... done.")
    # Check range input
    elif range_ is not None:
        # Min and max in right order?
        if range_[1] <= range_[0]+range_step:
            error_message = ("Energy range maximum value ({0} keV) must be "
                             "at least {1} keV larger than minimum value "
                             "({2} keV)."
                             .format(range_[0], range_step, range_[1]))
            logger.error(error_message)
            raise InputError(error_message)
        # Calc spectrum
        spectrum_dict = dict()
        # Calc from range
        logger.info("Setting spectrum based on input range...")
        spectrum_dict['energies'] = np.arange(range_[0],
                                              range_[1]+range_step,
                                              range_step,
                                              dtype=np.float)
        spectrum_dict['photons'] = (np.ones(len(spectrum_dict['energies']),
                                            dtype=np.float) /
                                    len(spectrum_dict['energies']))
        logger.debug("\tSet all photons to {}."
                     .format(spectrum_dict['photons'][0]))
        # Convert to struct
        spectrum = simulation.utility.Struct(**spectrum_dict)
        logger.info("... done.")
    # Both spectrum_file and _range are None, use design energy as spectrum
    else:
        logger.info("Only design energy specified, calculating only for {} "
                    "keV...".format(design_energy))
        spectrum_dict = dict()
        spectrum_dict['energies'] = np.array(design_energy, dtype=np.float)
        spectrum_dict['photons'] = np.array(1, dtype=np.float)
        spectrum = simulation.utility.Struct(**spectrum_dict)
        logger.debug("\tSet photons to 1.")
        logger.info("... done.")
        logger.info("Spectrum is design energy {} keV."
                    .format(spectrum.energies))
        return spectrum, spectrum.energies, spectrum.energies

    # Check and show spectrum results
    min_energy = min(spectrum.energies)
    max_energy = max(spectrum.energies)
    # Design energy in spectrum?
    if design_energy < min_energy or \
       design_energy > max_energy:
        error_message = ("Design energy ({0} keV) must be within "
                         "spectrum range (min: {1} kev, max: {2} keV).") \
                         .format(design_energy, min_energy,
                                 max_energy)
        logger.error(error_message)
        raise InputError(error_message)
    logger.debug("Design energy within spectrum.")
    logger.info("Spectrum from {0} keV to {1} keV in {2} keV steps."
                .format(min_energy, max_energy,
                        spectrum.energies[1]-spectrum.energies[0]))
    return spectrum, min_energy, max_energy


def read_spectrum(spectrum_file):
    """
    Read from spectrum file.

    Parameters
    ##########

    spectrum_file [str] or [argparse.FileType('r')]     to .csv or .txt file.
                                                        Delimiter is ',', see
                                                        Format

    Returns
    #######

    spectrum [struct] [keV]:                            spectrum.energies
                                                        spectrum.photons

    Format
    ######

    energy, photons
    1, 10e3
    2, 23e4
    .,.
    .,.
    .,.

    """
    # Read dict from file
    logger.debug("Reading from file {}...".format(spectrum_file))
    spectrum_struct_array = np.genfromtxt(spectrum_file, delimiter=',',
                                          names=True)
    if 'energy' in spectrum_struct_array.dtype.names:
        # Rename 'energy' to 'energies'
        spectrum_struct_array.dtype.names = ('energies', 'photons')
    # Convert to dict
    spectrum_dict = dict()
    try:
        spectrum_dict['energies'] = spectrum_struct_array['energies']
        spectrum_dict['photons'] = spectrum_struct_array['photons']
    except AttributeError as e:
        error_message = "Spectrum file at {0} is missing '{1}'-column." \
                        .format(spectrum_file, str(e).split()[-1])
        logger.error()
        raise InputError
    # Convert to struct
    spectrum = simulation.utility.Struct(**spectrum_dict)

    # Check if more than 2 energies in spectrum
    if len(spectrum.energies) <= 1:
                error_message = ("Spectrum file only contains 1 energy."
                                 "Minimum is 2.")
                logger.error(error_message)
                raise InputError(error_message)
    logger.debug("... done.")
    return spectrum

# %% Private checking functions


# %% Private utility functions


def _nearest_value(array, value):
    """
    Funtion to find the nearest value of a number within a numpy array.

    Parameters
    ##########
    array [numpy array]     array to be searched
    value                   target number

    Returns
    #######

    [nearest_value, index]

    """
    nearest_index = (np.abs(array-value)).argmin()
    return array[nearest_index], nearest_index
