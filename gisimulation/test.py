"""
Created on Fri Oct 20 09:59:26 2017

@author: buechner_m
"""
import numpy as np
import os
import csv

if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    print("script dir is: {}".format(script_dir))

    rel_path = 'data/spectra/Comet120kV.csv'

    file_path = os.path.join(script_dir, rel_path)

    print("file path is: {}".format(file_path))

#    csv_file = open(file_path)
#    spectrum = csv.reader(csv_file)
#
#    energies = np.array(0, dtype=float)
#    photons = np.array(0, dtype=float)
#
#    for line in spectrum:
#        print("{0}\t{1}".format(line[0], line[1]))
#        print(type(line[0]))
#        np.append(energies, line[0].astype())
#        np.append(photons, line[1])

    # Read file to numpy array. Skip header (first line).
#    spectrum = np.genfromtxt(file_path, delimiter=',', skip_header=1)
    spectrum = np.genfromtxt(file_path, delimiter=',', names=True)

