"""

@author: buechner_m <maria.buechner@gmail.com>
"""
import materials
import logging
logger = logging.getLogger(__name__)


class Grating(object):
    """
    Parent class for gratings.

    Parameters
    ==========

    pitch: grating pitch in [um], in x-direction
    material: grating material
    design_energy: x-ray energy [keV]
    height: grating height in [um], in z-direction; default=0 (no height
    specified)
    duty_cycle: default=0.5
    shape: shape of grating, choices = ['flat','circular'], default='flat'

    Examples
    ========


    """
    def __init__(self, pitch, material, design_energy, height=0,
                 duty_cycle=0.5, shape='flat'):
        self.pitch = pitch  # [um]
        self.material = material
        self.design_energy = design_energy  # [keV]
        self.height = height  # [um]
        self.duty_cycle = duty_cycle
        self.shape = shape


class PhaseGrating(Grating):
    """
    Child class from Grating class, adds phase properties.

    Parameters
    ==========

    phase_shift: required phase shift at given design energy; default=0 (no
    shift specified)


    Notes
    =====

    Either a grating height or a required phase shift needs to be defined, the
    other is calculated accordingly.

    Examples
    ========

    """
    def __init__(self, pitch, material, design_energy, height=0,
                 duty_cycle=0.5, shape='flat', phase_shift=0):
        # call init from parent class
        super(PhaseGrating, self).__init__(pitch, material, design_energy,
                                           height, duty_cycle, shape)
        # Calculate height or phase shift respectively
        if self.height:
            self.phase_shift = materials.height_to_shift(self.height,
                                                         self.material,
                                                         self.design_energy)
        elif phase_shift:
            self.height = materials.shift_to_height(phase_shift, self.material,
                                                    self.design_energy)  # [um]
            self.phase_shift = phase_shift
        else:
            raise Exception('Neither height of grating nor phase shift are '
                            'defined.')


class AbsorptionGrating(Grating):
    """
    Child class from Grating class, adds absorption properties.

    Parameters
    ==========

    absorption: required percentage of absorbed x-rays at design energy;
    default=0 (no absorption specified)

    Notes
    =====

    Either a grating height or a required absorption needs to be defined, the
    other is calculated accordingly.


    Examples
    ========

    """
    def __init__(self, pitch, material, design_energy, height=0,
                 duty_cycle=0.5, shape='flat', absorption=0):
        # call init from parent class
        super(AbsorptionGrating, self).__init__(pitch, material,
                                                design_energy, height,
                                                duty_cycle, shape)
        # Calculate height or absorption respectively
        if self.height:
            self.absorption = materials.height_to_absorption(self.height,
                                                             self.material,
                                                             self.
                                                             design_energy)
            # [%]
        elif absorption:
            self.height = materials.absorption_to_height(absorption,
                                                         self.material,
                                                         self.
                                                         design_energy)  # [um]
            self.absorption = absorption  # [%]
        else:
            raise Exception('Neither height of grating nor absorption are '
                            'defined.')
