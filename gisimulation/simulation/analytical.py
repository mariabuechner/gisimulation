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


def spectrum_development(parameters, analytical_results,
                         analytical_components):
    """

    Parameters
    ==========

    parameters [dict]
    analytical_results [dict] (as ref)
    analytical_components [list] (of strings)

    """
    # Store original input spectrum
    analytical_results['energies'] = parameters['spectrum']['energies']
    analytical_results['input_photons'] = parameters['spectrum']['photons']
    analytical_results['input_photons_relative'] = \
        analytical_results['input_photons'] / \
        sum(analytical_results['input_photons'])

    for component in analytical_components:



def calculate_results(parameters, results, analytical_components):
    """
    ...


    """
    parameters = parameters.copy()
    geometry_results = results['geometry'].copy()

    # Spectrum development
    spectrum_development(parameters, results['analytical'],
                         analytical_components)

