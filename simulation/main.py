"""
Module to run grating interferometer simulation and metrics calculation

    System geometry
    ==========

    (0, 0, 0) point at source, detector center in (0, 0, z_d) ...

    Parameters
    ==========

    General:
        '--verbose', '-v':              flag for verbosity level of logger
        input_file:                     location of inout file,
                                        default '' (no file)
        sampling_size [um]:             0 (default)
            (if 0, pixel_size * 1e1-3)

    Grating interferometer:
        G0:
            type_g0 [string]:           'mix' (default), 'phase', 'absorption'
            pitch_g0 [um]:              0 (default)
            material_g0 [string]:       '' (default)
            thickness_g0 [um]:          0 (default)
            phase_shift_g0 [rad]:       0 (default)
            wafer_material_g0 [string]: '' (default)
            wafer_thickness_g0 [um]:    0 (default)
            fill_material_g0 [string]:  '' (default)
            fill_thickness_g0 [um]:     0 (default)
        G1:
            type_g1 [string]:           'mix' (default), 'phase', 'absorption'
            pitch_g1 [um]:              0 (default)
            material_g1 [string]
            thickness_g1 [um]:          0 (default)
            phase_shift_g1 [rad]:       0 (default)
            wafer_material_g1 [string]: '' (default)
            wafer_thickness_g1 [um]:    0 (default)
            fill_material_g1 [string]:  '' (default)
            fill_thickness_g1 [um]:     0 (default)
        G2:
            type_g2 [string]:           'mix' (default), 'phase', 'absorption'
            pitch_g2 [um]:              0 (default)
            material_g2 [string]
            thickness_g2 [um]:          0 (default)
            phase_shift_g2 [rad]:       0 (default)
            wafer_material_g2 [string]: '' (default)
            wafer_thickness_g2 [um]:    0 (default)
            fill_material_g2 [string]:  '' (default)
            fill_thickness_g2 [um]:     0 (default)
        design_energy [keV]
        spectrum [string]:              '' (default)
        distance_source2grating [mm]:   0 (default)
            (to G1 or G0, if defined)
        distance_G2_detector [mm]:      0 (default)

    Detector:
        pixel_size [um] (square)
        detector_size [#x-pixel, #y-pixel]
            (FOV)
        detector_material [string]
        detector_thickness [um]

    Source:
        focal_spot_size [um]
        beam_geometry [string]:         'parallel' (default), 'spherical'


    NECESSARY INPUT:
        Gratings:
            material + thickness OR phase_shift
        GI:
            1 pitch + 1 distance
            G1 and G2 defined
            if spherical beam: + distance_source2grating + distance_G2_detector
        Detector:
            pixel_size + FOV + detector_material + detector_thickness
        Source:
            focal_spot_size

    Returns
    =======

    Notes
    =====

    0 or '' indicated not-defined or non-existent component

@author: buechner_m
"""
import argparse
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                    '%(message)s')
# This technically only needs to be done once, in highest hirachy function!!!

# import materials
# import geometry
# import gratings

#  Parse input arguments
parser = argparse.ArgumentParser(description='Collect GI and simulation '
                                 'parameters.')
# USE SUBPARSERS FOR SIMULATION/GEOMETRY DEPENDENT ARGUMENTS...

# General input
parser.add_argument('--verbose', '-v', action='count',
                    help='Increase verbosity level. "v": error, "vv": warning,'
                    '"vvv": info (default), "vvvv": debug')
parser.add_argument('input_file', nargs='?', type=argparse.FileType('r'),
                    default='',
                    help='Location of input file containing all (necessary) '
                    'parameters. Default is "", parse via command line.')
parser.add_argument('sampling_size', default=0,
                    help='sampling vocel size (cube). '
                    'Default is 0, then pixel_size * 1e1-3.')

# Grating parameters
# G0
parser.add_argument('g0', dest='type_g0', default='mix',
                    choices=['mix', 'phase', 'absorption'],
                    help='Choose which interaction will be considered for G0. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('p0', dest='pitch_g0', default=0,
                    help='Pitch of G0 [um]. '
                    'Default is 0, no G0.')
parser.add_argument('m0', dest='material_g0', default='',
                    help='G0 grating line material. '
                    'Default is "", no G0.')
parser.add_argument('d0', dest='thickness_g0', default=0,
                    help='Depth of G0 grating lines [um]. '
                    'Default is 0, no G0 OR defined through phase shift.')
parser.add_argument('shift0', dest='phase_shift_g0', default=0,
                    help='Phase shift of G0 grating lines [rad]. '
                    'Default is 0, no G0/pure absorption OR '
                    'defined through thickness.')
parser.add_argument('m0_wafer', dest='wafer_material_g0', default='',
                    help='G0 wafer material. '
                    'Default is "", no wafer.')
parser.add_argument('d0_wafer', dest='wafer_thickness_g0', default=0,
                    help='Depth of G0 wafer [um]. '
                    'Default is 0, no wafer.')
parser.add_argument('m0_fill', dest='fill_material_g0', default='',
                    help='G0 filling material. '
                    'Default is "", no line filling.')
parser.add_argument('d0_fill', dest='fill_thickness_g0', default=0,
                    help='Depth of G0 filling [um]. '
                    'Default is 0, no line filling.')
# G1
parser.add_argument('g1', dest='type_g1', default='mix',
                    choices=['mix', 'phase', 'absorption'],
                    help='Choose which interaction will be considered for G1. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('p1', dest='pitch_g1', default=0,
                    help='Pitch of G1 [um]. '
                    'Default is 0, no G1.')
parser.add_argument('m1', dest='material_g1',
                    help='G1 grating line material.')
parser.add_argument('d1', dest='thickness_g1', default=0,
                    help='Depth of G1 grating lines [um]. '
                    'Default is 0, no G1 OR defined through phase shift.')
parser.add_argument('shift1', dest='phase_shift_g1', default=0,
                    help='Phase shift of G1 grating lines [rad]. '
                    'Default is 0, no G1/pure absorption OR '
                    'defined through thickness.')
parser.add_argument('m1_wafer', dest='wafer_material_g1', default='',
                    help='G1 wafer material. '
                    'Default is "", no wafer.')
parser.add_argument('d1_wafer', dest='wafer_thickness_g1', default=0,
                    help='Depth of G1 wafer [um]. '
                    'Default is 0, no wafer.')
parser.add_argument('m1_fill', dest='fill_material_g1', default='',
                    help='G1 filling material. '
                    'Default is "", no line filling.')
parser.add_argument('d1_fill', dest='fill_thickness_g1', default=0,
                    help='Depth of G1 filling [um]. '
                    'Default is 0, no line filling.')
# G2
parser.add_argument('g2', dest='type_g2', default='mix',
                    choices=['mix', 'phase', 'absorption'],
                    help='Choose which interaction will be considered for G2. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('p2', dest='pitch_g2', default=0,
                    help='Pitch of G2 [um]. '
                    'Default is 0, no G2.')
parser.add_argument('m2', dest='material_g2',
                    help='G2 grating line material.')
parser.add_argument('d2', dest='thickness_g2', default=0,
                    help='Depth of G2 grating lines [um]. '
                    'Default is 0, no G2 OR defined through phase shift.')
parser.add_argument('shift2', dest='phase_shift_g2', default=0,
                    help='Phase shift of G2 grating lines [rad]. '
                    'Default is 0, no G2/pure absorption OR '
                    'defined through thickness.')
parser.add_argument('m2_wafer', dest='wafer_material_g2', default='',
                    help='G2 wafer material. '
                    'Default is "", no wafer.')
parser.add_argument('d2_wafer', dest='wafer_thickness_g2', default=0,
                    help='Depth of G2 wafer [um]. '
                    'Default is 0, no wafer.')
parser.add_argument('m2_fill', dest='fill_material_g2', default='',
                    help='G2 filling material. '
                    'Default is "", no line filling.')
parser.add_argument('d2_fill', dest='fill_thickness_g2', default=0,
                    help='Depth of G2 filling [um]. '
                    'Default is 0, no line filling.')
# Design
parser.add_argument('e', dest='design_energy',
                    help='Design energy of GI [keV].')
parser.add_argument('spectrum', nargs='?', type=argparse.FileType('r'),
                    default='',
                    help='Location of spectrum file. '
                    'Default is "", no spectrum.')
parser.add_argument('s2g', dest='distance_source2grating', default=0,
                    help='Distance from source to first grating [mm]. '
                    'Default is 0.')
parser.add_argument('g2d', dest='distance_G2_detector', default=0,
                    help='Distance from G2 to detector [mm]. '
                    'Default is 0.')

# Detector
parser.add_argument('pxs', dest='pixel_size',
                    help='Pixel size (square) [um].')
parser.add_argument('fov', dest='pixel_size', nargs=2,
                    help='Number of pixels: x, y.')
parser.add_argument('md', dest='detector_material',
                    help='Choose detector material material.')
parser.add_argument('dd', dest='fill_thickness_g2', default=0,
                    help='Depth of detector [um].')

# Source
parser.add_argument('fs', dest='focal_spot_size',
                    help='Focal spot size [um].')
parser.add_argument('bg', dest='beam_geometry', default='parallel',
                    choices=['parallel', 'sperical'],
                    help='Beam geometry. Default is "parallel".')


if __name__ == '__main__':

    # Read out parser
    if args.input_file:
        # args = read_input_file(input_file)
        pass
    else:
        args = parser.parse_args()

    # Set verbose level of logger
    logging_level = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }.get(args.verbose, logging.INFO)
    logger.setLevel(logging_level)
