"""
Created on Fri Oct 20 09:59:26 2017

@author: buechner_m
"""
import os
import numpy as np
import argparse



parser = argparse.ArgumentParser()

parser.add_argument('-t', dest='talbot_order',
                    type=int,
                    help="Talbot order.")

parser.add_argument('--dual_phase',
                    action='store_true',
                    help="Option for dual phase setup (True or False). "
                    "Only valid for conventional setup (geometry='conv') "
                    "and without G0.")
if __name__ == '__main__':
    args = parser.parse_args()
    print(args.dual_phase)
