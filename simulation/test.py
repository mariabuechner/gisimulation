"""
Test script

Created on Fri Oct 06 14:37:55 2017

@author: buechner_m <maria.buechner@gmail.com>
"""
import argparse
import sys

#  Parse input arguments
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
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-v', '--verbose', action='count',
                    help='Increase verbosity level. "v": error, '
                    '"vv": warning, "vvv": info (default), "vvvv": debug')

parser.add_argument('-sr', dest='sampling_rate', default=0,
                    help='sampling voxel size (cube). '
                    'Default is 0, then pixel_size * 1e1-3.')

parser.add_argument('-gi', dest='geometry', default='sym',
                    type=str,
                    choices=['sym', 'trad', 'inv'],
                    help='GI geometry. Default is "sym", choices are\n'
                    '"sym": symmetrical, "trad": traditional, "inv": inverse.')

args = parser.parse_args()

try:
    # Check input
    if args.sampling_rate == 0:
        # Default to pixel_size *1e-3
        args.sampling_rate = args.pixel_size * 1e-3
except AttributeError as e:
    sys.stderr.write("Input arguments missing: {}".format(
                     e.message.split()[-1]))
