"""
Created on Fri Oct 20 09:59:26 2017

@author: buechner_m
"""
import os
import numpy as np
import argparse


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

parser = argparse.ArgumentParser()

parser.add_argument('-spec', dest='spectrum_file',
                    action=_CheckFile,
                    nargs='?', type=str,
                    help="Location of spectrum file (.csv).\n"
                    "Full path or relative path ('.|relative_path') "
                    "from calling script.")
if __name__ == '__main__':
    args = parser.parse_args()
    print(args.spectrum_file)
