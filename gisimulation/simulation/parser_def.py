"""
Module defining the parser for the gi_silmulation, which is called in main.py.

Also contains a dict class, which stores all parser optional arguments and
the corresponding destination (variable) names.

Usage
=====

input_parser():     defines and returns parser
                    Parameters:
                        numerical_type [numpy type] for all numerical arguments

@author: buechner_m <maria.buechner@gmail.com>
"""
import os.path
import sys
import re
import argparse
import numpy as np

# %% Constants
NUMERICAL_TYPE = np.float

# %% Classes


class _CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                       argparse.RawDescriptionHelpFormatter):
    """
    Custom formatter class combining all wanted formats.

    Parents
    #######

    argparse.ArgumentDefaultsHelpFormatter
    argparse.RawDescriptionHelpFormatter

    """
    pass


class _StoreNpArray(argparse._StoreAction):
    """
    argpars._StoreAction custom class to store multiple inout values into a
    numpy array. Values must be true positives.

    Usage
    #####

    action=_StoreNpArray

    """
    def __call__(self, parser, namespace, values, option_string=None):
        values = np.array(values, dtype=NUMERICAL_TYPE)
        if (values <= 0).any():
            parser.error("Values in {0} must be > 0.".format(option_string))
        setattr(namespace, self.dest, values)


class _PositiveNumber(argparse.Action):
    """
    argpars.Action custom class to only accept positives.

    Usage
    #####

    action=_PositiveNumber

    """
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 0:
            parser.error("{0} must be >= 0.".format(option_string))
        setattr(namespace, self.dest, values)


class _TruePositiveNumber(argparse.Action):
    """
    argpars.Action custom class to only accept true positives.

    Usage
    #####

    action=_TruePositiveNumber

    """
    def __call__(self, parser, namespace, values, option_string=None):
        if values <= 0:
            parser.error("{0} must be > 0.".format(option_string))
        setattr(namespace, self.dest, values)


class _CheckFile(argparse.Action):
    """
    Check if file input exists, add path to calling script if necessary.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        # Normaliye for OS
        values = os.path.normpath(values)
        # if main path missing, add, then check
        if not os.path.isabs(values):
            script_path = os.path.dirname(os.path.abspath(__file__))
            values = os.path.join(script_path, values)
        # Check if file exists
        if not os.path.exists(values):
            parser.error("{0} file ({1}) does not exist."
                         .format(option_string, values))
        setattr(namespace, self.dest, values)

# %% Functions


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
                                     formatter_class=_CustomFormatter)
    # USE SUBPARSERS FOR SIMULATION/GEOMETRY DEPENDENT ARGUMENTS...???

    # Verbosity of logger
    parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity level. 'v': error, "
                        "'vv': warning,"
                        "'vvv': info (None=default), 'vvvv': debug")

    # General input
    parser.add_argument('-bg', dest='beam_geometry', default='parallel',
                        type=str,
                        choices=['cone', 'parallel'], metavar='BEAM_GEOMETRY',
                        help="Beam geometry.")
    parser.add_argument('-gi', dest='geometry', default='sym',
                        type=str,
                        choices=['sym', 'conv', 'inv', 'free'],
                        metavar='GEOMETRY',
                        help="GI geometry. Choices are\n"
                        "'sym': symmetrical, 'conv': conventional, "
                        "'inv': inverse, 'free': free input.")
    # Grating parameters
    # G0
    parser.add_argument('-g0', dest='type_g0', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G0',
                        help="Choose which interaction will be considered "
                        "for G0. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p0', dest='pitch_g0',
                        action=_TruePositiveNumber,
                        help="Pitch of G0 [um].")
    parser.add_argument('-m0', dest='material_g0',
                        type=str,
                        help="G0 grating line material.")
    parser.add_argument('-d0', dest='thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 grating lines [um].")
    parser.add_argument('-shift0', dest='phase_shift_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Phase shift of G0 grating lines [rad].")
    parser.add_argument('-m0_wafer', dest='wafer_material_g0',
                        type=str,
                        help="G0 wafer material.")
    parser.add_argument('-d0_wafer', dest='wafer_thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 wafer [um].")
    parser.add_argument('-m0_fill', dest='fill_material_g0',
                        type=str,
                        help="G0 filling material.")
    parser.add_argument('-d0_fill', dest='fill_thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 filling [um].")
    # G1
    parser.add_argument('-g1', dest='type_g1', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G1',
                        help="Choose which interaction will be considered "
                        "for G1. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p1', dest='pitch_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pitch of G1 [um].")
    parser.add_argument('-m1', dest='material_g1',
                        type=str,
                        help="G1 grating line material.")
    parser.add_argument('-d1', dest='thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 grating lines [um].")
    parser.add_argument('-shift1', dest='phase_shift_g1', default=np.pi,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Phase shift of G1 grating lines [rad].")
    parser.add_argument('-m1_wafer', dest='wafer_material_g1',
                        type=str,
                        help="G1 wafer material.")
    parser.add_argument('-d1_wafer', dest='wafer_thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 wafer [um].")
    parser.add_argument('-m1_fill', dest='fill_material_g1',
                        type=str,
                        help="G1 filling material.")
    parser.add_argument('-d1_fill', dest='fill_thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 filling [um].")
    # G2
    parser.add_argument('-g2', dest='type_g2', default='mix',
                        type=str,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G2',
                        help="Choose which interaction will be considered "
                        "for G2. Default is 'mix', both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p2', dest='pitch_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pitch of G2 [um].")
    parser.add_argument('-m2', dest='material_g2',
                        type=str,
                        help="G2 grating line material.")
    parser.add_argument('-d2', dest='thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 grating lines [um]..")
    parser.add_argument('-shift2', dest='phase_shift_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Phase shift of G2 grating lines [rad].")
    parser.add_argument('-m2_wafer', dest='wafer_material_g2',
                        type=str,
                        help="G2 wafer material.")
    parser.add_argument('-d2_wafer', dest='wafer_thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 wafer [um].")
    parser.add_argument('-m2_fill', dest='fill_material_g2',
                        type=str,
                        help="G2 filling material.")
    parser.add_argument('-d2_fill', dest='fill_thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 filling [um].")
    # Design
    parser.add_argument('-t', dest='talbot_order',
                        type=numerical_type,
                        help="Talbot order.")
    parser.add_argument('-s2g', dest='distance_source2grating',
                        type=numerical_type,
                        help="Distance from source to first grating [mm].")
    parser.add_argument('-g2d', dest='distance_G2_detector',
                        type=numerical_type,
                        help="Distance from G2 to detector [mm].")

    # Detector
    parser.add_argument('-pxs', dest='pixel_size',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pixel size (square) [um].")
    parser.add_argument('-fov', dest='field_of_view', nargs=2,
                        action=_StoreNpArray,
                        metavar='FIELD_OF_VIEW',
                        type=np.int,
                        help="Number of pixels: x y.")
    parser.add_argument('-md', dest='material_detector',
                        type=str,
                        help="Choose detector material.")
    parser.add_argument('-dd', dest='thickness_detector',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of detector [um].")

    # Source
    parser.add_argument('-fs', dest='focal_spot_size', default=0,
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Focal spot size [um]. If 0, infinite source "
                        "size.")

    # Spectrum
    parser.add_argument('-e', dest='design_energy', required=True,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Design energy of GI [keV].")
    parser.add_argument('-spec', dest='spectrum_file',
                        action=_CheckFile,
                        metavar='SPECTRUM_FILE',
                        nargs='?', type=str,
                        help="Location of spectrum file (.csv).\n"
                        "Full path or relative path ('./relative_path') "
                        "from calling script.\n"
                        "File format:\n"
                        "energy,photons\n"
                        "e1,p1\n"
                        "e2,p2\n"
                        ".,.\n"
                        ".,.\n"
                        ".,.")
    parser.add_argument('-r', dest='spectrum_range',
                        action=_StoreNpArray,
                        metavar='SPECTRUM_RANGE',
                        nargs=2, type=numerical_type,
                        help=("Range of energies [keV]: min max.\n"
                        "If specturm from file: cut off at >= min and"
                        "<= max.\n"
                        "If just range: from min to <=max in 1 keV steps."))
    parser.add_argument('-sps', dest='spectrum_step', default=1,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Step size of range [keV].")

    # Calculations
    parser.add_argument('-sr', dest='sampling_rate', default=0,
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="sampling voxel size (cube). "
                        "If 0, it is pixel_size * 1e-3.")

    # Return
    return parser


def get_arguments_info(parser):
    """
    Read help message into variable by putting the stdout output from
    parser.print_help() into a custom sdtout.

    Parameters
    ##########

    parser [argparse.ArgumentParser]

    Returns
    #######

    arguments_info [dict]:  arguments_info[variable_name] =
                                [optional_key, help_message]

    Usage
    #####

    info = get_arguments_info(parser)

    # for variable_name
    optional_key = info[variable_name][0]
    help_message = info[variable_name][1]

    Notes
    #####

    Removes all linebreaks in help message, as they are not the original
    anymore, but defined via the help formatter used by parser.print_help


    """
    # Reset stdout
    old_stdout = sys.stdout
    sys.stdout = parser_help_string = _ListStream()
    parser.print_help()
    # Set back to console
    sys.stdout = old_stdout

    # Get infos
    complete_help_message = parser_help_string.data[0]
    help_messages = complete_help_message.split('optional arguments:')[1]
    help_messages = help_messages.split('-')[7:]
    arguments_info = dict()
    for help_message in help_messages:
        # "optional_key METAVAR(S)       help_message\n"
        words = re.split(' ', help_message)
        optional_key = '-' + words[0]
        variable_name = words[1].lower().rstrip()  # Make lower case and
                                                   # remove trailing \n
        # Remove potential [] (for e.g. file types)
        variable_name = variable_name.replace("[", "")  # Remove potential []
        variable_name = variable_name.replace("]", "")
        # For nargs=2, remove second entry
        if words[1] in words[2]:
            help_text = filter(None, words[3:])  # Remove ''
        else:
            help_text = filter(None, words[2:])  # Remove ''
        help_text = ' '.join(help_text)
        help_text= re.sub('\n', '', help_text)  # remove print_help-format
                                                # induces \n
        arguments_info[variable_name] = [optional_key, help_text]

    return arguments_info

# %% Private utilities


class _ListStream:
    """
    Custom stdout to print into list of string.
    """
    def __init__(self):
        self.data = []
    def write(self, s):
        self.data.append(s)




