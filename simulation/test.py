"""
Test script

Created on Fri Oct 06 14:37:55 2017

@author: buechner_m
"""
import argparse

#  Parse input arguments
parser = argparse.ArgumentParser(description='Collect GI and simulation '
                                 'parameters.')
parser.add_argument('--verbose', '-v', action='count',
                    help='Increase verbosity level. "v": error, '
                    '"vv": warning, "vvv": info (default), "vvvv": debug')

parser.add_argument('input_file', nargs='?', type=argparse.FileType('r'),
                    default='test.py',
                    help='Location of input file containing all (necessary) '
                    'parameters. Default is "test.py", '
                    'parse via command line.')

parser.add_argument('sampling_size',
                    help='sampling vocel size (cube). '
                    'Default is 0, then pixel_size * 1e1-3.')

# NOT WORKING CORRELTY YET...
#subparsers = parser.add_subparsers(title='subcommands',
#                                   description='valid subcommands',
#                                   help='sub-command help')
#
#general_parser = subparsers.add_parser('inputfile', help='inputfile help')
#general_parser.add_argument('input_file',  # nargs='?',
#                            # type=argparse.FileType('r'),
#                            help='Location of input file containing all '
#                            '(necessary) .parameters.')
#
#general_parser.add_argument('sampling_size', default=0,
#                            help='sampling vocel size (cube). '
#                            'Default is 0, then pixel_size * 1e1-3.')
#general_parser.add_argument('m1',
#                            help='G1 grating line material.')
#
#ct_parser = subparsers.add_parser('ct', help='ct help')
#ct_parser.add_argument('number_scans', type=int)


try:
    args = parser.parse_args()
except argparse.ArgumentError:
    if args.input_file is 'test.py':
        pass
