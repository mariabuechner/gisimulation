"""
X-ray source for grating interferometer simulation.

@author: buechner_m <maria.buechner@gmail.com>
"""
import numpy as np
from detector import pixel_coordinates
import logging
logger = logging.getLogger(__name__)


class Source():
    """
    X-ray source for grating interferometer simulation.

    Notes
    =====

    self.coordinates = [0.0, 0.0]

    self.rays:
        targets: [x, y]
        thetas: angles on x-z-plane
        phis: angles on y-z-plane

    """
    def __init__(self, parameters, geometry_results):
        """
        Parameters
        ==========

        parameters [dict]

        Notes
        =====

        focal_spot_size [um]:   if None or 0, infinite source size
                                (parallel beam) (NECESSARY??)


        """
        self.energies = parameters['spectrum']['energies']  # [keV]
        self.photons = parameters['spectrum']['energies']  # [conts/pixel]

#        NECESSARY???
#        if parameters['focal_spot_size'] is None or \
#                parameters['focal_spot_size'] == 0:
#            self.type = 'infinite'
#        else:
#            self.type = 'finite'
#            self.focal_spot_size = parameters['focal_spot_size']
#        logger.debug("Source type is: {0}".format(self.type))

        self.rays = dict()
        self.rays['targets'] = pixel_coordinates(parameters['field_of_view'],
                                                 parameters['pixel_size'])
        # theta = atan(x/z)
        self.rays['thetas'] = np.arctan(self.rays['targets'][:, :, 0] /
                                        geometry_results
                                        ['distance_source_detector'])
        # phi = atan(y/z)
        self.rays['phis'] = np.arctan(self.rays['targets'][:, :, 1] /
                                      geometry_results
                                      ['distance_source_detector'])
