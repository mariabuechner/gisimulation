"""
Module to calculate the grating interferometer geometry

ToDo:
    include check for correct results (p0>p2 etc., incase of invalid input
    values.

@author: buechner_m <maria.buechner@gmail.com>
"""
import numpy as np
import logging
logger = logging.getLogger(__name__)


class GeometryError(Exception):
    """
    GeometryError, parent 'Exception'
    """
    pass


class Geometry():
    """
    Class to calculate and set all missing geometry and GI parameters.
    """
    def __init__(self, parameters):
        """
        Calculates the geometries and missing GI parameters.

        ALSO: Check sample position!!! (GeometryError)

        Parameters
        ##########

        parameters [dict]

        """
        self._parameters = parameters
        # nu = 2 if pi shift, nu = 1 if pi-half shift
        self._nu = round(self._parameters['phase_shift_g1'] * 2/np.pi)
        logger.debug("self._nu: {}".format(self._nu))

        # Calculate geometries
        if self._parameters['gi_geometry'] == 'conv':
            self._calc_conventional()
        elif self._parameters['gi_geometry'] == 'sym':
            self._calc_symmetrical()
        elif self._parameters['gi_geometry'] == 'inv':
            self._calc_inverse()

        # Update geometry results
        self.results = self._get_geometry_results()

    # Set geometry results
    def _get_geometry_results(self):
        """
        Update self._parameters['results']['geometry'] and return geometry
        results dict.

        Results contain:
            - component_list
            - gi_geometry
            - beam_geometry
            - distances (not none)
            - pitches (not none)
            - if sample:
                - sample_position
                - sample_distance

        Returns
        #######

        self._parameters['results']['geometry'] [dict]

        """
        # To 'Setup'
        self._parameters['results']['geometry']['Setup'] = dict()
        # Add component list
        self._parameters['results']['geometry']['Setup']['component_list'] = \
            self._parameters['component_list']

        # Add geometries
        self._parameters['results']['geometry']['Setup']['gi_geometry'] = \
            self._parameters['gi_geometry']
        self._parameters['results']['geometry']['Setup']['beam_geometry'] = \
            self._parameters['beam_geometry']

        # To 'distances'
        self._parameters['results']['geometry']['distances'] = dict()
        # Add distances
        # distances =  [('distance_b', 10), ('distance_a', 10)]
        distances = [(distance_name, distance_value)
                     for distance_name, distance_value
                     in self._parameters.iteritems()
                     if ('distance_' in distance_name and
                         distance_value is not None)]
        for distance in distances:
            self._parameters['results']['geometry']['distances'][distance[0]] \
                = distance[1]

        # To 'pitches'
        self._parameters['results']['geometry']['pitches'] = dict()
        # Add pitches
        pitches = [(pitch_name, pitch_value) for pitch_name, pitch_value
                   in self._parameters.iteritems()
                   if ('pitch_' in pitch_name and pitch_value is not None)]
        for pitch in pitches:
            self._parameters['results']['geometry']['pitches'][pitch[0]] = \
                pitch[1]

        # To 'sample'
        self._parameters['results']['geometry']['sample'] = dict()
        # Add sample info
        if self._parameters['sample_position']:
            (self._parameters['results']['geometry']['sample']
             ['sample_position']) = self._parameters['sample_position']
            (self._parameters['results']['geometry']['sample']
             ['sample_distance']) = self._parameters['sample_distance']
             # FUTURE
             # Add shape and size

        return self._parameters['results']['geometry']

    def update_parameters(self):
        """
        Return updated parameter dict.

        Returns
        #######

        parameters [dict]

        """
        return self._parameters

    # Calculate gi geometries

    # ALSO: GeometryError if negative distances!!!

    def _calc_conventional(self):
        """
        For cone and parallel.

        Notes
        #####

        For parallel:

            Fractional talbot distance Dn:
                Dn = n * p1^2/(nu^2 * 2 * lambda), n: talbot_order

            Pitches:
                p1 = p2 * nu
                p2 = p1 / nu


        For cone:

            Magnification M:
                M = (l + dn) / l
                s = l + dn

            Fractional talbot distance Dn:
                Dn = n * p1^2/(nu^2 * 2 * lambda), n: talbot_order

            G1 to G2:
                dn = M * Dn
                dn = l * Dn / (l - Dn)

            Source/G0 to G1:
                l = s - dn
                l = s/2 + sqrt((s^2)/4 - s * Dn)

            Source/G0 to G2:
                s = l + dn

            Pitches:

                p1 = nu * p2 / M
                p2 = M * p1 / nu
                p0 = p2 * l / dn

        """

        if self._parameters['beam_geometry'] == 'parallel':
            # Parallel beam
            if not self._parameters['dual_phase']:
                # Standard GI
                if self._parameters['fixed_grating'] == 'g1':
                    # Talbot distance
                    self._parameters['distance_g1_g2'] = \
                        self._parameters['talbot_order'] * \
                        (np.square(self._parameters['pitch_g1'] / self._nu) /
                         (2 * self._parameters['design_wavelength']))  # [um]
                    self._parameters['distance_g1_g2'] = \
                        self._parameters['distance_g1_g2'] * 1e-3  # [mm]
                    # Pitches
                    self._parameters['pitch_g2'] = \
                        self._parameters['pitch_g1'] / self._nu
                    # Duty cycles
                    self._parameters['duty_cycle_g2'] = \
                        self._parameters['duty_cycle_g1']
                else:
                    # Pitches
                    self._parameters['pitch_g1'] = \
                        self._parameters['pitch_g2'] * self._nu
                    # Duty cycles
                    self._parameters['duty_cycle_g1'] = \
                        self._parameters['duty_cycle_g2']
                    # Talbot distance
                    self._parameters['distance_g1_g2'] = \
                        self._parameters['talbot_order'] * \
                        (np.square(self._parameters['pitch_g1'] / self._nu) /
                         (2 * self._parameters['design_wavelength']))  # [um]
                    self._parameters['distance_g1_g2'] = \
                        self._parameters['distance_g1_g2'] * 1e-3  # [mm]
            else:
                # Dual phase setup (HERE OR INSIDE CALCS???)
                logger.warn("Parallel, conv and dual phase not possible yet!")

        else:
            # Cone beam
            if not self._parameters['dual_phase']:
                # Standard GI
                if self._parameters['fixed_grating'] == 'g1':
                    # G1 fixed

                    # Talbot distance
                    talbot_distance = self._parameters['talbot_order'] * \
                        (np.square(self._parameters['pitch_g1'] / self._nu) /
                         (2 * self._parameters['design_wavelength']))  # [mm]
                    talbot_distance = talbot_distance * 1e-3  # [mm]

                    # Other distances
                    if self._parameters['fixed_distance'] == \
                            'distance_source_g1' or \
                            self._parameters['fixed_distance'] == \
                            'distance_g0_g1':
                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = self._parameters[self._parameters
                                                 ['fixed_distance']]
                        # G1 to G2
                        self._parameters['distance_g1_g2'] = \
                            to_g1 * talbot_distance / \
                            (to_g1 - talbot_distance)
                        if self._parameters['distance_g1_g2'] <= 0:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1."
                                             .format(self._parameters
                                                     ['fixed_distance']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        # Source/G0 to G2
                        total_length = to_g1 + \
                            self._parameters['distance_g1_g2']
                        if 'G0' in self._parameters['component_list']:
                            self._parameters['distance_g0_g2'] = total_length
                        else:
                            self._parameters['distance_source_g2'] = \
                                total_length

                    elif self._parameters['fixed_distance'] == \
                            'distance_source_g2' or \
                            self._parameters['fixed_distance'] == \
                            'distance_g0_g2':
                        # Distance from Source/G0 to g2 fixed (s)
                        total_length = self._parameters[self._parameters
                                                        ['fixed_distance']]

                        # Source/G0 to G1
                        if total_length <= 4.0 * talbot_distance:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1."
                                             .format(self._parameters
                                                     ['fixed_distance']))
                            logger.error(error_message)
                            raise GeometryError(error_message)
                        to_g1 = total_length/2.0 + np.sqrt(total_length**2.0 /
                                                           4.0 - total_length *
                                                           talbot_distance)

                        if 'G0' in self._parameters['component_list']:
                            self._parameters['distance_g0_g1'] = to_g1
                        else:
                            self._parameters['distance_source_g1'] = to_g1

                        # G1 to G2
                        self._parameters['distance_g1_g2'] = \
                            to_g1 * talbot_distance / \
                            (to_g1 - talbot_distance)

                    # Magnification (s/l)
                    M = total_length / to_g1

                    # Pitches
                    self._parameters['pitch_g2'] = \
                        M * self._parameters['pitch_g1'] / self._nu
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['pitch_g0'] = \
                            (to_g1 / self._parameters['distance_g1_g2']) * \
                            self._parameters['pitch_g1']

                    # Duty cycles
                    self._parameters['duty_cycle_g2'] = \
                        self._parameters['duty_cycle_g1']
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['duty_cycle_g0'] = \
                            self._parameters['duty_cycle_g1']

                elif self._parameters['fixed_grating'] == 'g2':
                    # G2 fixed
                    pass
                else:
                    # G0 fixed
                    pass
            else:
                # Dual phase setup (HERE OR INSIDE CALCS???)
                logger.warn("Cone, conv and dual phase not possible yet!")

    def _calc_symmetrical(self):
        """
        For cone

        Notes
        #####

        Magnification M:
            M = (l + dn) / l = 2
            s = l + dn with l = dn

        Fractional talbot distance Dn:
            Dn = n * p1^2/(nu^2 * 2 * lambda), n: talbot_order

        G1 to G2:
            dn = M * Dn = 2 * Dn

        Source/G0 to G1:
            l = dn

        Source/G0 to G2:
            s = 2 * l = 2* dn = l + dn

        Pitches:

            p1 = nu * p2 / 2
            p2 = 2 * p1 / nu
            p0 = p2

        """
        # Standard GI
        if self._parameters['fixed_grating'] == 'g1':
            # G1 fixed

            # Pitches
            self._parameters['pitch_g2'] = \
                2.0 * self._parameters['pitch_g1'] / self._nu
            if 'G0' in self._parameters['component_list']:
                self._parameters['pitch_g0'] = \
                    self._parameters['pitch_g2']

            # Duty cycles
            self._parameters['duty_cycle_g2'] = \
                self._parameters['duty_cycle_g1']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g1']

        elif self._parameters['fixed_grating'] == 'g2':
            # G2 fixed

            # Pitches
            self._parameters['pitch_g1'] = \
                self._nu * self._parameters['pitch_g2'] / 2.0
            if 'G0' in self._parameters['component_list']:
                self._parameters['pitch_g0'] = \
                    self._parameters['pitch_g2']

            # Duty cycles
            self._parameters['duty_cycle_g1'] = \
                self._parameters['duty_cycle_g2']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g2']
        else:
            # G0 fixed

            # Pitches
            self._parameters['pitch_g1'] = \
                self._nu * self._parameters['pitch_g0'] / 2.0
            self._parameters['pitch_g2'] = \
                self._parameters['pitch_g0']

            # Duty cycles
            self._parameters['duty_cycle_g1'] = \
                self._parameters['duty_cycle_g0']
            self._parameters['duty_cycle_g2'] = \
                self._parameters['duty_cycle_g0']

        # Distances (the same for all, based on p1)
        # G1 to G2
        talbot_distance = self._parameters['talbot_order'] * \
            (np.square(self._parameters['pitch_g1'] / self._nu) /
             (2.0 * self._parameters['design_wavelength']))
        self._parameters['distance_g1_g2'] = 2.0 * talbot_distance  # [um]
        self._parameters['distance_g1_g2'] = \
            self._parameters['distance_g1_g2'] * 1e-3  # [mm]
        # Source/G0 to G1 and Source/G0 to G2:
        if 'G0' in self._parameters['component_list']:
            self._parameters['distance_g0_g1'] = \
                self._parameters['distance_g1_g2']
            self._parameters['distance_g0_g2'] = \
                2 * self._parameters['distance_g1_g2']
        else:
            self._parameters['distance_source_g1'] = \
                self._parameters['distance_g1_g2']
            self._parameters['distance_source_g2'] = \
                2 * self._parameters['distance_g1_g2']

    def _calc_inverse(self):
        """
        For cone
        """
        # Cone beam
        # Standard GI
        if self._parameters['fixed_grating'] == 'g1':
            # G1 fixed

            # Talbot distance
            talbot_distance = self._parameters['talbot_order'] * \
                (np.square(self._parameters['pitch_g1'] / self._nu) /
                 (2 * self._parameters['design_wavelength']))  # [mm]
            talbot_distance = talbot_distance * 1e-3  # [mm]

            # Other distances
            if self._parameters['fixed_distance'] == \
                    'distance_source_g1' or \
                    self._parameters['fixed_distance'] == \
                    'distance_g0_g1':
                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = self._parameters[self._parameters
                                         ['fixed_distance']]
                # G1 to G2
                self._parameters['distance_g1_g2'] = \
                    to_g1 * talbot_distance / \
                    (to_g1 - talbot_distance)
                if self._parameters['distance_g1_g2'] <= 0:
                    error_message = ("{0} too small for chosen talbot "
                                     "order, energy and pitch of G1."
                                     .format(self._parameters
                                             ['fixed_distance']))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                # Source/G0 to G2
                total_length = to_g1 + \
                    self._parameters['distance_g1_g2']
                if 'G0' in self._parameters['component_list']:
                    self._parameters['distance_g0_g2'] = total_length
                else:
                    self._parameters['distance_source_g2'] = \
                        total_length

            elif self._parameters['fixed_distance'] == \
                    'distance_source_g2' or \
                    self._parameters['fixed_distance'] == \
                    'distance_g0_g2':
                # Distance from Source/G0 to g2 fixed (s)
                total_length = self._parameters[self._parameters
                                                ['fixed_distance']]

                # Source/G0 to G1
                if total_length <= 4.0 * talbot_distance:
                    error_message = ("{0} too small for chosen talbot "
                                     "order, energy and pitch of G1."
                                     .format(self._parameters
                                             ['fixed_distance']))
                    logger.error(error_message)
                    raise GeometryError(error_message)
                to_g1 = total_length/2.0 - np.sqrt(total_length**2.0 /
                                                   4.0 - total_length *
                                                   talbot_distance)

                if 'G0' in self._parameters['component_list']:
                    self._parameters['distance_g0_g1'] = to_g1
                else:
                    self._parameters['distance_source_g1'] = to_g1

                # G1 to G2
                self._parameters['distance_g1_g2'] = \
                    to_g1 * talbot_distance / \
                    (to_g1 - talbot_distance)

            # Magnification (s/l)
            M = total_length / to_g1

            # Pitches
            self._parameters['pitch_g2'] = \
                M * self._parameters['pitch_g1'] / self._nu
            if 'G0' in self._parameters['component_list']:
                self._parameters['pitch_g0'] = \
                    (to_g1 / self._parameters['distance_g1_g2']) * \
                    self._parameters['pitch_g1']

            # Duty cycles
            self._parameters['duty_cycle_g2'] = \
                self._parameters['duty_cycle_g1']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g1']

        elif self._parameters['fixed_grating'] == 'g2':
            # G2 fixed
            pass
        else:
            # G0 fixed
            pass

# %%
#
#
#class GeometryOld():
#    """
#
#    just for cone beam and with G0... ???
#
#    """
#    def __init__(self, design_energy, talbot_order, geometry_type,
#                 smallest_pitch, pi_half_shift=False, fixed_distance=0):
#        """
#
#        fixed_distance needed for inverse and conventional
#
#        Init:
#
#            self.p2 [um]
#            self.p0 [um]
#            self.p1 [um]
#
#            self.tablot_distance  # [mm]
#
#            self.gi_length # [mm]
#            self.g0g1 # [mm]
#            self.g1g2 # [mm]
#
#        """
#        self.design_energy = design_energy  # [keV]
#        self.design_wavelength = materials.energy_to_wavelength(
#                                                    self.design_energy)  # [um]
#        self.talbot_order = talbot_order
#        self.geometry_type = geometry_type
#        self.pi_half_shift = pi_half_shift
#
#        # Phase shift factor
#        if self.pi_half_shift:
#            self._phase_factor = 1
#        else:
#            self._phase_factor = 2
#
#        if self.geometry_type is "inverse":
#            self.calc_inverse(smallest_pitch, fixed_distance)
#        elif self.geometry_type is "symmetric":
#            self.calc_symmetric(smallest_pitch)
#        elif self.geometry_type is "conventional":
#            # raise Warning("Conventional case not defined yet...")
#            self.calc_conventional(smallest_pitch, fixed_distance)
#        else:
#            raise ValueError("'{0}' is not a valid geometry type. Please use"
#                             "'inverse', 'symmetric' or 'conventional'.")
#
#    def calc_symmetric(self, smallest_pitch):
#        """
#        g2 = smalles pitch (=p0)
#        no fixed distance
#        """
#        # Calc pitches
#        self.p2 = smallest_pitch  # [um]
#        self.p0 = self.p2  # [um]
#        self.p1 = self._phase_factor*self.p2/2  # [um]
#        # Calc talbot distance
#        self.talbot_distance = 2*self.talbot_order * self.p1**2 / \
#            (self._phase_factor**2 * 2*self.design_wavelength)  # [um]
#        self.talbot_distance = self.talbot_distance * 1e-3  # [mm]
#        # Calc distances
#        self.gi_length = 2*self.talbot_distance  # [mm]
#        self.g0g1 = self.gi_length/2  # [mm]
#        self.g1g2 = self.g0g1  # [mm]
#
#    def calc_inverse(self, smallest_pitch, fixed_distance):
#        """
#        p0 = smalles pitch
#        g0g1 = fixed distance
#        """
#        self.p0 = smallest_pitch  # [um]
#        self.g0g1 = fixed_distance  # [mm]
#        # Calc talbot distance based on G0G1Distance and p0
#        # according to: d_n = l^2/(n/2lambda * p0^2 - l)
#        self.talbot_distance = (self.g0g1**2) / \
#            ((self.talbot_order*(self.p0*1e-3)**2)/(2*(
#             self.design_wavelength*1e-3)) - self.g0g1)  # [mm]
#        # Calc remaining distances
#        self.g1g2 = self.talbot_distance  # [mm]
#        self.gi_length = self.g0g1 + self.g1g2  # [mm]
#        # Calc remaining pitches
#        self.p2 = self.p0*self.g1g2/self.g0g1  # p0 * d_n/l [um]
#        self.p1 = self._phase_factor * self.p2 * \
#            self.g0g1/(self.gi_length)  # ny*p2*l/(l+d_n) [um]
#
##    def calc_conventional(self, smallest_pitch, fixed_distance):
##        """
##        p2 = smalles pitch
##        g0g1 = fixed distance
##
##        """
##        self.p2 = smallest_pitch  # [um]
##        self.g0g1 = fixed_distance  # [mm]
##        # Calc talbot distance based on G0G1Distance and p0
##        # according to: d_n = -g0g1/2 + sqrt(n*p2^2/2*lambda + l^2/4)
##        self.talbot_distance = (-self.g0g1/2) + \
##            ((self.talbot_order*(self.p2*1e-3)**2)/(2*(
##              self.design_wavelength*1e-3)) + (self.g0g1**2)/4)**0.5  # [mm]
##        # Calc remaining distances
##        self.g1g2 = self.talbot_distance  # [mm]
##        self.gi_length = self.g0g1 + self.g1g2  # [mm]
##        # Calc remaining pitches
##        self.p0 = self.p2*self.g0g1/self.g1g2  # [um]
##        self.p1 = self.p2*self._phase_factor*self.g0g1/(self.g0g1 + self.g1g2)
#
#    def calc_conventional(self, smallest_pitch, fixed_distance):
#        """
#        from caros matlab code...
#
#        """
#        self.p2 = smallest_pitch  # [um]
#        self.g0g1 = fixed_distance  # [mm]
#        # Calc talbot distance based on G0G1Distance and p0
#        # according to:
#        factor = self.design_wavelength*self.g0g1/(self.talbot_order*self.p2)
#        self.p0 = factor + (factor**2 +
#                            2*self.design_wavelength*self.g0g1 /
#                            self.talbot_order)**0.5  # [um]
#        # Calc remaining distances
#        self.g1g2 = self.g0g1*self.p2/self.p0  # [mm]
#        self.gi_length = self.g0g1 + self.g1g2  # [mm]
#        # Calc remaining pitches
#        self.p1 = self._phase_factor * \
#            (2*self.design_wavelength*self.g1g2 /
#             (self.talbot_order*self.gi_length/self.g0g1))**0.5  # [um]
#        # SEEMS WRONG....
#
#    def list_parameters(self, source_to_g0=100, g1_to_sample=10,
#                        sample_diameter=200):
#        """
#        not yet for conventional...
#
#        returns total system length and g2 to detector distance
#
#        """
#        if not hasattr(self, 'source_to_g0'):
#            self.source_to_g0 = source_to_g0
#            self.g1_to_sample = g1_to_sample
#            self.sample_diameter = sample_diameter
#            self.isocenter = self.source_to_g0 + self.g0g1 + \
#                self.g1_to_sample + self.sample_diameter/2  # [mm]
#            self.system_length = 2*self.isocenter  # [mm]
#            self.g2_to_detector = self.system_length - self.gi_length - \
#                self.source_to_g0  # [mm]
#        # Display
#        print("For the GI setup:\n")
#        self.list_gi_parameters()
#        print("and the\nSource to G0 distance\t= {0}\nG1 to sample "
#              "distance\t= {1}\nsample diameter\t= {2}".format(
#                self.source_to_g0, self.g1_to_sample, self.sample_diameter))
#        print("with the sample in the isocenter:\n")
#        print("Total length from source to detector\t= {0}\nG2 to detector "
#              "distance\t= {1}".format(self.system_length,
#                                       self.g2_to_detector))
#
#    def list_gi_parameters(self):
#        """
#        """
#        print("Pitches in [um]:\np0\t= {0}\np1\t= {1}\np2\t= {2}".format(
#                                                    self.p0, self.p1, self.p2))
#        print("Distances in [mm]:\ng0g1\t= {0}\ng1g2\t= {1}\ng0g2\t= {2}".
#              format(self.g0g1, self.g1g2, self.gi_length))
