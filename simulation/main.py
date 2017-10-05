import argparse
"""
Module to run grating interferometer simulation and metrics calculation

    System geometry
    ==========

    (0, 0, 0) point at source, detector center in (0, 0, z_d) ...

    Parameters
    ==========

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
        type [string]:                 'parallel' (default), 'spherical'

    Simulation:
        sampling_size [um]:             0 (default)
            (if 0, pixel_size * 1e1-3)

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
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                    '%(message)s')
# This technically only needs to be done once, in highest hirachy function!!!

# import materials
# import geometry
# import gratings

#  Parse input arguments
parser = argparse.ArgumentParser(description='Collect GI and Simulation '
                                 'parameters.')
# General input
parser.add_argument('--verbose', '-v', action='count',
                    help='Increase verbosity level. "v": error, "vv": warning,'
                    '"vvv": info (default), "vvvv": debug')

# Grating parameters
parser.add_argument('-g0', dest='type_g0', default='mix',
                    choices=['mix', 'phase', 'absorption'],
                    help='Choose which interaction will be considered for G0. '
                    'Default is "mix", both phase shift and absoprtion.')
parser.add_argument('-p0', dest='pitch_g0', default=0,
                    help='Choose pitch of G0 [um]. '
                    'Default is 0, no G0.')
parser.add_argument('-g0_material', dest='material_g0', default='',
                    help='Choose G0 grating line material. '
                    'Default is "", no G0.')
parser.add_argument('-d0', dest='thickness_g0', default=0,
                    help='Choose thickness of G0 grating lines [um]. '
                    'Default is 0, no G0 OR defined through phase shift.')
parser.add_argument('-shift0', dest='phase_shift_g0', default=0,
                    help='Choose phase shift of G0 grating lines [rad]. '
                    'Default is 0, no G0/pure absorption OR '
                    'defined through thickness.')
parser.add_argument('-g0_waFer', dest='wafer_material_g0', default='',
                    help='Choose G0 wafer material. '
                    'Default is "", no wafer.')
parser.add_argument('-d0_wafer', dest='wafer_thickness_g0', default=0,
                    help='Choose thickness of G0 wafer [um]. '
                    'Default is 0, no wafer.')
parser.add_argument('-g0_fill', dest='fill_material_g0', default='',
                    help='Choose G0 filling material. '
                    'Default is "", no line filling.')
parser.add_argument('-d0_fill', dest='fill_thickness_g0', default=0,
                    help='Choose thickness of G0 filling [um]. '
                    'Default is 0, no line filling.')

if __name__ == '__main__':

    # Read out parser
    args = parser.parse_args()

    # Set verbose level of logger
    logging_level = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }.get(args.verbose, logging.INFO)
    logger.setLevel(logging_level)

