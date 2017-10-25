"""
Module to run grating interferometer simulation and metrics calculation

    System geometry
    ==========

    (0, 0, 0) point at source, detector center in (0, 0, z_d) ...

    Parameters
    ==========

    General:
        '--verbose', '-v':              flag for verbosity level of logger
        beam_geometry [string]:         'cone' (default), 'parallel'
        geometry [string]:              'sym' (default), 'conv', 'inv', 'free'
        @file.txt                       parse from txt file.
                                        Can use multiple files, in case of
                                        double entries, the last file
                                        overwrites the previous one(s).
                                        be overwritten afterwards in command
                                        line.
                                        File layout:
                                        ArgName1
                                        ArgValue1
                                        ArgName2
                                        ArgValue2
                                            .
                                            .
                                            .
                                        Example:
                                        -sr
                                        100
                                        -p0
                                        2.4
                                         .
                                         .
                                         .

    Grating interferometer:
        G0:
            type_g0 [string]
            pitch_g0 [um]
            material_g0 [string]
            thickness_g0 [um]
            phase_shift_g0 [rad]
            wafer_material_g0 [string]
            wafer_thickness_g0 [um]
            fill_material_g0 [string]
            fill_thickness_g0 [um]
        G1:
            type_g1 [string]:           'mix' (default), 'phase', 'abs'
            pitch_g1 [um]
            material_g1 [string]
            thickness_g1 [um]
            phase_shift_g1 [rad]        PI (default)
            wafer_material_g1 [string]
            wafer_thickness_g1 [um]
            fill_material_g1 [string]
            fill_thickness_g1 [um]
        G2:
            type_g2 [string]:           'mix' (default), 'phase', 'abs'
            pitch_g2 [um]
            material_g2 [string]
            thickness_g2 [um]
            phase_shift_g2 [rad]
            wafer_material_g2 [string]
            wafer_thickness_g2 [um]
            fill_material_g2 [string]
            fill_thickness_g2 [um]
        Talbot order

        distance_source2grating [mm]
            (to G1 or G0, if defined)
        distance_G2_detector [mm]

    Detector:
        pixel_size [um] (square)
        detector_size [#x-pixel, #y-pixel] [int, int]
            (FOV)
        detector_material [string]
            (if not defined, assume 100% efficiency)
        detector_thickness [um]

    Source:
        focal_spot_size [um]:           0 (default)
            (if 0, infinite source size)

    Spectrum:
        design_energy [keV]
        spectrum [string]:              path to file

    Calculations:
        sampling_rate [um]:             0 (default)
            (if 0, pixel_size * 1e1-4)

    Returns
    =======

    Notes
    =====

    0 or '' indicated not-defined or non-existent component

@author: buechner_m <maria.buechner@gmail.com>
"""
import logging
import numpy as np
import sys
# gisimulation modules
import simulation.utilities as utilities
import simulation.parser_def as parser_def
import simulation.check_input as check_input
# import materials
# import geometry
# import gratings
logger = logging.getLogger(__name__)

# %% Constants
NUMERICAL_TYPE = np.float

# %% Main


if __name__ == '__main__':
    # Parse from command line

    parser = parser_def.input_parser(NUMERICAL_TYPE)
    args = parser.parse_args()
    parameters = vars(args)
#    parameters = utilities.Struct(**vars(args))
# =============================================================================
# LEAVE OUT FOR NOW, TRY TO CHECK INPUT WITH NONETYPES
#     args = parser.parse_args()  # returns namespace
#     # Clean parsed arguments
#     all_input_parameters = vars(args)  # namespace to dict
#     # Keep verbosity level and all non-None input parameters
#     input_parameters = dict([key, value] for [key, value] in
#                             all_input_parameters.items()
#                             if value is not None or key == 'verbose')
#    # dict to struct
#    parameters = simulation.utility.Struct(**input_parameters)
# =============================================================================

    # Config logger output

    # Get verbose level of logger
    logger_level = utilities.get_logger_level(parameters['verbose'])
    # Set logger config
    logging.basicConfig(level=logger_level, format='%(asctime)s - %(name)s '
                        '- %(levelname)s - '
                        '%(message)s', disable_existing_loggers=False)

    # Check input
    logger.debug("Checking parsed arguments...")
    try:
        parameters = check_input.check_parser(parameters)
    except check_input.InputError:
        logger.info("Command line error, exiting...")
        sys.exit(2)  # 2: command line syntax errors
#    finally:
#        logger.debug("...done.")
