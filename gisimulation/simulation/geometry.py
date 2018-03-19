"""
Module to calculate the grating interferometer geometry

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

    Notes
    =====

    Changes self._parameters (copy of parameters) to update geometry and GI
    parameters. Returns self._parameters with .update_parameters().

    """
    def __init__(self, parameters):
        """
        Calculates the geometries and missing GI parameters.

        Parameters
        ==========

        parameters [dict]

        """
        self._parameters = parameters.copy()

        if self._parameters['gi_geometry'] != 'free':
            # nu = 2 if pi shift, nu = 1 if pi-half shift
            self._nu = round(self._parameters['phase_shift_g1'] * 2/np.pi)
            logger.debug("self._nu: {0}".format(self._nu))

        # Calculate geometries
        if self._parameters['gi_geometry'] == 'conv':
            self._calc_conventional()
        elif self._parameters['gi_geometry'] == 'sym':
            self._calc_symmetrical()
        elif self._parameters['gi_geometry'] == 'inv':
            self._calc_inverse()

        # Update source to component distances and grating radii if bent
        self._update_distances()

        if 'Sample' in self._parameters['component_list']:
            self._check_sample_position()

        # Update geometry results
        self._get_geometry_results()

    def update_parameters(self):
        """
        Return updated parameter dict.

        Returns
        =======

        parameters [dict]

        """
        return self._parameters

    def _calc_conventional(self):
        """
        For cone and parallel. Special case for dual phase (distances entered
        manually, just calculate pitch of G2 and fringe periode (pitch_fringe))

        Notes
        =====

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

            Conditions:

                l > dn
                s > s*dn

        """
        logger.info("Calculating conventional setup...")
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
            # Cone beam
            if not self._parameters['dual_phase']:
                if self._parameters['fixed_grating'] == 'g1':
                    # G1 fixed
                    # Talbot distance (Dn)
                    talbot_distance = self._parameters['talbot_order'] * \
                        (np.square(self._parameters['pitch_g1'] / self._nu) /
                         (2 * self._parameters['design_wavelength']))  # [um]
                    talbot_distance = talbot_distance * 1e-3  # [mm]

                    # Other distances
                    if self._parameters['fixed_distance'] == \
                            'distance_source_g1' or \
                            self._parameters['fixed_distance'] == \
                            'distance_g0_g1':
                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = self._parameters[self._parameters
                                                 ['fixed_distance']]  # [mm]

                        # G1 to G2 (dn)
                        self._parameters['distance_g1_g2'] = \
                            to_g1 * talbot_distance / \
                            (to_g1 - talbot_distance)

                        # Check if valid distance input
                        if self._parameters['distance_g1_g2'] <= 0:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     talbot_distance))
                            logger.error(error_message)
                            raise GeometryError(error_message)
                        elif self._parameters['distance_g1_g2'] >= to_g1:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     self._parameters
                                                     ['distance_g1_g2']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        # Source/G0 to G2 (s)
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
                        # Distance from Source/G0 to G2 fixed (s)
                        total_length = self._parameters[self._parameters
                                                        ['fixed_distance']]

                        # Source/G0 to G1 (l)
                        # Checks ultimately if s> 2*dn:
                        if total_length <= 4.0 * talbot_distance:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     4.0 * talbot_distance))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        to_g1 = total_length/2.0 + np.sqrt(total_length**2.0 /
                                                           4.0 - total_length *
                                                           talbot_distance)

                        if 'G0' in self._parameters['component_list']:
                            self._parameters['distance_g0_g1'] = to_g1
                        else:
                            self._parameters['distance_source_g1'] = to_g1

                        # G1 to G2 (dn)
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
                            self._parameters['pitch_g2']

                    # Duty cycles
                    self._parameters['duty_cycle_g2'] = \
                        self._parameters['duty_cycle_g1']
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['duty_cycle_g0'] = \
                            self._parameters['duty_cycle_g1']

                elif self._parameters['fixed_grating'] == 'g2':
                    # G2 fixed
                    if self._parameters['fixed_distance'] == \
                            'distance_source_g1' or \
                            self._parameters['fixed_distance'] == \
                            'distance_g0_g1':
                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = self._parameters[self._parameters
                                                 ['fixed_distance']]  # [mm]

                        # distance from G1 to G2 (dn)
                        # dn = -05*l + sqrt(0.25*l^2 + n/(2*lambda)*p2^2*l)
                        # lambda and p2 in um, need to be in mm
                        wavelength = self._parameters['design_wavelength'] * \
                            1e-3  # [mm]
                        p2 = self._parameters['pitch_g2'] * 1e-3  # [mm]

                        self._parameters['distance_g1_g2'] = -0.5 * to_g1 + \
                            np.sqrt(0.25 * to_g1**2 +
                                    self._parameters['talbot_order'] *
                                    p2**2 * to_g1 / (2 * wavelength))  # [mm]

                        # Check if l > dn:
                        if self._parameters['distance_g1_g2'] >= to_g1:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     self._parameters
                                                     ['distance_g1_g2']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        # Distance from Source/G0 to G2 fixed (s)
                        total_length = self._parameters['distance_g1_g2'] + \
                            to_g1  # [mm]

                        # Source/G0 to G2 (s)
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
                        # Distance from Source/G0 to G2 fixed (s)
                        total_length = self._parameters[self._parameters
                                                        ['fixed_distance']]

                        # distance from G1 to G2 (dn)
                        # dn = s / (s * 2 * lambda / (n * p2^2) + 1)
                        # lambda and p2 in um, need to be in mm
                        wavelength = self._parameters['design_wavelength'] * \
                            1e-3  # [mm]
                        p2 = self._parameters['pitch_g2'] * 1e-3  # [mm]

                        self._parameters['distance_g1_g2'] = total_length / \
                            (total_length * 2 * wavelength /
                             (self._parameters['talbot_order'] * p2**2) + 1)  # [mm]

                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = total_length - \
                            self._parameters['distance_g1_g2']  # [mm]

                        # Check if l > dn:
                        if self._parameters['distance_g1_g2'] >= to_g1:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     self._parameters
                                                     ['distance_g1_g2']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        if 'G0' in self._parameters['component_list']:
                            self._parameters['distance_g0_g1'] = to_g1
                        else:
                            self._parameters['distance_source_g1'] = to_g1

                    # Magnification (s/l)
                    M = total_length / to_g1

                    # Pitches [um]
                    self._parameters['pitch_g1'] = \
                        self._nu * self._parameters['pitch_g2'] / M
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['pitch_g0'] = \
                            (to_g1 / self._parameters['distance_g1_g2']) * \
                            self._parameters['pitch_g2']

                    # Duty cycles
                    self._parameters['duty_cycle_g1'] = \
                        self._parameters['duty_cycle_g2']
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['duty_cycle_g0'] = \
                            self._parameters['duty_cycle_g2']

                else:
                    # G0 fixed
                    if self._parameters['fixed_distance'] == \
                            'distance_source_g1' or \
                            self._parameters['fixed_distance'] == \
                            'distance_g0_g1':
                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = self._parameters[self._parameters
                                                 ['fixed_distance']]  # [mm]

                        # distance from G1 to G2 (dn)
                        # dn = l / (n * p0^2 / (2 * lambda * l) - 1)
                        # lambda and p2 in um, need to be in mm
                        wavelength = self._parameters['design_wavelength'] * \
                            1e-3  # [mm]
                        p0 = self._parameters['pitch_g0'] * 1e-3  # [mm]

                        self._parameters['distance_g1_g2'] = to_g1 / \
                            ((self._parameters['talbot_order'] * p0**2) /
                             (2 * wavelength * to_g1) - 1)  # [mm]

                        # Check if l > dn:
                        if self._parameters['distance_g1_g2'] >= to_g1:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     self._parameters
                                                     ['distance_g1_g2']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        # Distance from Source/G0 to G2 fixed (s)
                        total_length = self._parameters['distance_g1_g2'] + \
                            to_g1  # [mm]

                        # Source/G0 to G2 (s)
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
                        # Distance from Source/G0 to G2 fixed (s)
                        total_length = self._parameters[self._parameters
                                                        ['fixed_distance']]

                        # distance from G1 to G2 (dn)
                        # dn = s / (s * 2 * lambda / (n * p2^2) + 1)
                        # lambda and p2 in um, need to be in mm
                        wavelength = self._parameters['design_wavelength'] * \
                            1e-3  # [mm]
                        p0 = self._parameters['pitch_g0'] * 1e-3  # [mm]

                        self._parameters['distance_g1_g2'] = total_length / \
                            ((self._parameters['talbot_order'] * p0**2) /
                             (2 * wavelength * total_length) + 1)  # [mm]

                        # Distance from Source/G0 to G1 fixed (l)
                        to_g1 = total_length - \
                            self._parameters['distance_g1_g2']  # [mm]

                        # Check if l > dn:
                        if self._parameters['distance_g1_g2'] >= to_g1:
                            error_message = ("{0} too small for chosen talbot "
                                             "order, energy and pitch of G1. "
                                             "Must be larger than: {1} mm"
                                             .format(self._parameters
                                                     ['fixed_distance'],
                                                     self._parameters
                                                     ['distance_g1_g2']))
                            logger.error(error_message)
                            raise GeometryError(error_message)

                        if 'G0' in self._parameters['component_list']:
                            self._parameters['distance_g0_g1'] = to_g1
                        else:
                            self._parameters['distance_source_g1'] = to_g1

                    # Magnification (s/l)
                    M = total_length / to_g1

                    # Pitches [um]
                    self._parameters['pitch_g1'] = \
                        self._nu * self._parameters['pitch_g2'] / M
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['pitch_g0'] = \
                            (to_g1 / self._parameters['distance_g1_g2']) * \
                            self._parameters['pitch_g2']

                    # Duty cycles
                    self._parameters['duty_cycle_g1'] = \
                        self._parameters['duty_cycle_g2']
                    if 'G0' in self._parameters['component_list']:
                        self._parameters['duty_cycle_g0'] = \
                            self._parameters['duty_cycle_g2']
            else:
                # Dual phase setup

                # Remaining distance
                if self._parameters['fixed_distance'] == \
                            'distance_source_g1':
                    self._parameters['distance_source_g2'] = \
                        self._parameters['distance_source_g1'] + \
                        self._parameters['distance_g1_g2']
                elif self._parameters['fixed_distance'] == \
                            'distance_source_g2':
                    self._parameters['distance_source_g1'] = \
                        self._parameters['distance_source_g2'] - \
                        self._parameters['distance_g1_g2']

                # G2
                # Duty cycle
                self._parameters['duty_cycle_g2'] = \
                    self._parameters['duty_cycle_g1']
                # Pitche [um]
                s_g1 = self._parameters['distance_source_g1']  # [mm]
                g1_g2 = self._parameters['distance_g1_g2']  # [mm]
                self._parameters['pitch_g2'] = \
                    self._parameters['pitch_g1'] * (s_g1 + g1_g2)/s_g1

                # Fringe at detector [um] # Duty cycle
                self._parameters['duty_cycle_fringe'] = \
                    self._parameters['duty_cycle_g1']
                # Pitche [um]
                g2_d = self._parameters['distance_g2_detector']  # [mm]
                p1 = self._parameters['pitch_g1']  # [um]
                self._parameters['pitch_fringe'] = \
                    ((s_g1 + g1_g2 + g2_d)/(s_g1 + g1_g2) /
                     (1.0/p1 - s_g1/(p1*(s_g1 + g1_g2))))

        logger.info("... done.")

    def _calc_symmetrical(self):
        """
        For cone

        Notes
        =====

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
        logger.info("Calculating symmetrical setup...")
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

        logger.info("... done.")

    def _calc_inverse(self):
        """
        For cone
        """
        logger.info("Calculating inverse setup...")
        # G1 fixed
        if self._parameters['fixed_grating'] == 'g1':
            # Talbot distance (Dn)
            talbot_distance = self._parameters['talbot_order'] * \
                (np.square(self._parameters['pitch_g1'] / self._nu) /
                 (2 * self._parameters['design_wavelength']))  # [um]
            talbot_distance = talbot_distance * 1e-3  # [mm]

            # Other distances
            if self._parameters['fixed_distance'] == \
                    'distance_source_g1' or \
                    self._parameters['fixed_distance'] == \
                    'distance_g0_g1':
                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = self._parameters[self._parameters
                                         ['fixed_distance']]  # [mm]
                # G1 to G2 (dn)
                self._parameters['distance_g1_g2'] = \
                    to_g1 * talbot_distance / \
                    (to_g1 - talbot_distance)

                # Check if valid distance input
                if self._parameters['distance_g1_g2'] <= 0:
                    error_message = ("{0} too small for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be larger than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             talbot_distance))
                    logger.error(error_message)
                    raise GeometryError(error_message)
                elif self._parameters['distance_g1_g2'] < to_g1:
                    error_message = ("{0} too large for chosen talbot "
                                     "order, energy and pitch of G1."
                                     .format(self._parameters
                                             ['fixed_distance']))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                # Source/G0 to G2 (s)
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
                # Distance from Source/G0 to G2 fixed (s)
                total_length = self._parameters[self._parameters
                                                ['fixed_distance']]

                # Source/G0 to G1 (l)
                # Checks ultimately if s> 2*dn:
                if total_length <= 4.0 * talbot_distance:
                    error_message = ("{0} too small for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be larger than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             4.0 * talbot_distance))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                to_g1 = total_length/2.0 - np.sqrt(total_length**2.0 /
                                                   4.0 - total_length *
                                                   talbot_distance)

                if 'G0' in self._parameters['component_list']:
                    self._parameters['distance_g0_g1'] = to_g1
                else:
                    self._parameters['distance_source_g1'] = to_g1

                # G1 to G2 (dn)
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
                    self._parameters['pitch_g2']

            # Duty cycles
            self._parameters['duty_cycle_g2'] = \
                self._parameters['duty_cycle_g1']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g1']

        elif self._parameters['fixed_grating'] == 'g2':
            # G2 fixed
            if self._parameters['fixed_distance'] == \
                    'distance_source_g1' or \
                    self._parameters['fixed_distance'] == \
                    'distance_g0_g1':
                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = self._parameters[self._parameters
                                         ['fixed_distance']]  # [mm]

                # distance from G1 to G2 (dn)
                # dn = -05*l + sqrt(0.25*l^2 + n/(2*lambda)*p2^2*l)
                # lambda and p2 in um, need to be in mm
                wavelength = self._parameters['design_wavelength'] * \
                    1e-3  # [mm]
                p2 = self._parameters['pitch_g2'] * 1e-3  # [mm]

                self._parameters['distance_g1_g2'] = -0.5 * to_g1 + \
                    np.sqrt(0.25 * to_g1**2 +
                            self._parameters['talbot_order'] *
                            p2**2 * to_g1 / (2 * wavelength))  # [mm]

                # Check if l < dn:
                if self._parameters['distance_g1_g2'] <= to_g1:
                    error_message = ("{0} too large for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be smaller than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             self._parameters
                                             ['distance_g1_g2']))

                # Distance from Source/G0 to G2 fixed (s)
                total_length = self._parameters['distance_g1_g2'] + \
                    to_g1  # [mm]

                # Source/G0 to G2 (s)
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
                # Distance from Source/G0 to G2 fixed (s)
                total_length = self._parameters[self._parameters
                                                ['fixed_distance']]

                # distance from G1 to G2 (dn)
                # dn = s / (s * 2 * lambda / (n * p2^2) + 1)
                # lambda and p2 in um, need to be in mm
                wavelength = self._parameters['design_wavelength'] * \
                    1e-3  # [mm]
                p2 = self._parameters['pitch_g2'] * 1e-3  # [mm]

                self._parameters['distance_g1_g2'] = total_length / \
                    (total_length * 2 * wavelength /
                     (self._parameters['talbot_order'] * p2**2) + 1)  # [mm]

                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = total_length - \
                    self._parameters['distance_g1_g2']  # [mm]

                # Check if l < dn:
                if self._parameters['distance_g1_g2'] <= to_g1:
                    error_message = ("{0} too large for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be smaller than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             self._parameters
                                             ['distance_g1_g2']))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                if 'G0' in self._parameters['component_list']:
                    self._parameters['distance_g0_g1'] = to_g1
                else:
                    self._parameters['distance_source_g1'] = to_g1

            # Magnification (s/l)
            M = total_length / to_g1

            # Pitches [um]
            self._parameters['pitch_g1'] = \
                self._nu * self._parameters['pitch_g2'] / M
            if 'G0' in self._parameters['component_list']:
                self._parameters['pitch_g0'] = \
                    (to_g1 / self._parameters['distance_g1_g2']) * \
                    self._parameters['pitch_g2']

            # Duty cycles
            self._parameters['duty_cycle_g1'] = \
                self._parameters['duty_cycle_g2']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g2']

        else:
            # G0 fixed
            if self._parameters['fixed_distance'] == \
                    'distance_source_g1' or \
                    self._parameters['fixed_distance'] == \
                    'distance_g0_g1':
                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = self._parameters[self._parameters
                                         ['fixed_distance']]  # [mm]

                # distance from G1 to G2 (dn)
                # dn = l / (n * p0^2 / (2 * lambda * l) - 1)
                # lambda and p2 in um, need to be in mm
                wavelength = self._parameters['design_wavelength'] * \
                    1e-3  # [mm]
                p0 = self._parameters['pitch_g0'] * 1e-3  # [mm]

                self._parameters['distance_g1_g2'] = to_g1 / \
                    ((self._parameters['talbot_order'] * p0**2) /
                     (2 * wavelength * to_g1) - 1)  # [mm]

                # Check if l < dn:
                if self._parameters['distance_g1_g2'] <= to_g1:
                    error_message = ("{0} too large for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be smaller than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             self._parameters
                                             ['distance_g1_g2']))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                # Distance from Source/G0 to G2 fixed (s)
                total_length = self._parameters['distance_g1_g2'] + \
                    to_g1  # [mm]

                # Source/G0 to G2 (s)
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
                # Distance from Source/G0 to G2 fixed (s)
                total_length = self._parameters[self._parameters
                                                ['fixed_distance']]

                # distance from G1 to G2 (dn)
                # dn = s / (s * 2 * lambda / (n * p2^2) + 1)
                # lambda and p2 in um, need to be in mm
                wavelength = self._parameters['design_wavelength'] * \
                    1e-3  # [mm]
                p0 = self._parameters['pitch_g0'] * 1e-3  # [mm]

                self._parameters['distance_g1_g2'] = total_length / \
                    ((self._parameters['talbot_order'] * p0**2) /
                     (2 * wavelength * total_length) + 1)  # [mm]

                # Distance from Source/G0 to G1 fixed (l)
                to_g1 = total_length - \
                    self._parameters['distance_g1_g2']  # [mm]

                # Check if l < dn:
                if self._parameters['distance_g1_g2'] <= to_g1:
                    error_message = ("{0} too large for chosen talbot "
                                     "order, energy and pitch of G1. "
                                     "Must be smaller than: {1} mm"
                                     .format(self._parameters
                                             ['fixed_distance'],
                                             self._parameters
                                             ['distance_g1_g2']))
                    logger.error(error_message)
                    raise GeometryError(error_message)

                if 'G0' in self._parameters['component_list']:
                    self._parameters['distance_g0_g1'] = to_g1
                else:
                    self._parameters['distance_source_g1'] = to_g1

            # Magnification (s/l)
            M = total_length / to_g1

            # Pitches [um]
            self._parameters['pitch_g1'] = \
                self._nu * self._parameters['pitch_g2'] / M
            if 'G0' in self._parameters['component_list']:
                self._parameters['pitch_g0'] = \
                    (to_g1 / self._parameters['distance_g1_g2']) * \
                    self._parameters['pitch_g2']

            # Duty cycles
            self._parameters['duty_cycle_g1'] = \
                self._parameters['duty_cycle_g2']
            if 'G0' in self._parameters['component_list']:
                self._parameters['duty_cycle_g0'] = \
                    self._parameters['duty_cycle_g2']

        logger.info("... done.")

    def _update_distances(self):
        """
        Updates grating distances from source and radii if bent.

        Notes
        =====

        If only one grating: source to Gi is already set.
        If 2 gratings, source to first is set, and first to second
        If 3 gratings, source to first, first to second and second to third are
        set.

        """
        gratings = [grating for grating in self._parameters['component_list']
                    if "G" in grating]

        # If radius of first grating is set manually, update
        # source to first grating distance
        if self._parameters[gratings[0].lower()+'_bent'] and \
                not self._parameters[gratings[0].lower()+'_matching']:
            self._parameters['distance_source_'+gratings[0].lower()] = \
                self._parameters['radius_'+gratings[0].lower()]

        # Set distance from source to grating
        if len(gratings) == 2:
            self._parameters['distance_source_'+gratings[1].lower()] = \
                self._parameters['distance_source_'+gratings[0].lower()] + \
                self._parameters['distance_'+gratings[0].lower() +
                                 '_'+gratings[1].lower()]
        elif len(gratings) == 3:
            self._parameters['distance_source_'+gratings[1].lower()] = \
                self._parameters['distance_source_'+gratings[0].lower()] + \
                self._parameters['distance_'+gratings[0].lower() +
                                 '_'+gratings[1].lower()]
            self._parameters['distance_source_'+gratings[2].lower()] = \
                self._parameters['distance_source_'+gratings[0].lower()] + \
                self._parameters['distance_'+gratings[0].lower() +
                                 '_'+gratings[1].lower()] + \
                self._parameters['distance_'+gratings[1].lower() +
                                 '_'+gratings[2].lower()]

        # Calc source to detector distance if gratings are in system
        if gratings:
            self._parameters['distance_source_detector'] = \
                self._parameters['distance_source_'+gratings[-1].lower()] + \
                self._parameters['distance_'+gratings[-1].lower()+'_detector']

        # Set grating radius
        for grating in gratings:
            grating = grating.lower()

            if self._parameters[grating+'_bent']:
                # Check if radius/distance from source is larger 0
                distance_to_source = \
                    self._parameters['distance_source_'+grating]
                if distance_to_source == 0.0:
                    error_message = ("Radius of {0} is 0. Either set radius "
                                     "manually or choose larger distance from "
                                     "source.".format(grating.upper()))
                    logger.error(error_message)
                    raise GeometryError(error_message)
                if self._parameters[grating+'_matching']:
                    self._parameters['radius_'+grating] = distance_to_source

    def _check_sample_position(self):
        """
        Checks whether sample fits inbetween previous and next component and
        calculates sample distance from source.

        """
        sample_index = self._parameters['component_list'].index('Sample')
        previous_component = \
            self._parameters['component_list'][sample_index-1].lower()
        next_component = \
            self._parameters['component_list'][sample_index+1].lower()

        if 'a' in self._parameters['sample_position']:
            # Sample relative to previous component ('after')

            # Calc source to sample center distance
            self._parameters['distance_source_sample'] = \
                self._parameters['distance_source_'+previous_component] + \
                self._parameters['sample_distance'] + \
                self._parameters['sample_diameter']/2.0
            # Check distance of sample to next component
            if self._parameters['sample_diameter'] > \
                    (self._parameters['distance_source_'+next_component] -
                     self._parameters['distance_source_sample']):
                error_message = ("Sample diameter larger than distance from "
                                 "sample to next component.")
                logger.error(error_message)
                raise GeometryError(error_message)
        else:
            # Sample relative to next component ('before')

            # Calc source to sample center distance
            self._parameters['distance_source_sample'] = \
                self._parameters['distance_source_'+next_component] - \
                self._parameters['sample_distance'] - \
                self._parameters['sample_diameter']/2.0
            # Check distance of sample to previous component
            if self._parameters['sample_diameter'] > \
                    (self._parameters['distance_source_sample'] -
                     self._parameters['distance_source_'+previous_component]):
                error_message = ("Sample diameter larger than distance from "
                                 "sample to previous component.")
                logger.error(error_message)
                raise GeometryError(error_message)

    # Set geometry results
    def _get_geometry_results(self):
        """
        Adds self.results dict.

        Results contain:
            - setup
                - component_list
                - gi_geometry
                - beam_geometry
                - dual_phase
            - distances (not none) [mm]
            - if sample:
                - sample info
            - gratings:
                - pitches (not none) [um]
                - if bent gratings:
                    radius (input or matching distance) [mm]
            - detector:
                - curved (bool)
                - size (x, y) [mm]
                - fan/cone angles [rad]


        """
        self.results = dict()

        # Setup
        # Add component list
        self.results['component_list'] = self._parameters['component_list']
        # Add geometries
        self.results['gi_geometry'] = self._parameters['gi_geometry']
        self.results['beam_geometry'] = self._parameters['beam_geometry']
        self.results['dual_phase'] = self._parameters['dual_phase']

        # Distances
        # distances =  [('distance_b', 10), ('distance_a', 10)]
        distances = [(distance_name, distance_value)
                     for distance_name, distance_value
                     in self._parameters.iteritems()
                     if ('distance_' in distance_name and
                         distance_value is not None)]
        for distance in distances:
            self.results[distance[0]] = distance[1]

        # Gratings
        # Add pitches
        pitches = [(pitch_name, pitch_value) for pitch_name, pitch_value
                   in self._parameters.iteritems()
                   if ('pitch_' in pitch_name and pitch_value is not None)]
        for pitch in pitches:
            self.results[pitch[0]] = pitch[1]
        # Add duty cycles
        duty_cycles = [(duty_cycle_name, duty_cycle_value)
                       for duty_cycle_name, duty_cycle_value
                       in self._parameters.iteritems()
                       if ('duty_cycle_' in duty_cycle_name and
                           duty_cycle_value is not None)]
        for duty_cycle in duty_cycles:
            self.results[duty_cycle[0]] = duty_cycle[1]
        # Add grating radii
        # if bent: radius not None <=> if straight: radius None
        radii = [(radius_name, radius_value) for radius_name, radius_value
                 in self._parameters.iteritems()
                 if 'radius_' in radius_name]

        for radius in radii:
            self.results[radius[0]] = radius[1]

        # Add sample info
        if 'Sample' in self._parameters['component_list']:
            # If sample defined
            self.results['sample_position'] = \
                self._parameters['sample_position']
            self.results['sample_distance'] = \
                self._parameters['sample_distance']
            self.results['sample_shape'] = self._parameters['sample_shape']
            self.results['sample_diameter'] = \
                self._parameters['sample_diameter']

        # Detector
        self.results['curved_detector'] = self._parameters['curved_detector']
        if self.results['curved_detector']:
            self.results['radius_detector'] = \
                self._parameters['distance_source_detector']  # [mm]
        else:
            self.results['radius_detector'] =  None

        if self._parameters['field_of_view'] is not None and \
                self._parameters['pixel_size'] is not None:
            self.results['width'] = self._parameters['field_of_view'][0] * \
                self._parameters['pixel_size'] * 1e-3  # [mm]
            self.results['height'] = self._parameters['field_of_view'][1] * \
                self._parameters['pixel_size'] * 1e-3  # [mm]
            self.results['fan_angle'] = 2.0 * \
                np.arctan(self.results['width'] / (2.0 *
                          self.results['distance_source_detector']))
            self.results['cone_angle'] = 2.0 * \
                np.arctan(self.results['height'] / (2.0 *
                          self.results['distance_source_detector']))
