"""
Test script

Created on Fri Oct 06 14:37:55 2017

@author: buechner_m <maria.buechner@gmail.com>
"""
#import argparse
#import sys
#
#
##  Parse input arguments
#parser = argparse.ArgumentParser(description='Collect GI and simulation '
#                                 'parameters.',
#                                 fromfile_prefix_chars='@',
#                                 formatter_class=argparse.RawTextHelpFormatter)
#
#parser.add_argument('-v', '--verbose', action='count',
#                    help='Increase verbosity level. "v": error, '
#                    '"vv": warning, "vvv": info (default), "vvvv": debug')
#
#sr = parser.add_argument('-sr', dest='sampling_rate',
#                         help='sampling voxel size (cube). '
#                         'Default is 0, then pixel_size * 1e1-3.')
#
#parser.add_argument('-gi', dest='geometry', default='sym',
#                    type=str,
#                    choices=['sym', 'trad', 'inv'],
#                    help='GI geometry. Default is "sym", choices are\n'
#                    '"sym": symmetrical, "trad": traditional, "inv": inverse.')
#
#args = parser.parse_args()  # returns namespace
#all_parameter = vars(args)  # namespace to dict
## Keep verbosity level and all non-None input parameters
#parameter = dict([key, value] for [key, value] in all_parameter.items()
#                 if value is not None or key == 'verbose')
#
#
#class Struct:
#    def __init__(self, **entries):
#        self.__dict__.update(entries)
#
#parameters = Struct(**parameter)
#
#
#try:
#    # Check input
#    if args.sampling_rate == 0:
#        # Default to pixel_size *1e-3
#        args.sampling_rate = args.pixel_size * 1e-3
#except AttributeError as e:
#    sys.stderr.write("Input arguments missing: {}".format(
#                     str(e).split()[-1]))
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestClass():
    a = 3.0
    logger.info("Type of 'a' is: {}".format(type(a)))

    def print_a(self):
        logger.info("Printing a...")
        print(self.a)
        logger.info("... done.")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                        '%(message)s')
    logger.info("Creating b.")
#    b = TestClass()
#    logger.info("Calling b.print_a()")
#    b.print_a()
