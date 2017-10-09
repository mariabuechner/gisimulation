"""
Module to run grating interferometer simulation and metrics calculation

    System geometry
    ==========

    (0, 0, 0) point at source, detector center in (0, 0, z_d) ...

    Parameters
    ==========

    General:
        '--verbose', '-v':              flag for verbosity level of logger
        @file.txt                       parse from txt file.
                                        Can use multiple files. Arguments can
                                        be overwritten afterwards in command
                                        line.
                                        File layout:
                                            ArgName ArgValue
                                        Example:
                                            -sr 100
                                            -p0 2.4

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
        design_energy [keV]
        Talbot order
        spectrum [string]:
        geometry [string]:              'sym' (default), 'conv', 'inv'
            (symmentric, conventional, inverse)
        distance_source2grating [mm]
            (to G1 or G0, if defined)
        distance_G2_detector [mm]

    Detector:
        pixel_size [um] (square)
        detector_size [#x-pixel, #y-pixel]
            (FOV)
        detector_material [string]
        detector_thickness [um]

    Source:
        focal_spot_size [um]
        beam_geometry [string]:         'parallel' (default), 'spherical'

    Simulation:
        sampling_rate [um]:             0 (default)
            (if 0, pixel_size * 1e1-3)


    NECESSARY INPUT:
        Gratings:
            material + thickness OR phase_shift
        GI: (parallel and spherical-> difference???)
            1 pitch + 1 distance + talbot_order (???)
            G1 and G2 defined
            if spherical beam: + distance_source2grating + distance_G2_detector
            Symmetrical:
                (p0 or) p1 or p2
            Conventional:
                (p0 or) p1 or p2
            Inverse:
                (p0 or) p1 or p2

        Detector:
            pixel_size + FOV + detector_material + detector_thickness
        Source:
            focal_spot_size

    Returns
    =======

    Notes
    =====

    0 or '' indicated not-defined or non-existent component

@author: buechner_m <maria.buechner@gmail.com>
"""
import argparse
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                    '%(message)s')
import numpy as np
# import materials
# import geometry
# import gratings

# Constants
NUMERICAL_TYPE = np.float


# Parse input arguments
# NOTE: error handling to unpractical with argparse
#       -> make all arguments optional and check manually later!
# Custom formatter class combining all wanted formats
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass
parser = argparse.ArgumentParser(description='Collect GI and simulation '
                                 'parameters.\n'
                                 'Parse from .txt file: '
                                 '@filedir/filename.txt.\n'
                                 'Can use multiple files. Arguments can \n'
                                 'be overwritten afterwards in command line.\n'
                                 'File layout:\n'
                                 '\tArgName ArgValue\n'
                                 'Example:\n'
                                 '\t-sr 100\n'
                                 '\t-p0 2.4\n',
                                 fromfile_prefix_chars='@',
                                 formatter_class=CustomFormatter)
# USE SUBPARSERS FOR SIMULATION/GEOMETRY DEPENDENT ARGUMENTS...

# General input
parser.add_argument('-v', '--verbose', action='count',
                    help='Increase verbosity level. "v": error, "vv": warning,'
                    '"vvv": info (default), "vvvv": debug')
# Grating parameters
# G0
parser.add_argument('-g0', dest='type_g0', default='mix',
                    type=str,
                    choices=['mix', 'phase', 'abs'],
                    help='Choose which interaction will be considered for G0. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('-p0', dest='pitch_g0',
                    help='Pitch of G0 [um].')
parser.add_argument('-m0', dest='material_g0',
                    type=str,
                    help='G0 grating line material.')
parser.add_argument('-d0', dest='thickness_g0',
                    type=NUMERICAL_TYPE,
                    help='Depth of G0 grating lines [um].')
parser.add_argument('-shift0', dest='phase_shift_g0',
                    type=NUMERICAL_TYPE,
                    help='Phase shift of G0 grating lines [rad].')
parser.add_argument('-m0_wafer', dest='wafer_material_g0',
                    type=str,
                    help='G0 wafer material.')
parser.add_argument('-d0_wafer', dest='wafer_thickness_g0',
                    type=NUMERICAL_TYPE,
                    help='Depth of G0 wafer [um].')
parser.add_argument('-m0_fill', dest='fill_material_g0',
                    type=str,
                    help='G0 filling material.')
parser.add_argument('-d0_fill', dest='fill_thickness_g0',
                    type=NUMERICAL_TYPE,
                    help='Depth of G0 filling [um].')
# G1
parser.add_argument('-g1', dest='type_g1', default='mix',
                    type=str,
                    choices=['mix', 'phase', 'abs'],
                    help='Choose which interaction will be considered for G1. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('-p1', dest='pitch_g1',
                    type=NUMERICAL_TYPE,
                    help='Pitch of G1 [um].')
parser.add_argument('-m1', dest='material_g1',
                    type=str,
                    help='G1 grating line material.')
parser.add_argument('-d1', dest='thickness_g1',
                    type=NUMERICAL_TYPE,
                    help='Depth of G1 grating lines [um].')
parser.add_argument('-shift1', dest='phase_shift_g1', default=np.pi,
                    type=NUMERICAL_TYPE,
                    help='Phase shift of G1 grating lines [rad]. '
                    'Default is PI.')
parser.add_argument('-m1_wafer', dest='wafer_material_g1',
                    type=str,
                    help='G1 wafer material.')
parser.add_argument('-d1_wafer', dest='wafer_thickness_g1',
                    type=NUMERICAL_TYPE,
                    help='Depth of G1 wafer [um].')
parser.add_argument('-m1_fill', dest='fill_material_g1',
                    type=str,
                    help='G1 filling material.')
parser.add_argument('-d1_fill', dest='fill_thickness_g1',
                    type=NUMERICAL_TYPE,
                    help='Depth of G1 filling [um].')
# G2
parser.add_argument('-g2', dest='type_g2', default='mix',
                    type=str,
                    choices=['mix', 'phase', 'abs'],
                    help='Choose which interaction will be considered for G2. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('-p2', dest='pitch_g2',
                    type=NUMERICAL_TYPE,
                    help='Pitch of G2 [um].')
parser.add_argument('-m2', dest='material_g2',
                    type=str,
                    help='G2 grating line material.')
parser.add_argument('-d2', dest='thickness_g2',
                    type=NUMERICAL_TYPE,
                    help='Depth of G2 grating lines [um]..')
parser.add_argument('-shift2', dest='phase_shift_g2',
                    type=NUMERICAL_TYPE,
                    help='Phase shift of G2 grating lines [rad].')
parser.add_argument('-m2_wafer', dest='wafer_material_g2',
                    type=str,
                    help='G2 wafer material.')
parser.add_argument('-d2_wafer', dest='wafer_thickness_g2',
                    type=NUMERICAL_TYPE,
                    help='Depth of G2 wafer [um].')
parser.add_argument('-m2_fill', dest='fill_material_g2',
                    type=str,
                    help='G2 filling material.')
parser.add_argument('-d2_fill', dest='fill_thickness_g2',
                    type=NUMERICAL_TYPE,
                    help='Depth of G2 filling [um].')
# Design
parser.add_argument('-e', dest='design_energy',
                    type=NUMERICAL_TYPE,
                    help='Design energy of GI [keV].')
parser.add_argument('-t', dest='talbot_order',
                    type=NUMERICAL_TYPE,
                    help='Talbot order.')
parser.add_argument('-spec', dest='spectrum',  # NEEDTO IMPL CUSTOM FILE INPUT?
                    nargs='?', type=argparse.FileType('r'),
                    help='Location of spectrum file.')
parser.add_argument('-gi', dest='geometry', default='sym',
                    type=str,
                    choices=['sym', 'conv', 'inv'],
                    help='GI geometry. Default is "sym", choices are\n'
                    '"sym": symmetrical, "conv": conventional, '
                    '"inv": inverse.')
parser.add_argument('-s2g', dest='distance_source2grating',
                    type=NUMERICAL_TYPE,
                    help='Distance from source to first grating [mm].')
parser.add_argument('-g2d', dest='distance_G2_detector',
                    type=NUMERICAL_TYPE,
                    help='Distance from G2 to detector [mm].')

# Detector
parser.add_argument('-pxs', dest='pixel_size',
                    type=NUMERICAL_TYPE,
                    help='Pixel size (square) [um].')
parser.add_argument('-fov', dest='pixel_size', nargs=2,
                    type=NUMERICAL_TYPE,
                    help='Number of pixels: x, y.')
parser.add_argument('-md', dest='detector_material',
                    type=str,
                    help='Choose detector material.')
parser.add_argument('-dd', dest='fill_thickness_g2',
                    type=NUMERICAL_TYPE,
                    help='Depth of detector [um].')

# Source
parser.add_argument('-fs', dest='focal_spot_size',
                    type=NUMERICAL_TYPE,
                    help='Focal spot size [um].')
parser.add_argument('-bg', dest='beam_geometry', default='parallel',
                    type=str,
                    choices=['parallel', 'sperical'],
                    help='Beam geometry. Default is "parallel".')

# Simulation
parser.add_argument('-sr', dest='sampling_rate', default=0,
                    type=NUMERICAL_TYPE,
                    help='sampling voxel size (cube). '
                    'Default is 0, then pixel_size * 1e1-3.')

if __name__ == '__main__':
    # Parse from command line
    args = parser.parse_args()

    # Check input

    # Set verbose level of logger
    logging_level = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }.get(args.verbose, logging.INFO)
    logger.setLevel(logging_level)
