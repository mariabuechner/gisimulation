"""
Module to calculate the grating interferometer geometry

ToDo:
    include check for correct results (p0>p2 etc., incase of invalid input
    values.

@author: buechner_m <maria.buechner@gmail.com>
"""
import materials
import logging
logger = logging.getLogger(__name__)


class Geometry():
    """
    """
    def __init__(self, beam_geometry, gi_geometry):
        """
        """





# %%


class GeometryOld():
    """

    just for cone beam and with G0... ???

    """
    def __init__(self, design_energy, talbot_order, geometry_type,
                 smallest_pitch, pi_half_shift=False, fixed_distance=0):
        """

        fixed_distance needed for inverse and conventional

        Init:

            self.p2 [um]
            self.p0 [um]
            self.p1 [um]

            self.tablot_distance  # [mm]

            self.gi_length # [mm]
            self.g0g1 # [mm]
            self.g1g2 # [mm]

        """
        self.design_energy = design_energy  # [keV]
        self.design_wavelength = materials.energy_to_wavelength(
                                                    self.design_energy)  # [um]
        self.talbot_order = talbot_order
        self.geometry_type = geometry_type
        self.pi_half_shift = pi_half_shift

        # Phase shift factor
        if self.pi_half_shift:
            self._phase_factor = 1
        else:
            self._phase_factor = 2

        if self.geometry_type is "inverse":
            self.calc_inverse(smallest_pitch, fixed_distance)
        elif self.geometry_type is "symmetric":
            self.calc_symmetric(smallest_pitch)
        elif self.geometry_type is "conventional":
            # raise Warning("Conventional case not defined yet...")
            self.calc_conventional(smallest_pitch, fixed_distance)
        else:
            raise ValueError("'{0}' is not a valid geometry type. Please use"
                             "'inverse', 'symmetric' or 'conventional'.")

    def calc_symmetric(self, smallest_pitch):
        """
        g2 = smalles pitch (=p0)
        no fixed distance
        """
        # Calc pitches
        self.p2 = smallest_pitch  # [um]
        self.p0 = self.p2  # [um]
        self.p1 = self._phase_factor*self.p2/2  # [um]
        # Calc talbot distance
        self.talbot_distance = 2*self.talbot_order * self.p1**2 / \
            (self._phase_factor**2 * 2*self.design_wavelength)  # [um]
        self.talbot_distance = self.talbot_distance * 1e-3  # [mm]
        # Calc distances
        self.gi_length = 2*self.talbot_distance  # [mm]
        self.g0g1 = self.gi_length/2  # [mm]
        self.g1g2 = self.g0g1  # [mm]

    def calc_inverse(self, smallest_pitch, fixed_distance):
        """
        p0 = smalles pitch
        g0g1 = fixed distance
        """
        self.p0 = smallest_pitch  # [um]
        self.g0g1 = fixed_distance  # [mm]
        # Calc talbot distance based on G0G1Distance and p0
        # according to: d_n = l^2/(n/2lambda * p0^2 - l)
        self.talbot_distance = (self.g0g1**2) / \
            ((self.talbot_order*(self.p0*1e-3)**2)/(2*(
             self.design_wavelength*1e-3)) - self.g0g1)  # [mm]
        # Calc remaining distances
        self.g1g2 = self.talbot_distance  # [mm]
        self.gi_length = self.g0g1 + self.g1g2  # [mm]
        # Calc remaining pitches
        self.p2 = self.p0*self.g1g2/self.g0g1  # p0 * d_n/l [um]
        self.p1 = self._phase_factor * self.p2 * \
            self.g0g1/(self.gi_length)  # ny*p2*l/(l+d_n) [um]

#    def calc_conventional(self, smallest_pitch, fixed_distance):
#        """
#        p2 = smalles pitch
#        g0g1 = fixed distance
#
#        """
#        self.p2 = smallest_pitch  # [um]
#        self.g0g1 = fixed_distance  # [mm]
#        # Calc talbot distance based on G0G1Distance and p0
#        # according to: d_n = -g0g1/2 + sqrt(n*p2^2/2*lambda + l^2/4)
#        self.talbot_distance = (-self.g0g1/2) + \
#            ((self.talbot_order*(self.p2*1e-3)**2)/(2*(
#              self.design_wavelength*1e-3)) + (self.g0g1**2)/4)**0.5  # [mm]
#        # Calc remaining distances
#        self.g1g2 = self.talbot_distance  # [mm]
#        self.gi_length = self.g0g1 + self.g1g2  # [mm]
#        # Calc remaining pitches
#        self.p0 = self.p2*self.g0g1/self.g1g2  # [um]
#        self.p1 = self.p2*self._phase_factor*self.g0g1/(self.g0g1 + self.g1g2)

    def calc_conventional(self, smallest_pitch, fixed_distance):
        """
        from caros matlab code...

        """
        self.p2 = smallest_pitch  # [um]
        self.g0g1 = fixed_distance  # [mm]
        # Calc talbot distance based on G0G1Distance and p0
        # according to:
        factor = self.design_wavelength*self.g0g1/(self.talbot_order*self.p2)
        self.p0 = factor + (factor**2 +
                            2*self.design_wavelength*self.g0g1 /
                            self.talbot_order)**0.5  # [um]
        # Calc remaining distances
        self.g1g2 = self.g0g1*self.p2/self.p0  # [mm]
        self.gi_length = self.g0g1 + self.g1g2  # [mm]
        # Calc remaining pitches
        self.p1 = self._phase_factor * \
            (2*self.design_wavelength*self.g1g2 /
             (self.talbot_order*self.gi_length/self.g0g1))**0.5  # [um]
        # SEEMS WRONG....

    def list_parameters(self, source_to_g0=100, g1_to_sample=10,
                        sample_diameter=200):
        """
        not yet for conventional...

        returns total system length and g2 to detector distance

        """
        if not hasattr(self, 'source_to_g0'):
            self.source_to_g0 = source_to_g0
            self.g1_to_sample = g1_to_sample
            self.sample_diameter = sample_diameter
            self.isocenter = self.source_to_g0 + self.g0g1 + \
                self.g1_to_sample + self.sample_diameter/2  # [mm]
            self.system_length = 2*self.isocenter  # [mm]
            self.g2_to_detector = self.system_length - self.gi_length - \
                self.source_to_g0  # [mm]
        # Display
        print("For the GI setup:\n")
        self.list_gi_parameters()
        print("and the\nSource to G0 distance\t= {0}\nG1 to sample "
              "distance\t= {1}\nsample diameter\t= {2}".format(
                self.source_to_g0, self.g1_to_sample, self.sample_diameter))
        print("with the sample in the isocenter:\n")
        print("Total length from source to detector\t= {0}\nG2 to detector "
              "distance\t= {1}".format(self.system_length,
                                       self.g2_to_detector))

    def list_gi_parameters(self):
        """
        """
        print("Pitches in [um]:\np0\t= {0}\np1\t= {1}\np2\t= {2}".format(
                                                    self.p0, self.p1, self.p2))
        print("Distances in [mm]:\ng0g1\t= {0}\ng1g2\t= {1}\ng0g2\t= {2}".
              format(self.g0g1, self.g1g2, self.gi_length))
