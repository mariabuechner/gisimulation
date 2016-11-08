import materials
import logging
logger = logging.getLogger(__name__)



class Grating():
    """
    Parent class for gratings.

    Parameters
    ==========

    pitch: grating pitch in [um], in x-direction
    material: grating material
    design_energy: x-ray energy [keV]
    duty_cycle: default=0.5

    Examples
    ========


    """
    def __init__(self, pitch, material, design_energy, duty_cycle=0.5):
        self.pitch = pitch # [um]
        self.material = material
        self.design_energy = design_energy # [keV]
        self.duty_cycle = duty_cycle


class PhaseGrating(Grating):
    """
    Child class from Grating class, adds phase properties.

    Parameters
    ==========

    height: grating height in [um], in z-direction; default=0 (no height
    specified)
    phase_shift: required phase shift at given design energy; default=0 (no
    shift specified)


    Notes
    =====

    Either a grating height or a required phase shift needs to be defined, the
    other is calculated accordingly.

    Examples
    ========

    """
    def __init__(self, height=0, phase_shift=0):
        if height:
            self.height = height # [um]
            self.phase_shift = materials.height_to_shift(height, self.material,
                self.design_energy)
        elif phase_shift:
            self.height = materials.shift_to_height(phase_shift, self.material,
                self.design_energy) # [um]
            self.phase_shift = phase_shift
        else:
            raise Exception('Neither height of grating nor phase shift are '
                'given.')


class AbsorptionGrating(Grating):
    """
    Child class from Grating class, adds absorption properties.

    Parameters
    ==========

    height: grating height in [um], in z-direction; default=0 (no height
    specified)
    absorption: required percentage of absorbed x-rays at design energy;
    default=0 (no absorption specified)

    Notes
    =====

    Either a grating height or a required absorption needs to be defined, the
    other is calculated accordingly.


    Examples
    ========

    """
    def __init__(self, height=0, absorption=0):
        if height:
            self.height = height # [um]
            self.absorption = materials.height_to_absorption(height, self.material,
                self.design_energy) # [%]
        elif absorption:
            self.height = materials.absorption_to_height(absorption,
                self.material, self.design_energy) # [um]
            self.absorption = absorption # [%]
        else:
            raise Exception('Neither height of grating nor absorption are '
                'given.')
