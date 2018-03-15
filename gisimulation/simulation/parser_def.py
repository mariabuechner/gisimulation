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
    argpars._StoreAction custom class to store multiple input values into a
    numpy array. Values must be true positives.

    Usage
    #####

    action=_StoreNpArray

    """
    def __call__(self, parser, namespace, values, option_string=None):
        values = np.array(values).astype(np.float).astype(NUMERICAL_TYPE)
        if (values <= 0).any():
            parser.error("Values in {0} must be > 0.".format(option_string))
        setattr(namespace, self.dest, values)


class _StoreNpIntArray(argparse._StoreAction):
    """
    argpars._StoreAction custom class to store multiple input values into a
    numpy array. Values must be true positives.

    Usage
    #####

    action=_StoreNpIntArray

    """
    def __call__(self, parser, namespace, values, option_string=None):
        values = np.array(values).astype(np.float).round().astype(np.int)
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


def _PhaseValue(value):
    """
    Custom class to accept true positives or 'pi' or 'pi/2'.

    Parameters
    ##########

    value:      number or 'pi' or 'pi/2'

    Returns
    #######

    value [NUMERICAL_TYPE]

    """
    if type(value) is str:
        if value.lower() == 'pi':
            value = np.pi
        elif value.lower() == 'pi/2':
            value = np.pi / 2
    return NUMERICAL_TYPE(value)


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
                                     "File layout:        Example:\n"
                                     "ArgName1                -sr\n"
                                     "ArgValue1               100\n"
                                     "ArgName2                -p0\n"
                                     "ArgValue2               2.4\n"
                                     "ArgName3                -fov\n"
                                     "ArgValue3.1             200\n"
                                     "ArgValue3.2             400\n"
                                     "    .                    .\n"
                                     "    .                    .\n"
                                     "    .                    .",
                                     usage="Parameters that are defined but "
                                     "not applicable in current setup will "
                                     "be ignored without warning.",
                                     fromfile_prefix_chars='@',
                                     formatter_class=_CustomFormatter)
    # USE SUBPARSERS FOR SIMULATION/GEOMETRY DEPENDENT ARGUMENTS...???

    # Verbosity of logger
    parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity level. 'v': error, "
                        "'vv': warning,"
                        "'vvv': info (None=default), 'vvvv': debug")

    # General and GI Design
    parser.add_argument('-gi', dest='gi_geometry', default='sym',
                        type=str.lower, required=True,
                        choices=['sym', 'conv', 'inv', 'free'],
                        metavar='GI_GEOMETRY',
                        help="GI geometry. Choices are\n"
                        "'sym': symmetrical, 'conv': conventional, "
                        "'inv': inverse, 'free': free input.")
    parser.add_argument('-e', dest='design_energy', required=True,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Design energy of GI [keV].")
    parser.add_argument('-t', dest='talbot_order',
                        type=numerical_type,
                        help="Talbot order.")
    parser.add_argument('--dual_phase',
                        action='store_true',
                        help="Option for dual phase setup [bool]. "
                        "Only valid for conventional setup and without G0.")
    parser.add_argument('-bg', dest='beam_geometry', default='parallel',
                        type=str.lower, required=True,
                        choices=['cone', 'parallel'], metavar='BEAM_GEOMETRY',
                        help="Beam geometry. Choices are\n"
                        "'cone': cone/divergent beam, "
                        "'parallel': parallel beam (infinite source size).")
    parser.add_argument('-sr', dest='sampling_rate',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Sampling voxel size (cube). "
                        "If not set, it is pixel_size * 1e-3.")
    parser.add_argument('-lut', dest='look_up_table', default='nist',
                        type=str.lower,
                        choices=['nist', 'x0h'],
                        metavar='LOOK_UP_TABLE',
                        help="Source of material properties LUT. Choices are\n"
                        "'NIST', 'X0h'.")
    parser.add_argument('--photo_only',
                        action='store_true',
                        help="Option to consider only photo_absorption "
                        "[bool]. Else, the total cross_section is considered "
                        "(default).")

    # Source
    parser.add_argument('-fs', dest='focal_spot_size',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Focal spot size [um]. Is infinite in case of "
                        "parallel beam greometry.")
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
                        ".,.\n\n"
                        "Photons are in [1/pixel/sec].")
    parser.add_argument('-r', dest='spectrum_range',
                        action=_StoreNpArray,
                        metavar='SPECTRUM_RANGE',
                        nargs=2,
                        help=("Range of energies [keV]: min max.\n"
                              "If specturm from file: cut off at >= min and"
                              "<= max.\n"
                              "If just range: from min to <=max in 1 keV "
                              "steps."))
    parser.add_argument('-sps', dest='spectrum_step', default=1,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Step size of range [keV].")
    parser.add_argument('-et', dest='exposure_time', default=1,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Exposure time per acquired image [s].")
    parser.add_argument('-fm', dest='material_filter',
                        type=str,
                        help="Choose filter material. Note: non-shape "
                        "specific filter, filters homogenously over beam.")
    parser.add_argument('-tf', dest='thickness_filter',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of filter [um]. Note: non-shape "
                        "specific filter, filters homogenously over beam.")

    # Detector
    parser.add_argument('-dt', dest='detector_type', default='photon',
                        type=str.lower,
                        choices=['photon', 'conv'],
                        metavar='DETECTOR_TYPE',
                        help="Detector type. Choices are\n"
                        "'photon': photon counting (PSF of one pixel), "
                        "'conv': conventional (PSF larger one pixel).")
    parser.add_argument('-psf', dest='point_spread_function',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Point spread function (PSF) [um]: "
                        "FWHM (Full width at half maximum) of gaussian shape.")
    parser.add_argument('-pxs', dest='pixel_size', #required=True,
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pixel size (square) [um].")
    parser.add_argument('-fov', dest='field_of_view', nargs=2,
                        action=_StoreNpIntArray,
                        metavar='FIELD_OF_VIEW',
                        help="Number of pixels: x y.")
    parser.add_argument('-dth', dest='detector_threshold',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Cut of threshold of detector [keV], everything "
                        "below will not be displayed.")
    parser.add_argument('-dm', dest='material_detector',
                        type=str,
                        help="Choose detector material.")
    parser.add_argument('-td', dest='thickness_detector',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of detector [um].")
    parser.add_argument('--curved_detector',
                        action='store_true',
                        help=("Option to have curved detector with same "
                              "radius as distance from source [bool]. Else, "
                              "flat and perpendicular to center of beam "
                              "(default)."))

    # Distances
    parser.add_argument('-fd', dest='fixed_distance',
                        type=str.lower,
                        choices=['distance_source_g1', 'distance_source_g2',
                                 'distance_g0_g1', 'distance_g0_g2'],
                        metavar='FIXED_DISTANCE',
                        help="Choose based on which fixed distance the "
                        "interferometer will be calcualted from. Note that G0 "
                        "can only be chosen if G0 is added to the setup.")
    # From source
    parser.add_argument('-sg0', dest='distance_source_g0',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from source to G0 [mm].")
    parser.add_argument('-sg1', dest='distance_source_g1',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from source to G1 [mm].")
    parser.add_argument('-sg2', dest='distance_source_g2',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from source to G2 [mm].")
    parser.add_argument('-s2d', dest='distance_source_detector',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from source to detector [mm].")
    # From G0
    parser.add_argument('-g0g1', dest='distance_g0_g1',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G0 to G1 [mm].")
    parser.add_argument('-g0g2', dest='distance_g0_g2',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G0 to G2 [mm].")
    parser.add_argument('-g0d', dest='distance_g0_detector',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G0 to detector [mm].")
    # From G1
    parser.add_argument('-g1g2', dest='distance_g1_g2',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G1 to G2 [mm].")
    parser.add_argument('-g1d', dest='distance_g1_detector',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G1 to detector [mm].")
    # From G2
    parser.add_argument('-g2d', dest='distance_g2_detector',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help="Distance from G2 to detector [mm].")

    # Grating parameters
    parser.add_argument('-fg', dest='fixed_grating',
                        type=str.lower,
                        choices=['g0', 'g1', 'g2'], metavar='FIXED_GRATING',
                        help="Choose on which grating the calculations will "
                        "based on. Note that G0 cannot be chosen for "
                        "parallel beam geometries.")
    # G0
    parser.add_argument('-g0', dest='type_g0',
                        type=str.lower,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G0',
                        help="Choose which interaction will be considered "
                        "for G0. 'mix': both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p0', dest='pitch_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pitch of G0 [um].")
    parser.add_argument('-dc0', dest='duty_cycle_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Duty cycle of G0 ]0...1[.")
    parser.add_argument('-m0', dest='material_g0',
                        type=str,
                        help="G0 grating line material.")
    parser.add_argument('-t0', dest='thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 grating lines [um].")
    parser.add_argument('-s0', dest='phase_shift_g0',
                        action=_TruePositiveNumber,
                        type=_PhaseValue,
                        help="Phase shift of G0 grating lines [rad] or ['pi' "
                        "or 'pi/2'].")
    parser.add_argument('-mw0', dest='wafer_material_g0',
                        type=str,
                        help="G0 wafer material.")
    parser.add_argument('-tw0', dest='wafer_thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 wafer [um].")
    parser.add_argument('-mf0', dest='fill_material_g0',
                        type=str,
                        help="G0 filling material.")
    parser.add_argument('-tf0', dest='fill_thickness_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G0 filling [um].")
    parser.add_argument('--g0_bent',
                        action='store_true',
                        help="Option to make G0 bent shaped [bool]. "
                        "Else, it is straight and perpendicular to the "
                        "beam (default).")
    parser.add_argument('--g0_matching',
                        action='store_true',
                        help="Option to bent G0 matching to its distance "
                        " from the source [bool]. If so, radius of G0 will "
                        "be ignored. Else, radius of G0 needs to be set "
                        "(default).")
    parser.add_argument('-r0', dest='radius_g0',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Radius if bent G0 [mm].")
    # G1
    parser.add_argument('-g1', dest='type_g1',
                        type=str.lower,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G1',
                        help="Choose which interaction will be considered "
                        "for G1. 'mix': both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p1', dest='pitch_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pitch of G1 [um].")
    parser.add_argument('-dc1', dest='duty_cycle_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Duty cycle of G1 ]0...1[.")
    parser.add_argument('-m1', dest='material_g1',
                        type=str,
                        help="G1 grating line material.")
    parser.add_argument('-t1', dest='thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 grating lines [um].")
    parser.add_argument('-s1', dest='phase_shift_g1', default=np.pi,
                        action=_TruePositiveNumber,
                        type=_PhaseValue,
                        help="Phase shift of G1 grating lines [rad] or ['pi' "
                        "or 'pi/2'].")
    parser.add_argument('-mw1', dest='wafer_material_g1',
                        type=str,
                        help="G1 wafer material.")
    parser.add_argument('-tw1', dest='wafer_thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 wafer [um].")
    parser.add_argument('-mf1', dest='fill_material_g1',
                        type=str,
                        help="G1 filling material.")
    parser.add_argument('-tf1', dest='fill_thickness_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G1 filling [um].")
    parser.add_argument('--g1_bent',
                        action='store_true',
                        help="Option to make G1 bent shaped [bool]. "
                        "Else, it is straight and perpendicular to the "
                        "beam (default).")
    parser.add_argument('--g1_matching',
                        action='store_true',
                        help="Option to bent G1 matching to its distance "
                        " from the source [bool]. If so, radius of G1 will "
                        "be ignored. Else, radius of G1 needs to be set "
                        "(default).")
    parser.add_argument('-r1', dest='radius_g1',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Radius if bent G1 [mm].")
    # G2
    parser.add_argument('-g2', dest='type_g2',
                        type=str.lower,
                        choices=['mix', 'phase', 'abs'], metavar='TYPE_G2',
                        help="Choose which interaction will be considered "
                        "for G2. 'mix': both phase shift and "
                        "absoprtion.")
    parser.add_argument('-p2', dest='pitch_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Pitch of G2 [um].")
    parser.add_argument('-dc2', dest='duty_cycle_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Duty cycle of G2 ]0...1[.")
    parser.add_argument('-m2', dest='material_g2',
                        type=str,
                        help="G2 grating line material.")
    parser.add_argument('-t2', dest='thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 grating lines [um]..")
    parser.add_argument('-s2', dest='phase_shift_g2',
                        action=_TruePositiveNumber,
                        type=_PhaseValue,
                        help="Phase shift of G2 grating lines [rad] or ['pi' "
                        "or 'pi/2'].")
    parser.add_argument('-mw2', dest='wafer_material_g2',
                        type=str,
                        help="G2 wafer material.")
    parser.add_argument('-tw2', dest='wafer_thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 wafer [um].")
    parser.add_argument('-mf2', dest='fill_material_g2',
                        type=str,
                        help="G2 filling material.")
    parser.add_argument('-tf2', dest='fill_thickness_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Depth of G2 filling [um].")
    parser.add_argument('--g2_bent',
                        action='store_true',
                        help="Option to make G2 bent shaped [bool]. "
                        "Else, it is straight and perpendicular to the "
                        "beam (default).")
    parser.add_argument('--g2_matching',
                        action='store_true',
                        help="Option to bent G2 matching to its distance "
                        " from the source [bool]. If so, radius of G2 will "
                        "be ignored. Else, radius of G2 needs to be set "
                        "(default).")
    parser.add_argument('-r2', dest='radius_g2',
                        action=_TruePositiveNumber,
                        type=numerical_type,
                        help="Radius if bent G2 [mm].")

    # Sample
    parser.add_argument('-sp', dest='sample_position',
                        type=str.lower,
                        choices=['as',
                                 'bg0', 'ag0',
                                 'bg1', 'ag1',
                                 'bg2', 'ag2',
                                 'bd'],
                        metavar='SAMPLE_POSITION',
                        help="Choose where the sample will be positioned. "
                        "Choices are: 'as': after source, 'bg0': before G0, "
                        "'ag0': after G0, 'bg1': before G1, 'ag1': after G1, "
                        "'bg2': before G2, 'ag2': after G2, 'bd': before "
                        "detector.")
    parser.add_argument('-sd', dest='sample_distance',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help=("Distance from sample to reference component "
                              "[mm]."))
    # ########## Temp ########################
    parser.add_argument('-sdm', dest='sample_diameter',
                        action=_PositiveNumber,
                        type=numerical_type,
                        help=("Sample diameter [mm] (if sample shape is "
                              "circular)."))
    parser.add_argument('-ssp', dest='sample_shape',
                        type=str.lower,
                        choices=['circular'], metavar='SAMPLE_SHAPE',
                        help="Choose which shape the sample is.")
    # ########## Temp ########################

    # Return
    return parser


def get_arguments_info(parser):
    """
    Read help message into variable by putting the stdout output from
    parser.print_help() into a custom sdtout.

    Parameters
    ==========

    parser [argparse.ArgumentParser]

    Returns
    =======

    arguments_info [dict]:  arguments_info[variable_name] =
                                [optional_key, help_message]

    Usage
    =====

    info = get_arguments_info(parser)

    # for variable_name
    optional_key = info[variable_name][0]
    help_message = info[variable_name][1]

    Notes
    =====

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
        # Flags (--flag)
        # A) generate an extra empty help_message
        if not help_message:
            continue

        # "optional_key METAVAR(S)       variable_help\n"
        # Words in message
        words = re.split(' ', help_message)
        variable_key = '-' + words[0]
        # B) do not accept a metavar (if store_true): words[1] is ''
        # C) have 2 dashes (--) in their variable key
        if not words[1]:
            words[1] = words[0]
            variable_key = '--' + words[0]

        variable_name = words[1].lower().rstrip()  # Make lower case and
                                                   # remove trailing \n
        # Remove potential [] (for e.g. file types)
        variable_name = variable_name.replace("[", "")  # Remove potential []
        variable_name = variable_name.replace("]", "")
        # For nargs=2, remove second entry
        if words[1] in words[2]:
            variable_help = filter(None, words[3:])  # Remove ''
        else:
            variable_help = filter(None, words[2:])  # Remove ''
        variable_help = ' '.join(variable_help)
        variable_help = re.sub('\n', '', variable_help)  # remove print_help
                                                         # format (induces \n)
        # Remove: (default..) without removing all '('
        variable_help = '('.join(variable_help.split('(')[:-1])[:-1]# Remove: (default..)
        arguments_info[variable_name] = [variable_key, variable_help]

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




