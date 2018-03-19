"""
Module to calculate analytical results.

Includes:
    - spectrum development
    - visibility break down
    - performance (radiography and CT)

@author: buechner_m <maria.buechner@gmail.com>
"""
import logging
import numpy as np
logger = logging.getLogger(__name__)

# %% Functions

# #############################################################################
# Calculations ################################################################


#def calculate_results(parameters, results):
#    """
#    ...
#
#
#    Returns
#    =======
#
#    analytical_results [dict]
#
#    """
#    parameters = parameters.copy()
#    geometry_results = results['geometry'].copy()
#    analytical_results = dict()
#
#    # Spectrum development
#
#    # Store original input spectrum
#    analytical_results['energies'] = parameters['spectrum']['energies']
#    analytical_results['input_photons'] = parameters['spectrum']['photons']
#    analytical_results['input_photons_relative'] = \
#        analytical_results['input_photons'] / \
#        sum(analytical_results['input_photons'])
