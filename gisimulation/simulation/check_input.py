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
import simulation.utilities as utilities
import logging
logger = logging.getLogger(__name__)

# %% Classes


class InputError(Exception):
    """
    InputError, parent 'Exception'
    """
    pass

# %% Public checking functions


def check_parser(parameters):
    """
    checking all input (parser)

    Parameters
    ##########

    parameters [dict]

    Returns
    #######

    parameters [dict]:

    """
    logger.info("Checking general input...")
    # % Minimal required input for all scenarios
    parameters = general_input(parameters)
    logger.info("... done.")

    # % Scenario specific requirements
    # General and connected parameters (calculated geom., Metrices, ct, ...)

    return parameters


def general_input(parameters):
    """
    checking general input (everything to calculate the geometries)

    Parameters
    ##########

    parameters [dict]

    Notes
    #####

    If an parser argument is required, it can be None from the GUI. Thus,
    check it the first time it is called.
    """
    try:
        # % Minimal required input for 'free', 'parallel', no gatings

        # General and GI Design
        if not parameters['sampling_rate']:
            logger.debug("Sampling rate is not specified, "
                         "set to pixel size * 1e-3.")
            # Default to pixel_size *1e-3
            parameters['sampling_rate'] = parameters['pixel_size'] * 1e-3
            logger.debug("Sampling rate is {0} um, with pixel size {1} "
                         "um..".format(parameters['sampling_rate'],
                                       parameters['pixel_size']))
        # Source:
        if parameters['beam_geometry'] == 'cone':
            if not parameters['focal_spot_size']:
                error_message = "Input argument missing: 'focal_spot_size' " \
                                "('-fs')."
                logger.error(error_message)
                raise InputError(error_message)

        # Get spectrum
        [parameters['spectrum'], min_energy, max_energy] = \
            _get_spectrum(parameters['spectrum_file'],
                          parameters['spectrum_range'],
                          parameters['spectrum_step'],
                          parameters['design_energy'])
        # material filter
        if parameters['thickness_filter'] and \
                not parameters['material_filter']:
            error_message = "Filter material must be specified."
            logger.error(error_message)
            raise InputError(error_message)
        if parameters['material_filter'] and \
                not parameters['thickness_filter']:
            error_message = "Filter thickness must be specified."
            logger.error(error_message)
            raise InputError(error_message)

        # Detector:
        # PSF right size?
        if parameters['detector_type'] == 'conv':
            if not parameters['point_spread_function']:
                error_message = "Input argument missing: " \
                                "'point_spread_function' ('-psf')."
                logger.error(error_message)
                raise InputError(error_message)
            if parameters['point_spread_function'] <= \
                    parameters['pixel_size']:
                # PSF too small, but be larger
                error_message = "PSF must be at larger than the  pixel "
                "size."
                logger.error(error_message)
                raise InputError(error_message)

        # Threshold (error if > max energy and warninglog if < min)
        if parameters['detector_threshold'] > max_energy:
            error_message = "Detector threshold must be <= the maximal energy."
            logger.error(error_message)
            raise InputError(error_message)
        elif parameters['detector_threshold'] < min_energy:
            logger.warning("Detector threshold is smaller than the minimal "
                           "energy.")

        # material thickness
        if parameters['thickness_detector'] and \
                not parameters['material_detector']:
            error_message = "Detector material must be specified."
            logger.error(error_message)
            raise InputError(error_message)
        if parameters['material_detector'] and \
                not parameters['thickness_detector']:
            error_message = "Detector thickness must be specified."
            logger.error(error_message)
            raise InputError(error_message)

        # Special scenarios
        parameters['component_list'] = ['Source', 'Detector']
        # Add sample to component list
        if parameters['sample_position']:
            parameters['component_list'].append('Sample')

        if parameters['beam_geometry'] == 'parallel':
            # Parallel beam
            # Common checks for both 'free' and 'conv' geometry
            # Warn, that G0 will be ignored if it is defined
            if parameters['type_g0']:
                logger.warning("G0 is defined, but will be ignored.")

            # Individual checks
            if parameters['geometry'] == 'conv':
                # =============================================================
                # Conventional and parallel beam
                #
                # Conditions:
                #     no G0
                #     sample before or after G1 (bg1 or ag1)
                # Requirements:
                #     G1 and G2, one of them fixed
                # =============================================================
                # Sample position (if defined)
                if parameters['sample_position']:
                    if parameters['sample_position'] not in ['bg1', 'ag1']:
                        error_message = "Sample must be before or after G1."
                        logger.error(error_message)
                        raise InputError(error_message)
                # Fixed grating
                if parameters['fixed_grating'] == 'G0':
                    error_message = "The fixed grating must be either G1 or "
                    "G2."
                    logger.error(error_message)
                    raise InputError(error_message)
                # Add G1 and G2
                parameters['component_list'].append('G1')
                parameters['component_list'].append('G2')
            else:
                # =============================================================
                # Free and parallel beam
                #
                # Conditions:
                #     no G0
                # Requirements:
                #     all distances between components must be given
                # =============================================================
                # Add all other components
                if parameters['type_g1']:
                    parameters['component_list'].append('G1')
                if parameters['type_g2']:
                    parameters['component_list'].append('G2')
        else:
            # Cone beam
            if parameters['geometry'] != 'free':
                # Common checks for not 'free' geometry
                # Add G1 and G2
                parameters['component_list'].append('G1')
                parameters['component_list'].append('G2')
                # Fixed grating if G0 is not defined
                if not parameters['g0_type']:
                    # No G0
                    if parameters['fixed_grating'] == 'G0':
                        error_message = "G0 is not defined, choose G1 or G2 "
                        "as fixed grating."
                        logger.error(error_message)
                        raise InputError(error_message)
                    # Fixed distance
                    if not parameters['distance_Source_G1'] and \
                            not parameters['distance_Source_G2']:
                        error_message = ("Either distance from Source to G1 "
                                         "OR Source to G2 must be defined.")
                        logger.error(error_message)
                        raise InputError(error_message)
                    elif parameters['distance_Source_G1'] and \
                            parameters['distance_Source_G2']:
                        logger.warning("Both distance from Source to G1 AND "
                                       "Source to G2 are defined, choosing "
                                       "distance from Source to G2 (total GI "
                                       "length).")
                        parameters['distance_Source_G1'] = None
                        fixed_distance = 'distance_Source_G2'
                    elif parameters['distance_Source_G1']:
                        fixed_distance = 'distance_Source_G1'
                    elif parameters['distance_Source_G2']:
                        fixed_distance = 'distance_Source_G2'
                else:
                    # With G0
                    # Fixed distance
                    if not parameters['distance_G0_G1'] and \
                            not parameters['distance_G0_G2']:
                        error_message = ("Either distance from G0 to G1 OR G0 "
                                         "to G2 must be defined.")
                        logger.error(error_message)
                        raise InputError(error_message)
                    elif parameters['distance_G0_G1'] and \
                            parameters['distance_G0_G2']:
                        logger.warning("Both distance from G0 to G1 AND G0 "
                                       "to G2 are defined, choosing distance "
                                       "from G0 to G2 (total GI length).")
                        parameters['distance_G0_G1'] = None
                        fixed_distance = 'distance_G0_G2'
                    elif parameters['distance_G0_G1']:
                        fixed_distance = 'distance_G0_G1'
                    elif parameters['distance_G0_G2']:
                        fixed_distance = 'distance_G0_G2'

                # Individaul checks
                if parameters['geometry'] == 'conv':
                    # =========================================================
                    # Conventional and cone beam
                    #
                    # Conditions:
                    #     G0 optional
                    #     sample before G1 (bg1)
                    #     distance G2 to detector optional
                    #     distance from source (or G0) to G1
                    #       OR
                    #     distance from source (or G0) to G1
                    # Requirements:
                    #     G1 and G2
                    #     1 fixed grating
                    #
                    # =========================================================
                    if parameters['sample_position']:
                        if parameters['sample_position'] != 'bg1':
                            error_message = "Sample must be before G1."
                            logger.error(error_message)
                            raise InputError(error_message)
                elif parameters['geometry'] == 'sym':
                    # =========================================================
                    # Symmetrical and cone beam
                    #
                    # Conditions:
                    #     G0 optional
                    #     sample before or after G1 (bg1 or ag1)
                    #     distance G2 to detector optional
                    #     distance from source (or G0) to G1
                    #       OR
                    #     distance from source (or G0) to G1
                    # Requirements:
                    #     G1 and G2
                    #     1 fixed grating
                    #
                    # =========================================================
                    if parameters['sample_position']:
                        if parameters['sample_position'] not in ['bg1', 'ag1']:
                            error_message = ("Sample must be before or after "
                                             "G1.")
                            logger.error(error_message)
                            raise InputError(error_message)
                elif parameters['geometry'] == 'inv':
                    # =========================================================
                    # Inverse and cone beam
                    #
                    # Conditions:
                    #     G0 optional
                    #     sample after G1 (ag1)
                    #     distance G2 to detector optional
                    #     distance from source (or G0) to G1
                    #       OR
                    #     distance from source (or G0) to G1
                    # Requirements:
                    #     G1 and G2
                    #     1 fixed grating
                    #
                    # =========================================================
                    if parameters['sample_position']:
                        if parameters['sample_position'] != 'ag1':
                            error_message = ("Sample must be after G1.")
                            logger.error(error_message)
                            raise InputError(error_message)
            else:
                # =============================================================
                # Free and cone beam
                #
                # Conditions:
                #
                # Requirements:
                #     all distances between components must be given
                # =============================================================
                # Add all other components
                if parameters['type_g0']:
                    parameters['component_list'].append('G0')
                if parameters['type_g1']:
                    parameters['component_list'].append('G1')
                if parameters['type_g2']:
                    parameters['component_list'].append('G2')

        # Sort updated component list
        parameters['component_list'].sort()
        # After sort, switch Source and Detector
        parameters['component_list'][0],  parameters['component_list'][-1] = \
            parameters['component_list'][-1], parameters['component_list'][0]

        # Check remaining components (source and detector already done)
        # sample distance, shape, amterial etc.
        # Gratings...

        # if 'free', check distances are all tehre

        # Info
        logger.info("Beam geometry is '{0}' and setup geometry is '{1}'."
                    .format(parameters['beam_geometry'],
                            parameters['geometry']))
        logger.info("Setup consists of: {0}."
                    .format(parameters['component_list']))
        if parameters['geometry'] != 'free':
            logger.info("Fixed grating is: '{0}'."
                        .format(parameters['fixed_grating']))
            if parameters['beam_geometry'] == 'cone':
                logger.info("Fixed distance is: {0}."
                            .format(fixed_distance))

        return parameters

    except AttributeError as e:
        error_message = "Input arguments missing: {}." \
                        .format(str(e).split()[-1])
        logger.error(error_message)
        raise InputError(error_message)

# %% Public utility functions


# %% Private checking functions


# %% Private utility functions

def _get_spectrum(spectrum_file, range_, spectrum_step, design_energy):
    """
    Load spectrum from file or define based on range (min, max). Returns
    energies and relative photons (normalized to 1 in total).

    Parameters
    ##########

    spectrum_file:              path to spectrum file
    range_ [keV, keV]:          [min, max]
    spectrum_step [keV]
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
        spectrum = _read_spectrum(spectrum_file)
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
        if range_[1] <= range_[0]+spectrum_step:
            error_message = ("Energy range maximum value ({0} keV) must be "
                             "at least {1} keV larger than minimum value "
                             "({2} keV)."
                             .format(range_[0], spectrum_step, range_[1]))
            logger.error(error_message)
            raise InputError(error_message)
        # Calc spectrum
        spectrum_dict = dict()
        # Calc from range
        logger.info("Setting spectrum based on input range...")
        spectrum_dict['energies'] = np.arange(range_[0],
                                              range_[1]+spectrum_step,
                                              spectrum_step,
                                              dtype=np.float)
        spectrum_dict['photons'] = (np.ones(len(spectrum_dict['energies']),
                                            dtype=np.float) /
                                    len(spectrum_dict['energies']))
        logger.debug("\tSet all photons to {}."
                     .format(spectrum_dict['photons'][0]))
        # Convert to struct
        spectrum = utilities.Struct(**spectrum_dict)
        logger.info("... done.")
    # Both spectrum_file and _range are None, use design energy as spectrum
    else:
        logger.info("Only design energy specified, calculating only for {} "
                    "keV...".format(design_energy))
        spectrum_dict = dict()
        spectrum_dict['energies'] = np.array(design_energy, dtype=np.float)
        spectrum_dict['photons'] = np.array(1, dtype=np.float)
        spectrum = utilities.Struct(**spectrum_dict)
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


def _read_spectrum(spectrum_file_path):
    """
    Read from spectrum file.

    Parameters
    ##########

    spectrum_file_path [str]:       to .csv or .txt file.
                                    Delimiter is ',', see Format

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
    logger.debug("Reading from file {}...".format(spectrum_file_path))
    spectrum_struct_array = np.genfromtxt(spectrum_file_path, delimiter=',',
                                          names=True)  # np ndarray
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
                        .format(spectrum_file_path, str(e).split()[-1])
        logger.error()
        raise InputError
    # Convert to struct
    spectrum = utilities.Struct(**spectrum_dict)

    # Check if more than 2 energies in spectrum
    if len(spectrum.energies) <= 1:
                error_message = ("Spectrum file only contains 1 energy."
                                 "Minimum is 2.")
                logger.error(error_message)
                raise InputError(error_message)
    logger.debug("... done.")
    return spectrum


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
