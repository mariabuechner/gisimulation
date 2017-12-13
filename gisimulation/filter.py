"""
Module to calculate the shape of a filter for x-ray grating interferometry.

Calculate the filter thicknesses from source to each pixel based on the
minimization of the least square error of an optimization function.

Choices for optimization function:

    - inter pixel variance of detector quantum noise in phase
    (Revol et al., 2010, Noise analysis of grating-based x-ray differential
    phase contrast imaging)

Note:

    filter design only in x-z plane, not in y (only fan angles considered,
    not cone)

    Parameters
    ##########

    parameters [dict]
        look_up_table [str]
        spectrum [dict]
            energies [kev]
            photons [counts/pixel/sec]
        thetas [rad]:                   fan-angles from source center to pixels
        number_phase_steps
        material_sample
        sample_distance [mm]
        thichness_sample [mm]           if round, is diameter
        material_filter
        filter_position [mm]
        material_g0
        material_g1
        material_g2
        thickness_g0 [um]
        thickness_g1 [um]
        thickness_g2 [um]
        duty_cycle_g0
        duty_cycle_g2


    Notes
    #####

    Current assumtions/limitations:

    for photon counting detectors:  f1_r and f1_s are 1
    for no scatter sample:          mean visibility reduction is 1
    cylindric sample
    for talbot-lau and matching gratings

@author: buechner_m <maria.buechner@gmail.com>
"""
import numpy as np
import logging
import interferometer.materials as materials
import simulation.check_input as check_input
from scipy.optimize import minimize, minimize_scalar
logger = logging.getLogger(__name__)
#logger.setLevel = logging.INFO
logger.level = logging.INFO


def optimize_phase_detector_variance(filter_thickness, *args):
    """
    Parameters
    ##########

    filter_thickness [mm]       to be solved/found
    args[0]                     parameters [dict]
    args[1]                     sigma_0
    args[2]                     sample_thickness [mm] (=f(theta))

    """
    # Use copy of paramters, since reference and not content is passed
    parameters = args[0].copy()

    sigma_0 = args[1]
    sample_thickness = args[2].copy()  # [mm] (=f(theta))
    sample_thickness = sample_thickness * 1e3  # [um]

    # constants
    c_0 = 1.0 / (2.0 * np.pi**2 * parameters['number_phase_steps'])

    # calc sigma over all energies
    sigma = 0.0
    for index, energy in enumerate(parameters['spectrum']['energies']):
        print("{0} keV...".format(energy))
        logger.info("Calculating for {0} keV....".format(energy))
        # Background visibility factor (energy dependent)
        # Transmission of G0 and G2 [%]
        t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
                                                parameters['material_g0'],
                                                energy)
        t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
                                                parameters['material_g2'],
                                                energy)
        dc_g0 = parameters['duty_cycle_g0']
        dc_g2 = parameters['duty_cycle_g2']
        # Background visibility
        visibility = (4.0/np.pi) * \
                     ((dc_g2*(1.0-t_g2)*np.sinc(dc_g2)) /
                      (t_g2+dc_g2*(1.0-t_g2))) * \
                     ((dc_g0*(1.0-t_g0)*np.sinc(dc_g0)) /
                      (t_g0+dc_g0*(1.0-t_g0)))
        c_v = 1.0/visibility**2

        # Sample transmission factor (energy and sample_thickness dependent)
        # sample_thickness dependes on theta
        transmission = \
            materials.height_to_transmission(sample_thickness,
                                             parameters['material_sample'],
                                             energy,
                                             rho=1.19)
        c_t = 1.0 + 1.0/transmission

        # Counts factor (energy dependent)
        # Remaining transmission
        t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
                                                parameters['material_g1'],
                                                energy)
        c_n = parameters['spectrum']['photons'][index] * t_g0 * t_g1 * t_g2

        # Sigma
        a = c_0 * c_v * c_t / c_n
        beta_filter = materials.delta_beta(parameters['material_filter'],
                                           energy,
                                           source=parameters['look_up_table'])[0]
        b = - materials.attenuation_coefficient(beta_filter, energy)
        # Sum pver energy
        sigma = sigma + a * np.exp(b*filter_thickness)
        logger.info("...done.")

    # Minimize least square error
    return (sigma - sigma_0)**2


def constraint_mean_energy(filter_thickness, *args):
    """
    mean energy atr detector, after passint through filter, sample and
    gratings should be constant

    filter_thickness [mm]       to be solved/found
    args[0]                     parameters [dict]
    args[1]                     mean_energy_0 [keV]
    args[2]                     sample_thickness [mm] (=f(theta))

    Notes
    #####

    minimize method must be  COBYLA or SLSQP to consider constraints

    """
    # Use copy of paramters, since reference and not content is passed
    parameters = args[0].copy()

    mean_energy_0 = args[1]  # [keV]
    sample_thickness = args[2]  # [mm] (=f(theta))
    sample_thickness = sample_thickness * 1e3  # [um]

    counts = parameters['spectrum']['photons'].copy()  # copy necessary again?
    # Rescale counts for each energy
    for index, energy in enumerate(parameters['spectrum']['energies']):
        print("ME {0} keV...".format(energy))
        logger.info("Calculating mean energy for {0} keV....".format(energy))
        # Sample transmission
        transmission = \
                materials.height_to_transmission(sample_thickness,
                                                 parameters['material_sample'],
                                                 energy,
                                                 rho=1.19)
        if transmission == 0.0:
            transmission = 1e-15

        # Grating transmission
        t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
                                                parameters['material_g0'],
                                                energy)
        t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
                                                parameters['material_g1'],
                                                energy)
        t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
                                                parameters['material_g2'],
                                                energy)

        # Filter transmission
        beta_filter = materials.delta_beta(parameters['material_filter'],
                                           energy,
                                           source=parameters['look_up_table'])[0]
        mu_filter = - materials.attenuation_coefficient(beta_filter, energy)
        filter_transmission = np.exp(mu_filter*filter_thickness)

        # counts through sample, grating and filter
        counts[index] = parameters['spectrum']['photons'][index] * \
            transmission * t_g0 * t_g1 * t_g2 * filter_transmission

        logger.info("...done.")

    weighted_spectrum = sum(counts*parameters['spectrum']['energies']) / \
        sum(counts)  # [kev]

    return weighted_spectrum - mean_energy_0  # Set type to 'eq', then this has
                                              # to be 0

#def func(t, *args):
#    """
#    E range of energies -> array
#    M = M (theta)
#    """
#    E = args[0]
#    M = args[1]
#
##    sigma = 0.0
##    for e in E:
##        sigma = sigma + e*np.exp(M*t)
##    return sigma
#    return (np.exp(t * E) - np.exp(t * M) + 19000)**2
#
#
#def con(t, E):
#    return np.mean(E*t/np.max(E))


def calc_thetas(parameters):
    """
    Returns angles from source center to detector pixel center on positive
    x-axis, not oncluding center pixel (if odd number of pixels).

    Parameters
    ##########

    parameters [dict]

    Returns
    #######

    thetas [rad]

    """
    # Use copy of paramters, since reference and not content is passed
    parameters = parameters.copy()

    number_pixels = parameters['field_of_view'][0]  # in x>0 direction
    if parameters['curved_detector']:
        logger.warning("Theta calculation for curved detector not yet "
                       "implemented. Change to flat detector "
                       "(parameters['curved_detector'] =  False).")
    else:
        # Flat detector
        number_pixels = int(np.round(number_pixels / 2.0))
        thetas = np.zeros(number_pixels)
        for pixel_number in np.arange(0, number_pixels):
            if number_pixels%2 == 0:
                # is even
                pixel_position = parameters['pixel_size']/2.0 + \
                    pixel_number * parameters['pixel_size']  # [um]
            else:
                # is odd
                pixel_position = pixel_number * parameters['pixel_size']  # [um]
            # Calc angle
            pixel_position = pixel_position * 1e-3  # [mm]
            thetas[pixel_number] = np.arctan(pixel_position /
                                       parameters['distance_source_detector'])
    return thetas

def calc_sample_thicknesses(parameters):
    """
    Calculate sample crosssection (thickness, length of path) for given thetas.

    x = b +/- sqrt(b^2 - a)
    y = tan(theta) * x

    with a = (sample_distance^2 - sample_radius^2)/(1+tan^2(theta))
    and  b = (sample_distance*tan(theta))/(1+tan^2(theta))

    with b^2-a > 0 and sqrt(b^2-a)>b (else: 0 thickness)

    Parameters
    ##########

    parameters [dict]

    Returns
    #######

    sample_thicknesses [mm]
    thetas [rad]:               array of angles that actually pass through the
                                sample. others are set to zero.

    Notes
    #####

    if tangent or ray passes out of sample, thickness = 0. Round sample.

    """
    # Use copy of paramters, since reference and not content is passed
    parameters = parameters.copy()

    sample_radius = parameters['thichness_sample'] / 2.0  # [mm]

    a = (parameters['sample_distance']**2.0 - sample_radius**2.0) / \
        (1.0 + np.tan(parameters['thetas'])**2.0)  # [mm^2]
    b = (parameters['sample_distance'] * np.tan(parameters['thetas'])) / \
        (1.0 + np.tan(parameters['thetas'])**2.0)  # [mm]

    x_1 = b - np.sqrt(b**2 - a)  # [mm]
    x_2 = b + np.sqrt(b**2 - a)  # [mm]


    # Set nans (complex) and negative (?) to 0
    x_1 = np.nan_to_num(x_1)
    x_1[x_1 < 0] = 0.0
    x_2 = np.nan_to_num(x_2)
    x_2[x_2 < 0] = 0.0

    # Calc sample cross section
    y_1 = np.tan(parameters['thetas']) * x_1  # Element wise, [mm]
    y_2 = np.tan(parameters['thetas']) * x_2  # Element wise, [mm]

    dx = x_2 - x_1  # [mm]
    dy = y_2 - y_1  # [mm]
    sample_thicknesses = np.sqrt(dx**2.0 + dy**2.0)  # [mm]

    # Set all angles that do not pass throught the sample (thickness==0) to 0
    thetas = parameters['thetas'].copy()  # not clear why necessary again...?
    thetas[sample_thicknesses == 0] = 0
    return sample_thicknesses, thetas


if __name__ == "__main__":

#    E = 4.0
#    M = 5.0
#    x0 = 0.0
#
#    results = minimize(func, x0, (E, M), tol=10**-3)
##    results = minimize_scalar(func, args=(E, M))
#    t = results.x
#    print(results.x)

    # Set paramters
    parameters = dict()
    parameters['look_up_table'] = 'nist'
    parameters['spectrum_file'] = ("C:\\Users\\buechner_m\\Documents\\Code\\"
                                   "bCTDesign\\Simulation\\matlab_calcs\\"
                                   "Comet100kV_counts.csv")
    # _counts calculated as mean of 10keV and 20keV from 20 keV on, before from
    # 10 keV!!!
    parameters['spectrum_range'] = None
    parameters['spectrum_step'] = None
    parameters['design_energy'] = 46  # [keV]
    [parameters['spectrum'], min_energy, max_energy] = \
        check_input._get_spectrum(parameters['spectrum_file'],
                                  parameters['spectrum_range'],
                                  parameters['spectrum_step'],
                                  parameters['design_energy'])
    # FOV at detector 208 mm at 75 um pixel size: ca. 2775 pixel
    parameters['pixel_size'] = 75  # [um]
    parameters['field_of_view'] = np.array([2775, 1.0])
    parameters['curved_detector'] = False
    parameters['distance_source_detector'] = 1041  # [mm]
    parameters['number_phase_steps'] = 31.0
    parameters['material_sample'] = 'C5H8O2'  # PMMA
    parameters['sample_distance'] = 520.5  # [mm]
    parameters['thichness_sample'] = 100.0  # [mm]
    parameters['material_filter'] = 'Al'
    parameters['filter_position'] = 165.0  # [mm]
    parameters['material_g0'] = 'Au'
    parameters['material_g1'] = 'Au'
    parameters['material_g2'] = 'Au'
    parameters['thickness_g0'] = 80.0  # [um]
    parameters['thickness_g1'] = 1.2  # [um]
    parameters['thickness_g2'] = 60.0  # [um]
    parameters['duty_cycle_g0'] = 0.5
    parameters['duty_cycle_g2'] = 0.5

    # Calc sample thicknesses depending on theta
    parameters['thetas'] = calc_thetas(parameters)  # [rad]
    sample_thicknesses, thetas = calc_sample_thicknesses(parameters)  # [mm]

    # Calc theta=0 filter thickness and mean energy
    theta_0 = 0.0  # [rad]
    sample_thickness_0 = parameters['thichness_sample']

    # Optimize mean energy to 46 keV at center beam
    filter_thickness_0 = 2.0 * 1e3  # [um]
    # For _counts and 2.0 mm: 33.0312174676 before, 46.1058165904 after
    # for normal 100kVp and 2.0mm: 33.2284455028, 46.1275334897

    mean_before = np.sum(parameters['spectrum']['energies'] *
                         parameters['spectrum']['photons']) / \
        np.sum(parameters['spectrum']['photons'])
    print(mean_before)

    filtered_counts = parameters['spectrum']['photons'] * \
        materials.height_to_transmission(filter_thickness_0,
                                         parameters['material_filter'],
                                         parameters['spectrum']['energies'],
                                         source=parameters['look_up_table'])

    mean_after = np.sum(parameters['spectrum']['energies'] *
                        filtered_counts) / np.sum(filtered_counts)
    print(mean_after)
    # Done

    # Calc 0-values
    mean_energy_0 = mean_after  # [keV]

#    sample_thickness_0 = sample_thickness_0 * 1e3  # [um]
#
#    # constants
#    c_0 = 1.0 / (2.0 * np.pi**2 * parameters['number_phase_steps'])
#    sigma_0 = 0.0
#    for index, energy in enumerate(parameters['spectrum']['energies']):
#        print("{0} keV...".format(energy))
#        logger.info("Calculating for {0} keV....".format(energy))
#        # Background visibility factor (energy dependent)
#        # Transmission of G0 and G2 [%]
#        t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
#                                                parameters['material_g0'],
#                                                energy)
#        t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
#                                                parameters['material_g2'],
#                                                energy)
#        dc_g0 = parameters['duty_cycle_g0']
#        dc_g2 = parameters['duty_cycle_g2']
#        # Background visibility
#        visibility = (4.0/np.pi) * \
#                     ((dc_g2*(1.0-t_g2)*np.sinc(dc_g2)) /
#                      (t_g2+dc_g2*(1.0-t_g2))) * \
#                     ((dc_g0*(1.0-t_g0)*np.sinc(dc_g0)) /
#                      (t_g0+dc_g0*(1.0-t_g0)))
#        c_v = 1.0/visibility**2
#
#        # Sample transmission factor (energy and sample_thickness dependent)
#        # sample_thickness dependes on theta
#        transmission = \
#            materials.height_to_transmission(sample_thickness_0,
#                                             parameters['material_sample'],
#                                             energy,
#                                             rho=1.19)
#        if transmission == 0.0:
#            transmission = 1e-15
#        c_t = 1.0 + 1.0/transmission
#
#        # Counts factor (energy dependent)
#        # Remaining transmission
#        t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
#                                                parameters['material_g1'],
#                                                energy)
#        c_n = parameters['spectrum']['photons'][index] * t_g0 * t_g1 * t_g2
#
#        # Sigma
#        a = c_0 * c_v * c_t / c_n
#        beta_filter = materials.delta_beta(parameters['material_filter'],
#                                           energy,
#                                           source=parameters['look_up_table'])[0]
#        b = - materials.attenuation_coefficient(beta_filter, energy)
#        # Sum pver energy
#        sigma_0 = sigma_0 + a * np.exp(b*filter_thickness_0)
#        logger.info('...done.')

    sigma_0 = 5.4192948236178471e-47

#    filter_thicknesses = parameters['thetas'] * 0.0
#    x0 = filter_thickness_0
#    for index, sample_thickness in enumerate(sample_thicknesses):
#        print("{0} rad ({1}.)...".format(parameters['thetas'][index], index))
#        logger.info("Calculating for {0} rad ({1}.)..."
#                    .format(parameters['thetas'][index], index))
#        # Options
#        method = 'COBYLA'  # COBYLA or SLSQP
#        args = (parameters, sigma_0, sample_thickness)
#        constraints = {'type': 'eq', 'fun': constraint_mean_energy,
#                       'args': (parameters, mean_energy_0, sample_thickness)}
#
#        results = minimize(optimize_phase_detector_variance, x0, args,
#                           tol=10**-3)
#        filter_thicknesses[index] = results.x
#        print(results.x)
#        # set next starting point to current thickness
#        x0 = filter_thicknesses
#        logger.info('...done.')