class Grating():
    """
    Parent class for gratings.

    Parameters
    ==========

    pitch: grating pitch in [um], in x-direction
    height: grating height in [um], in z-direction
    material: grating material


    Returns
    =======


    Notes
    =====


    Examples
    ========

    """
    def __init__(self, pitch, height, material):
        self.pitch = pitch # [um]
        self.height = height # [um]
        self.material = material
