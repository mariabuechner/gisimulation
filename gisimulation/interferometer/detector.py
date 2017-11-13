"""
X-ray detector for grating interferometer simulation.

@author: buechner_m <maria.buechner@gmail.com>
"""
import materials
from scipy.ndimage.filters import gaussian_filter
import logging
logger = logging.getLogger(__name__)


class Detector():
    """
    """
    def __init__(self, detector_type, point_spread_function, pixel_size,
                 field_of_view, detector_threshold,
                 material_detector, thickness_detector,
                 spectrum, look_up_table, photo_only,
                 sampling_rate):
        """
        """
        self.type = detector_type
        if self.type == 'conv':
            self.point_spread_function = point_spread_function
        self.pixel_size = pixel_size
        self.field_of_view = field_of_view
        self.detector_threshold = detector_threshold

        self.sampling_rate = sampling_rate

        if material_detector:
            # Calculate detector efficiency
            self.efficiency = \
                materials.height_to_absorption(thickness_detector,
                                               material_detector,
                                               spectrum,
                                               photo_only=photo_only,
                                               source=look_up_table)
        else:
            self.efficiency = 1
        logger.debug("Detector efficiency is: {0}%"
                     .format(self.efficiency*100))

    def detect(self, image):
        """

        Parameters
        ##########

        image [x, y, energies]

        Notes
        #####

        image * self.efficiency with self.efficiency [energies]
        multiplies each energy 2D matrix in image with the corresponding
        efficiency

        """
        # Account for detector efficiency
        image = image * self.efficiency

        # Account for PFS
        if self.type == 'conv':
            # PSF relative to pixel size
            pixel_blurring = self.point_spread_function / self.pixel_size
            # w = 2*int(truncate*sigma + 0.5) + 1 )from gaussian_filter1d():
            # pixel_blurring = 2*int(4*sigma + 0.5) + 1
            sigma = (pixel_blurring-2)/8
            image = gaussian_filter(image, sigma)

        return image


if __name__ == '__main__':
    import numpy as np
    detector = Detector('conv', 80., 50., np.array([20,20]), 25, None, None, np.array([20, 25, 30, 35, 40]), 'nist', False)

    image = np.random.rand(20, 20)

    res_img = detector.detect(image)

    import matplotlib.pyplot as plt

    f = plt.figure(1)
    plt.imshow(image)
    f.show()

    f = plt.figure(2)
    plt.imshow(res_img)
    f.show()













