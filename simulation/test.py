"""
Test script

Created on Fri Oct 06 14:37:55 2017

@author: buechner_m <maria.buechner@gmail.com>
"""
import argparse

#  Parse input arguments
parser = argparse.ArgumentParser(description='Collect GI and simulation '
                                 'parameters.',
                                 fromfile_prefix_chars='@',
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('--verbose', '-v', action='count',
                    help='Increase verbosity level. "v": error, '
                    '"vv": warning, "vvv": info (default), "vvvv": debug')

#parser.add_argument('-i', dest='input_file', type=open, action=LoadFromFile,
#                    help='Location of input file containing all (necessary) '
#                    'parameters.\n'
#                    'NOTE: input from input file can be overwritten in '
#                    'command line after.\n'
#                    'Layout:\n'
#                    'Line1: argument name (e.g. -sr)\n'
#                    'Line2: values        (e.g. 100)\n'
#                    'Example:\n'
#                    '-sr\n'
#                    '100\n'
#                    '-g0\n'
#                    'phase\n'
#                    '-d0\n'
#                    '33\n'
#                    '.\n'
#                    '.\n'
#                    '.')

parser.add_argument('-sr', dest='sampling_rate',
                    help='sampling voxel size (cube). '
                    'Default is 0, then pixel_size * 1e1-3.')

args = parser.parse_args()
