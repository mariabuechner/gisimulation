"""
Module defining the parser for the gi_silmulation, which is called in main.py.

Classes
=======

CustomFormatter:    Combines argparse.ArgumentDefaultsHelpFormatter and
                    argparse.RawDescriptionHelpFormatter

Functions
=========

input_parser:       defines and returns parser
                    Parameters:
                        numerical_type [numpy type] for all numerical arguments

@author: buechner_m <maria.buechner@gmail.com>
"""
import argparse
import numpy as np

# Constants
NUMERICAL_TYPE = np.float

# =============================================================================
# Classes
# =============================================================================


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    """
    Custom formatter class combining all wanted formats.
    """
    pass

# =============================================================================
# Functions
# =============================================================================


def input_parser(numerical_type=NUMERICAL_TYPE):
    """
    Parameters
    ==========

    numerical_type (i.e. numpy.float), default: NUMERICAL_TYPE (np.float)

    Returns
    =======

    parser

    Note
    ====

    error handling to unpractical with argparse
    -> make all arguments optional and check manually later!

    """

    parser = argparse.ArgumentParser(description="Collect GI and simulation "
                                     "parameters.\n"
                                     "Parse from .txt file: "
                                     "@filedir/filename.txt.\n"
                                     "Can use multiple files. Arguments can \n"
                                     "be overwritten afterwards in command "
                                     "line.\n"
                                     "File layout:\n"
                                     "\tArgName ArgValue\n"
                                     "Example:\n"
                                     "\t-sr 100\n"
                                     "\t-p0 2.4\n",
                                     fromfile_prefix_chars='@',
                                     formatter_class=CustomFormatter)
    # USE SUBPARSERS FOR SIMULATION/GEOMETRY DEPENDENT ARGUMENTS...???

    # General input
    parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity level. 'v': error, "
                        "'vv': warning,"
                        "'vvv': info (None=default), 'vvvv': debug")
    parser.add_argument('-gi', dest='geometry', default='sym',
                        type=str,
                        choices=['sym', 'conv', 'inv', 'free'],
                        help="GI geometry. Choices are\n"
                        "'sym': symmetrical, 'conv': conventional, "
                        "'inv': inverse, 'free': free input.")
    # Grating parameters
    # G0
    parser.add_argument('-g0', dest='type_g0', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'],
                        help="Choose which interaction will be considered "
                        "for G0. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p0', dest='pitch_g0',
                        help="Pitch of G0 [um].")
    parser.add_argument('-m0', dest='material_g0',
                        type=str,
                        help="G0 grating line material.")
    parser.add_argument('-d0', dest='thickness_g0',
                        type=numerical_type,
                        help="Depth of G0 grating lines [um].")
    parser.add_argument('-shift0', dest='phase_shift_g0',
                        type=numerical_type,
                        help="Phase shift of G0 grating lines [rad].")
    parser.add_argument('-m0_wafer', dest='wafer_material_g0',
                        type=str,
                        help="G0 wafer material.")
    parser.add_argument('-d0_wafer', dest='wafer_thickness_g0',
                        type=numerical_type,
                        help="Depth of G0 wafer [um].")
    parser.add_argument('-m0_fill', dest='fill_material_g0',
                        type=str,
                        help="G0 filling material.")
    parser.add_argument('-d0_fill', dest='fill_thickness_g0',
                        type=numerical_type,
                        help="Depth of G0 filling [um].")
    # G1
    parser.add_argument('-g1', dest='type_g1', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'],
                        help="Choose which interaction will be considered "
                        "for G1. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p1', dest='pitch_g1', required=True,
                        type=numerical_type,
                        help="Pitch of G1 [um].")
    parser.add_argument('-m1', dest='material_g1', required=True,
                        type=str,
                        help="G1 grating line material.")
    parser.add_argument('-d1', dest='thickness_g1',
                        type=numerical_type,
                        help="Depth of G1 grating lines [um].")
    parser.add_argument('-shift1', dest='phase_shift_g1', default=np.pi,
                        type=numerical_type,
                        help="Phase shift of G1 grating lines [rad].")
    parser.add_argument('-m1_wafer', dest='wafer_material_g1',
                        type=str,
                        help="G1 wafer material.")
    parser.add_argument('-d1_wafer', dest='wafer_thickness_g1',
                        type=numerical_type,
                        help="Depth of G1 wafer [um].")
    parser.add_argument('-m1_fill', dest='fill_material_g1',
                        type=str,
                        help="G1 filling material.")
    parser.add_argument('-d1_fill', dest='fill_thickness_g1',
                        type=numerical_type,
                        help="Depth of G1 filling [um].")
    # G2
    parser.add_argument('-g2', dest='type_g2', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'],
                        help="Choose which interaction will be considered "
                        "for G2. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p2', dest='pitch_g2',
                        type=numerical_type,
                        help="Pitch of G2 [um].")
    parser.add_argument('-m2', dest='material_g2',
                        type=str,
                        help="G2 grating line material.")
    parser.add_argument('-d2', dest='thickness_g2',
                        type=numerical_type,
                        help="Depth of G2 grating lines [um]..")
    parser.add_argument('-shift2', dest='phase_shift_g2',
                        type=numerical_type,
                        help="Phase shift of G2 grating lines [rad].")
    parser.add_argument('-m2_wafer', dest='wafer_material_g2',
                        type=str,
                        help="G2 wafer material.")
    parser.add_argument('-d2_wafer', dest='wafer_thickness_g2',
                        type=numerical_type,
                        help="Depth of G2 wafer [um].")
    parser.add_argument('-m2_fill', dest='fill_material_g2',
                        type=str,
                        help="G2 filling material.")
    parser.add_argument('-d2_fill', dest='fill_thickness_g2',
                        type=numerical_type,
                        help="Depth of G2 filling [um].")
    # Design
    parser.add_argument('-e', dest='design_energy', required=True,
                        type=numerical_type,
                        help="Design energy of GI [keV].")
    parser.add_argument('-t', dest='talbot_order',
                        type=numerical_type,
                        help="Talbot order.")
    parser.add_argument('-spec', dest='spectrum',  # NEEDTO IMPL CUSTOM
                                                   # FILE INPUT?
                        nargs='?', type=argparse.FileType('r'),
                        help="Location of spectrum file.")

    parser.add_argument('-s2g', dest='distance_source2grating',
                        type=numerical_type,
                        help="Distance from source to first grating [mm].")
    parser.add_argument('-g2d', dest='distance_G2_detector',
                        type=numerical_type,
                        help="Distance from G2 to detector [mm].")

    # Detector
    parser.add_argument('-pxs', dest='pixel_size', required=True,
                        type=numerical_type,
                        help="Pixel size (square) [um].")
    parser.add_argument('-fov', dest='field_of_view', nargs=2, required=True,
                        type=numerical_type,
                        help="Number of pixels: x, y.")
    parser.add_argument('-md', dest='material_detector',
                        type=str,
                        help="Choose detector material.")
    parser.add_argument('-dd', dest='thickness_detector',
                        type=numerical_type,
                        help="Depth of detector [um].")

    # Source
    parser.add_argument('-fs', dest='focal_spot_size', default=0,
                        type=numerical_type,
                        help="Focal spot size [um]. If 0, infinite source "
                        "size.")
    parser.add_argument('-bg', dest='beam_geometry', default='cone',
                        type=str,
                        choices=['cone', 'parallel'],
                        help="Beam geometry.")

    # Simulation
    parser.add_argument('-sr', dest='sampling_rate', default=0,
                        type=numerical_type,
                        help="sampling voxel size (cube). "
                        "If 0, it is pixel_size * 1e-4.")

    # Return
    return parser
