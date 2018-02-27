# Vis calc??? talbot order not important! Check formula

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
import scipy.io
import matplotlib.pyplot as plt
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
    parameters = args[0]
    sigma_0 = args[1]
    sample_thickness = args[2].copy()  # [mm] (=f(theta))
    sample_thickness = sample_thickness * 1e3  # [um]

    # constants
    c_0 = 1.0 / (2.0 * np.pi**2 * parameters['number_phase_steps'])

    # calc sigma over all energies
    sigma = 0.0
    print("Calculating all energies...")
    print(filter_thickness)
    for index, energy in enumerate(parameters['spectrum']['energies']):
#        print("\n{0} keV...".format(energy))
        logger.debug("Calculating for {0} keV....".format(energy))
        # Background visibility factor (energy dependent)
        # Transmission of G0 and G2 [%]
        t_g0 = materials.height_to_transmission(parameters['thickness_g0']+100,
                                                parameters['material_g0'],
                                                energy)
        t_g2 = materials.height_to_transmission(parameters['thickness_g2']+120,
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

#        print(visibility)

        # Sample transmission factor (energy and sample_thickness dependent)
        # sample_thickness dependes on theta
        transmission = \
            materials.height_to_transmission(sample_thickness,
                                             parameters['material_sample'],
                                             energy,
                                             rho=1.19)
        if transmission == 0.0:
            transmission = 1e-15
#            continue  # Skip, since value gets too larger...???
        c_t = 1.0 + 1.0/transmission

#        print(transmission)

        # Counts factor (energy dependent)
        # Remaining transmission
        t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
                                                parameters['material_g0'],
                                                energy)
        t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
                                                parameters['material_g2'],
                                                energy)
        t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
                                                parameters['material_g1'],
                                                energy)
        c_n = parameters['spectrum']['photons'][index] * t_g0 * t_g1 * t_g2

        # Sigma
        a = c_0 * c_v * c_t / c_n
        beta_filter = materials.delta_beta(parameters['material_filter'],
                                           energy,
                                           source=parameters['look_up_table'])[1]
        b = materials.attenuation_coefficient(beta_filter, energy)

#        print("\n")
#        print(c_0)
#        print(c_v)
#        print(c_t)
#        print(c_n)
#        print(a)
#        print(b)
#        print(np.exp(b*filter_thickness))

        # Sum over energies
        sigma = sigma + a * np.exp(b*filter_thickness)
#        print(sigma)
        logger.debug("...done.")

    print("...done.")
    print(sigma)

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
    parameters = args[0]
    mean_energy_0 = args[1]  # [keV]
    sample_thickness = args[2]  # [mm] (=f(theta))
    sample_thickness = sample_thickness * 1e3  # [um]

    counts = parameters['spectrum']['photons'].copy()
    # Rescale counts for each energy
    print("Calculating constraints...")
    for index, energy in enumerate(parameters['spectrum']['energies']):
        logger.debug("Calculating mean energy for {0} keV....".format(energy))
        # Sample transmission
        transmission = \
                materials.height_to_transmission(sample_thickness,
                                                 parameters['material_sample'],
                                                 energy,
                                                 rho=1.19)

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
#        beta_filter = materials.delta_beta(parameters['material_filter'],
#                                           energy,
#                                           source=parameters['look_up_table'])[1]
#        mu_filter = - materials.attenuation_coefficient(beta_filter, energy)
#        filter_transmission = np.exp(mu_filter*filter_thickness)
        filter_transmission = materials.height_to_transmission(
                                                filter_thickness,
                                                parameters['material_filter'],
                                                energy)

        # counts through sample, grating and filter
        counts[index] = parameters['spectrum']['photons'][index] * \
            transmission * t_g0 * t_g1 * t_g2 * filter_transmission
#        counts[index] = parameters['spectrum']['photons'][index] * \
#            t_g0 * t_g1 * t_g2 * filter_transmission

        logger.debug("...done.")

    mean_energy = sum(counts*parameters['spectrum']['energies']) / \
        sum(counts)  # [kev]

    print("...done.")

    return mean_energy - mean_energy_0  # Set type to 'eq', then this has
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
    ==========

    parameters [dict]

    Returns
    =======

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
    ==========

    parameters [dict]

    Returns
    =======

    sample_thicknesses [mm]
    thetas [rad]:               array of angles that actually pass through the
                                sample. others are set to zero.

    Notes
    =====

    if tangent or ray passes out of sample, thickness = 0. Round sample.

    """
    sample_radius = parameters['thichness_sample'] / 2.0  # [mm]

#    a = (parameters['sample_distance']**2.0 - sample_radius**2.0) / \
#        (1.0 + np.tan(parameters['thetas'])**2.0)  # [mm^2]
#    b = (parameters['sample_distance'] * np.tan(parameters['thetas'])) / \
#        (1.0 + np.tan(parameters['thetas'])**2.0)  # [mm]
#
#    x_1 = b - np.sqrt(b**2 - a)  # [mm]
#    x_2 = b + np.sqrt(b**2 - a)  # [mm]

    a = (parameters['sample_distance'] * np.tan(parameters['thetas'])) / \
        (1.0 + np.tan(parameters['thetas'])**2.0)  # [mm]

    b = (sample_radius**2 - parameters['sample_distance']**2 +
         (parameters['sample_distance']**2 /
          (1.0 + np.tan(parameters['thetas'])**2.0))) * \
        ((np.tan(parameters['thetas'])**2.0) /
         ((1.0 + np.tan(parameters['thetas'])**2.0)))  # [mm^2]

    x_1 = a - np.sqrt(b)  # [mm]
    x_2 = a + np.sqrt(b)  # [mm]

    # Set nans (complex) and negative (?) to 0
    x_1 = np.nan_to_num(x_1)
    x_1[x_1 < 0] = 0.0
    x_2 = np.nan_to_num(x_2)
    x_2[x_2 < 0] = 0.0

    # Calc sample cross section
    y_1 = x_1 / np.tan(parameters['thetas'])   # Element wise, [mm]
    y_2 = x_2 / np.tan(parameters['thetas'])   # Element wise, [mm]

    dx = x_2 - x_1  # [mm]
    dy = y_2 - y_1  # [mm]
    sample_thicknesses = np.sqrt(dx**2.0 + dy**2.0)  # [mm]

    # Set all angles that do not pass throught the sample (thickness==0) to 0
    thetas = parameters['thetas'].copy()
    thetas[sample_thicknesses == 0] = 0
    return sample_thicknesses, thetas


if __name__ == "__main__":

    # Set paramters
    parameters = dict()
    parameters['look_up_table'] = 'nist'
    parameters['spectrum_file'] = ("C:\\Users\\buechner_m\\Documents\\Code\\"
                                   "bCTDesign\\Simulation\\matlab_calcs\\"
                                   "Comet100kV_counts.csv")
    # _counts calculated as mean of 10keV and 20keV from 20 keV on, before from
    # 10 keV!!!
    parameters['spectrum_range'] = [30, 82]
#    parameters['spectrum_range'] = None
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
    # Grating thickness:
    # For visibility calc use actual 46 keV design heights
    # For energy calc use these missing thicknesses
    parameters['thickness_g0'] = 80.0  # [um] should be 180
    parameters['thickness_g1'] = 0.4  # [um] Was 8.8 and should be 9.2?
    parameters['thickness_g2'] = 60.0  # [um] should be 180
    parameters['duty_cycle_g0'] = 0.5
    parameters['duty_cycle_g2'] = 0.5

    # Calc sample thicknesses depending on theta
    parameters['thetas'] = calc_thetas(parameters)  # [rad]
    sample_thicknesses, thetas = calc_sample_thicknesses(parameters)  # [mm]

##    plt.plot(thetas, sample_thicknesses)
##    plt.show()
#
#    # Calc theta=0 filter thickness and mean energy
#    theta_0 = 0.0  # [rad]
#    sample_thickness_0 = parameters['thichness_sample']
#    sample_thickness_0 = sample_thickness_0 * 1e3  # [um]
#
#    filter_thickness_0 = 1.0 * 1e3  # [um]
#
#    # Optimize mean energy to 46 keV at center beam
#
#    # For _counts and 2.0 mm: 33.0312174676 before, 46.1058165904 after
#    # for normal 100kVp and 2.0mm: 33.2284455028, 46.1275334897
#
#    mean_before = np.sum(parameters['spectrum']['energies'] *
#                         parameters['spectrum']['photons']) / \
#        np.sum(parameters['spectrum']['photons'])
#
##    plt.plot(parameters['spectrum']['energies'],
##             parameters['spectrum']['photons'] )
##    plt.show()
#
#    print(mean_before)
#
#    # Include also gratings and sample!!!!!! -> gratings already make mean energy 63,
#    # but see that spectrum start shifts from 30 keV to ca 35-40 keV
#    # ISSUE: Counts get very low like this (10-25 mm needed)
#    #   -> leave at 1 mm for now
#    t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
#                                            parameters['material_g0'],
#                                            parameters['spectrum']['energies'])
#    t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
#                                            parameters['material_g1'],
#                                            parameters['spectrum']['energies'])
#    t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
#                                            parameters['material_g2'],
#                                            parameters['spectrum']['energies'])
#
##    grating_counts = parameters['spectrum']['photons'] * \
##        t_g0 * t_g1 * t_g2
##
##    plt.plot(parameters['spectrum']['energies'], grating_counts)
##    plt.show()
##
##    mean_gratings = np.sum(parameters['spectrum']['energies'] *
##                           grating_counts) / np.sum(grating_counts)
##    print(mean_gratings)
#
#    sample_transmission = \
#                materials.height_to_transmission(sample_thickness_0,
#                                                 parameters['material_sample'],
#                                                 parameters['spectrum']['energies'],
#                                                 rho=1.19)
#
#
#    filter_transmission = materials.height_to_transmission(filter_thickness_0,
#                                         parameters['material_filter'],
#                                         parameters['spectrum']['energies'],
#                                         source=parameters['look_up_table'])
#
#    filtered_counts = parameters['spectrum']['photons'] * \
#        t_g0 * t_g1 * t_g2 * sample_transmission * filter_transmission
#
##    plt.plot(parameters['spectrum']['energies'], filtered_counts)
##    plt.show()
#
#
#    mean_after = np.sum(parameters['spectrum']['energies'] *
#                        filtered_counts) / np.sum(filtered_counts)
#    print(mean_after)
#    # Done
#
#    # Calc 0-values
#    mean_energy_0 = mean_after  # [keV]
#
##    # constants
##    c_0 = 1.0 / (2.0 * np.pi**2 * parameters['number_phase_steps'])
##    sigma_0 = 0.0
##    for index, energy in enumerate(parameters['spectrum']['energies']):
##        print("\n{0} keV...".format(energy))
##        logger.info("Calculating for {0} keV....".format(energy))
##        # Background visibility factor (energy dependent)
##        # Transmission of G0 and G2 [%]
##        t_g0 = materials.height_to_transmission(parameters['thickness_g0']+100,
##                                                parameters['material_g0'],
##                                                energy)
##        t_g2 = materials.height_to_transmission(parameters['thickness_g2']+120,
##                                                parameters['material_g2'],
##                                                energy)
##        dc_g0 = parameters['duty_cycle_g0']
##        dc_g2 = parameters['duty_cycle_g2']
##        # Background visibility
##        visibility = (4.0/np.pi) * \
##                     ((dc_g2*(1.0-t_g2)*np.sinc(dc_g2)) /
##                      (t_g2+dc_g2*(1.0-t_g2))) * \
##                     ((dc_g0*(1.0-t_g0)*np.sinc(dc_g0)) /
##                      (t_g0+dc_g0*(1.0-t_g0)))
##        c_v = 1.0/visibility**2
##
##        print(visibility)
##
##        # Sample transmission factor (energy and sample_thickness dependent)
##        # sample_thickness dependes on theta
##        transmission = \
##            materials.height_to_transmission(sample_thickness_0,
##                                             parameters['material_sample'],
##                                             energy,
##                                             rho=1.19)
##        if transmission == 0.0:
##            transmission = 1e-15
###            continue  # Skip, since value gets too larger...???
##        c_t = 1.0 + 1.0/transmission
##
###        print(transmission)
##
##        # Counts factor (energy dependent)
##        # Remaining transmission
##        t_g0 = materials.height_to_transmission(parameters['thickness_g0'],
##                                                parameters['material_g0'],
##                                                energy)
##        t_g2 = materials.height_to_transmission(parameters['thickness_g2'],
##                                                parameters['material_g2'],
##                                                energy)
##        t_g1 = materials.height_to_transmission(parameters['thickness_g1'],
##                                                parameters['material_g1'],
##                                                energy)
##        c_n = parameters['spectrum']['photons'][index] * t_g0 * t_g1 * t_g2
##
##        # Sigma
##        a = c_0 * c_v * c_t / c_n
##        beta_filter = materials.delta_beta(parameters['material_filter'],
##                                           energy,
##                                           source=parameters['look_up_table'])[1]
##        b = materials.attenuation_coefficient(beta_filter, energy)
##
###        print(a)
###        print(b)
##
##        # Sum pver energy
##        sigma_0 = sigma_0 + a * np.exp(b*filter_thickness_0)
###        print(sigma_0)
##        logger.info('...done.')
#
##    # Old sigmas: without gratings in mean_energy_0
###    sigma_0 = 517126.007558  # from 20 keV on...
##    sigma_0 = 83.021283925579809  # from 25 keV on...
##
##    sigma_0 = 28.011132475316167  # from 30 keV, with gratings
#
##    sigma_0 = 31.381097701311816  # with positive mu..., 30-100keV
##    sigma_0 = 1.5580242573545113  # with positive mu..., 30-60keV
##    sigma_0 = 10.377495157145837  # with positive mu..., 30-82keV
#    sigma_0 = 0.93802246451191473  # with positive mu..., 30-82keV, correct vis calc
#
#    # Optimize filter
#
#    # Take only every 50th angle
#    sample_thicknesses = sample_thicknesses[49::50]  # [mm]
#    thetas = thetas[49::50]  # [rad]
#    print(sample_thicknesses)
#    print(thetas)
#
#    filter_thicknesses = thetas * 0.0
#    x0 = filter_thickness_0
##    x0 = 5518.8125+500
#    for index, sample_thickness in enumerate(sample_thicknesses):
#        print("{0} rad ({1}.)...".format(thetas[index], index))
#        logger.info("Calculating for {0} rad ({1}.)..."
#                    .format(thetas[index], index))
#        # Skip if zero
#        if sample_thickness == 0.0:
#            filter_thicknesses[index] = 0.0
#            logger.debug('Filter thickness is {0} [um]'
#                         .format(filter_thicknesses[index]))
#            continue
##        if index < 20:
##            continue
#        # Options
##        solver = 'COBYLA'  # COBYLA or SLSQP
#        args = (parameters, sigma_0, sample_thickness)
#        constraints = {'type': 'eq', 'fun': constraint_mean_energy,
#                       'args': (parameters, mean_energy_0, sample_thickness)}
#
##        # Minimize Scalar (no contraints)
##        results = minimize_scalar(optimize_phase_detector_variance, args=args,
##                                  bounds=(filter_thickness_0, None),
##                                  tol=1.0,
##                                  options={'maxiter': 10})
#
#        # Minimize
##        # Default (no contraints, no bounds)
##        results = minimize(optimize_phase_detector_variance, x0, args,
##                           tol=1.0, options={'eps': 1.0, 'maxiter': 10})
##
##        # TNC (no constriants)
##        results = minimize(optimize_phase_detector_variance, x0, args,
##                           method='TNC',
##                           options={'eps': 1.0, 'ftol': 0.1, 'maxiter': 10},
##                           bounds=[(filter_thickness_0, None)])
##
#        # COBYLA
#        results = minimize(optimize_phase_detector_variance, x0, args,
#                           method='COBYLA',
#                           options={'rhobeg': 200.0, 'tol': 1.0,  # 50
#                                    'catol':  1.0})  # , 'maxiter': 1000
##        # SLSQP
##        results = minimize(optimize_phase_detector_variance, x0, args,
##                           method='SLSQP',
##                           bounds=(filter_thickness_0, None),
##                           options={'eps': 1.0, 'ftol': 10e-2, 'maxiter': 10})
#        filter_thicknesses[index] = results.x  # [um]
#        print(filter_thicknesses[index])
#        logger.debug('Filter thickness is {0} [um]'
#                     .format(filter_thicknesses[index]))
#        # set next starting point to current thickness plus last increment
#        x0 = filter_thicknesses[index] + (filter_thicknesses[index]-x0)
#        logger.info('...done.')
#
##    # Calculate x and y pairs
##    filter_thicknesses = filter_thicknesses * 1e-3  # [mm]
#
#    x = parameters['filter_position'] * np.tan(thetas) + \
#        filter_thicknesses * np.sin(thetas)
#    y = parameters['filter_position'] + \
#        filter_thicknesses * np.cos(thetas)
#
#    all_results = dict()
#    all_results['mean_energy_0'] = mean_energy_0  # [keV]
#    all_results['sigma_0'] = sigma_0
#    all_results['thetas'] = thetas.copy()  # [rad]
#    all_results['sample_thicknesses'] = sample_thicknesses.copy()  # [mm]
#    all_results['filter_thicknesses'] = filter_thicknesses  # [mm]
#    all_results['x'] = x.copy()
#    all_results['y'] = y.copy()
##    scipy.io.savemat('results_17_end-rad_49_50-step_30_82-keV', all_results)
#

    results = scipy.io.loadmat('filter_sample_thicknesses.mat')
    # Collapse and remove 0 value (where sample thickness was 0 and filter was
    # set to 0)
    # Thicknesses in mm
    filter_thicknesses = np.squeeze(results['filter_thicknesses'][:1,:-1])
    sample_thicknesses = np.squeeze(results['sample_thicknesses'][:1,:-1])

    thetas = thetas[49::50][:-1]

    number_energies = len(parameters['spectrum']['energies'])
    number_angles = len(thetas)

    filtered_photons = np.zeros([number_angles, number_energies])
    sampled_photons = np.zeros([number_angles, number_energies])
    for energy_index, energy in enumerate(parameters['spectrum']['energies']):
        # photons after = photons before * transmission
        # height to transmission: height in um
        print(energy)

        for angle, theta in enumerate():
            print(theta)
            filtered_photons[angle, energy_index] = \
                parameters['spectrum']['photons'][energy_index] * \
                materials.height_to_transmission(filter_thicknesses[angle]*1e3,
                                                 parameters['material_filter'],
                                                 energy)

            sampled_photons[angle, energy_index] = \
                filtered_photons[angle, energy_index] * \
                materials.height_to_transmission(sample_thicknesses[angle]*1e3,
                                                 parameters['material_sample'],
                                                 energy,
                                                 rho=1.19)

    all_results = dict()
    all_results['thetas'] = thetas.copy()
    all_results['sample_thicknesses'] = sample_thicknesses.copy()  # [mm]
    all_results['filter_thicknesses'] = filter_thicknesses.copy()  # [mm]
    all_results['filtered_photons'] = filtered_photons.copy()
    all_results['sampled_photons'] = sampled_photons.copy()
    scipy.io.savemat('spectrum_dev', all_results)

    # Plot results
    # A: absolute
    # 1: after filter
    for angle, theta in enumerate(thetas):
        plt.plot(parameters['spectrum']['energies'],
                 filtered_photons[angle, :])
#    plt.legend(thetas)
    plt.ylabel('Photons [abs]')
    plt.xlabel('Energies [kev]')
    plt.show()

    # 2: after sample
    for angle, theta in enumerate(thetas):
        plt.plot(parameters['spectrum']['energies'],
                 sampled_photons[angle, :])
#    plt.legend(thetas)
    plt.ylabel('Photons [abs]')
    plt.xlabel('Energies [kev]')
    plt.show()

    # B: relative
    # 1: after filter
    for angle, theta in enumerate(thetas):
        filtered = filtered_photons[angle, :] / sum(filtered_photons[angle, :])
        plt.plot(parameters['spectrum']['energies'],
                 filtered)
#    plt.legend(thetas)
    plt.ylabel('Photons [% / keV]')
    plt.xlabel('Energies [kev]')
    plt.show()

    # 2: after sample
    for angle, theta in enumerate(thetas):
        sampled = sampled_photons[angle, :] / sum(sampled_photons[angle, :])
        plt.plot(parameters['spectrum']['energies'],
                 sampled)
#    plt.legend(thetas)
    plt.ylabel('Photons [% / keV]')
    plt.xlabel('Energies [kev]')
    plt.show()



















