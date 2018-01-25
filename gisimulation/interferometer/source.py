"""
X-ray source for grating interferometer simulation.

@author: buechner_m <maria.buechner@gmail.com>
"""
import numpy as np
import materials
import logging
logger = logging.getLogger(__name__)


class Source():
    """
    X-ray source for grating interferometer simulation.

    Parameters
    ==========

    spectrum [keV]
    focal_spot_size [um]:   if None or 0, infinite source size (parallel beam)

    """
    def __init__(self, spectrum, focal_spot_size,
                 material_filter, thickness_filter,
                 look_up_table, photo_only):
        """
        """
        self.spectrum = np.array(spectrum)
        if focal_spot_size is None or focal_spot_size == 0:
            self.type = 'infinite'
        else:
            self.type = 'finite'
            self.focal_spot_size = focal_spot_size
        logger.debug("Source type is: {0}".format(self.type))

        if material_filter:
            self.spectrum = self.spectrum * \
                materials.height_to_transmission(thickness_filter,
                                                 material_filter,
                                                 self.spectrum,
                                                 photo_only=photo_only,
                                                 source=look_up_table)
        logger.debug("Spectrum is:\n{0}".format(self.spectrum))
