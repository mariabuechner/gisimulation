"""
Module to retrieve the complexe refractive index: n = 1 - delta - i*beta and
density rho of an arbritary material or chemical comppsition.

Either the python package 'nist_lookup' (git@git.psi.ch:tomcat/nist_lookup.git)
is used to retrieve delta and beta. This requires the input of the dentisty,
which for certain materials can be looked up online at
'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'

Alternatively the density and delta and beta will be looked up at 'X0h':
'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'

Delta:

    real part of index of refraction, with the resulting phase shift phi:
        phi = 2*pi*delta*dz/lambda

Beta:

    complex part of index of refraction, with the resulting attenuation
    coefficient mu:
        mu = 4*pi*beta/lambda

Rho: density in [g/cm3]

@author: buechner_m <maria.buechner@gmail.com>
"""
import nist_lookup.xraydb_plugin as xdb
import urllib2
import numpy as np
import logging
logger = logging.getLogger(__name__)

# Constants
H_C = 1.23984193  # [eV um]

###############################################################################
# Material constant look ups
###############################################################################


class MaterialError(Exception):
    """
    Error is raised, if material could not be looked up.
    """

def density(material):
    """
    Calculate density (rho, [g/cm3]) for given material. Look up online from
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'. If offline, need to
    enter manually.

    Parameters
    ==========

    material: chemical formula  ('Fe2O3')

    Returns
    =======

    rho: density in [g/cm3]

    Error: if offline or material unknown

    Notes
    =====

    All materials will be treated as amorphous.


    Examples
    ========

    density("Au")
    19.3

    """
    url_material = ('http://x-server.gmca.aps.anl.gov/cgi/'
                    'www_dbli.exe?x0hdb=amorphous%2Batoms')
    try:
        page = urllib2.urlopen(url_material).read()
        # Format of page, using \r\n to seperate lines
        #   Header
        #   Ac              *Amorphous*     rho=10.05     /Ac/
        #   Ag              *Amorphous*     rho=10.5      /Ag/
        page = page.splitlines()  # Split in lines
        page = [row for row in page if '*Amorphous*' in row]  # Remove header
        page = [row.split(' ') for row in page]  # Split strings
        page = [filter(None, row) for row in page]  # Remove spaces
        for row in page:
            del row[1]  # delete second column '*Amorphous*'
            del row[-1]  # delete last column '/name/'
        page = [[row[0], np.float(row[1].split('=')[1])] for row in page]
        page = dict(page)
        return page[material]  # return density belonging to material
    except urllib2.URLError:
        logger.error('URL "{}" cannot be accessed, check internet connection'
                     .format(url_material))
        raise
    except KeyError:
        logger.error("Density of material '{0}' not accessible at "
                     "'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'".
                     format(material))
        raise MaterialError("'{0}' is not a valid material".format(material))


def read_x0h(material, energy):
    """
    Look up delta and beta for single energy from
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'. If offline, need to
    enter manually.

    Parameters
    ==========

    material: chemical formula  ('Fe2O3')
    energy: x-ray energy [keV], accepts only single values

    Returns
    =======

    (delta, beta)

    where

        delta: real part of index of refraction
        beta: complex part of index of refraction

    Notes
    =====

    All materials will be treated as amorphous.


    Examples
    ========

    read_x0h('Au', 30)
    (3.5477e-06, 1.8106e-07)


    """
    energy = np.array(energy)
    if energy.size > 1:
        logger.debug('Size of "energy": {}'.format(energy.size))
        raise ValueError('"read_x0h()" does not accept multiple energies at '
                         'a time.')
    url_material = ('http://x-server.gmca.aps.anl.gov/cgi/x0h_form.exe?'
                    'xway=2&wave={}&coway=1&amor={}&i1=1&i2=1&i3=1&df1df2='
                    '-1&modeout=1&detail=0'.format(energy, material))
    # xway: 1 - wavelength, 2 - energy, 3 - line type
    # wave: [A]             [keV]       [characteristic X-ray line]
    # coway: 0 - crystal, 1 - other material, 2 - chemicalformula
    #        code: 'name' amor: 'name'        chem: 'chemical formula'
    # Miller indices: (i1, i2, i3) = 1, df1df2 = -1
    # modeout: 0 - html out, 1 - quasy-text out with keywords
    # detail: 0 - don't print coords, 1 = print coords
    try:
        page = urllib2.urlopen(url_material).read()
        # Retrieve delta and beta values, look at 'page' for details
        delta_eta = page.split('delta')[2].split('eta')
        delta = np.float(delta_eta[0].split('\r\n')[0][1:])
        beta = np.float(delta_eta[1].split('Absorption')[0].split('\r\n')
                        [0][1:])
        return delta, -beta
    except urllib2.URLError:
        logger.error('URL "{}" cannot be accessed, check internet connection'
                     .format(url_material))
        raise
    except IndexError:
        logger.error("'{0}' is not a valid material at "
                     "'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'".
                     format(material))
        raise MaterialError("'{0}' is not a valid material".format(material))


def delta_beta_nist(material, energy, rho=0, photo_only=False):
    """
    Calculate delta and beta values for given material and energy, based
    on the 'nist_lookup' package.

    Parameters
    ==========

    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False

    Returns
    =======

    (delta, beta, rho)

    where

        delta: real part of index of refraction
        beta: complex part of index of refraction
        rho: density in [g/cm3]

    Notes
    =====

    If the material is not listed at
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe', the density must be
    given manually and an error is raised.

    Examples
    ========

    delta_beta_nist('Au', 30)
    (3.5424041819846902e-06, 1.712907107947311e-07, 19.3)

    delta_beta_nist('Au', [30,35,46])
    (array([  3.54036290e-06,   2.59984680e-06,   1.49671119e-06]),
    array([  1.71290711e-07,   9.71481951e-08,   3.61364422e-08]),
    19.3)

    """
    energy = np.array(energy)
    logger.debug('Material is "{}", energy is {} keV.'.format(material,
                 energy))
    if photo_only:
        logger.debug('Only consider photo cross-section component.')
    else:
        logger.debug('Consider total cross-section.')
    if rho is not 0:
        logger.debug('Density entered manually: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
                                                                energy*1e3,
                                                                photo_only)
        logger.debug('delta: {},\tbeta: {},\tattenuation length: {}'.format(
            delta, beta, attenuation_length))
    else:
        logger.debug('Retrieve density (rho) from'
                     '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"')
        rho = density(material)
        logger.debug('Density calculated: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
                                                                energy*1e3,
                                                                photo_only)
        logger.debug('delta: {},\tbeta: {},\tattenuation length: {}'.format(
                     delta, beta, attenuation_length))
    return delta, beta, rho


def delta_beta_x0h(material, energy):
    """
    Lookup delta and beta values for given material and energy from
    'http://x-server.gmca.aps.anl.gov/cgi/x0h_form.exe

    Parameters
    ==========

    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]

    Returns
    =======

    (delta, beta, rho)

    where

        delta: real part of index of refraction
        beta: complex part of index of refraction
        rho: density in [g/cm3]

    Notes
    =====

    If the material is not listed at
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe', neither density nor
    delta and beta can be looked up, and an error is raised.

    Examples
    ========

    delta_beta_x0h('Au', 30)
    (3.5477e-06, -1.8106e-07, 19.3)

    delta_beta_x0h('Au', [30,35,46])
    (array([  3.54770000e-06,   2.60580000e-06,   1.50440000e-06]),
    array([  1.81060000e-07,   1.06140000e-07,   4.11930000e-08]),
    19.3)


    """
    logger.warning('Values interatively retrieved for each energy. Slow!')
    energy = np.array(energy)
    logger.debug('Material is "{}", energy is {} keV.'.format(material,
                 energy))
    logger.debug('Retrieve density (rho) from'
                 '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"')
    rho = density(material)
    logger.debug('Density calculated: rho = {}'.format(rho))
    if energy.size is 1:
        delta, beta = read_x0h(material, energy)
    else:
        delta, beta = np.array([read_x0h(material, e) for e in energy]).T
    logger.debug('delta: {},\tbeta: {}'.format(
        delta, beta))
    return delta, beta, rho


def delta_beta(material, energy, rho=0, photo_only=False, source='nist'):
    """
    Calculate delta and beta values for given material and energy, using the
    'nist_lookup' package (source='nist') or from
    'http://x-server.gmca.aps.anl.gov/cgi/x0h_form.exe' (source='X0h').

    Parameters
    ==========

    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only (for
    'nist_lookup', default=False
    source: source of values, choices=['nist','X0h'], default='nist'

    Returns
    =======

    (delta, beta, rho)

    where

        delta: real part of index of refraction
        beta: complex part of index of refraction
        rho: density in [g/cm3]

    Notes
    =====

    If the material is not listed at
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe', the density must be
    given manually and an error is raised. If the material ist not listed,
    'X0h' webside cannot be used as the source.

    Examples
    ========

    delta_beta('Au', 30)
    (3.5424041819846902e-06, 1.712907107947311e-07, 19.3)

    delta_beta('Au', 30, source='X0h')
    (3.5477e-06, -1.8106e-07, 19.3)

    """
    if source.lower() == 'nist':
        logger.debug('Looking up delta and beta from "nist_lookup"')
        return delta_beta_nist(material, energy, rho, photo_only)
    elif source.lower() == 'x0h':
        logger.debug('Looking up delta and beta from "X0h"')
        return delta_beta_x0h(material, energy)
    else:
        raise ValueError("Wrong data source specified: {0}. Source must be "
                         "'nist' or 'X0h'".format(source))


def test_material(material, energy, lut='nist'):
    """
    Test, if material does exist. Disable logger to suppress logger errors and
    warnings, since here only the existance matters.

    Parameters
    ==========

    material [str]:     chemical formula  ('Fe2O3', 'CaMg(CO3)2',
                        'La1.9Sr0.1CuO4')
    energy [float]:     x-ray energy [keV]
    lut [str]:          source of values, choices=['nist','X0h'],
                        default='nist'

    """
    try:
        logger_level = logger.level
        logger.level = logging.CRITICAL
        material = delta_beta(material, energy, source=lut)
        logger.level = logger_level
    finally:
        logger.level = logger_level

###############################################################################
# Conversions
###############################################################################


def energy_to_wavelength(energy):
    """
    Convert energy [keV] into wavelength [um].
    wavelength = h*c/E
    with
    E [keV]
    h*c = 1.23984193 [eV um]
    wavelength [um]

    Parameters
    ==========

    energy: in [keV], can be array

    Returns
    =======

    wavelength: in [um]

    Examples
    ========

    energy_to_wavelength(35)
    3.5424055142857143e-05
    # um or 0.35 angstroems

    """
    energy = np.array(energy)*1e3  # [eV]
    logger.debug('Energy is {} [eV].'.format(energy))
    return H_C / energy  # [um]


def wavelength_to_energy(wavelength):
    """
    Convert wavelength [um] into energy [keV].
    E = h*c/wavelength
    with
    E [keV]
    h*c = 1.23984193 [eV um]
    wavelength [um]

    Parameters
    ==========

    wavelength: in [um], can be array

    Returns
    =======

    energy: in [keV]

    Examples
    ========

    wavelength_to_energy(3.5424055142857143e-05)
    35.0

    """
    energy = H_C/np.array(wavelength)
    logger.debug('Energy is {} [eV].'.format(energy))
    return energy*1e-3  # [keV]


def attenuation_coefficient(beta, energy):
    """
    Calculate the x-ray attenuation coefficient (mu) from beta and
    corresponding energy.

    4*pi*beta/lambda


    Parameters
    ==========

    beta: complex part of index of refraction
    energy: x-ray energy [keV]

    Returns
    =======

    mu: x-ray attenuation coefficient [1/um]

    Notes
    =====

    beta and energy need to be the same length, as delta = delta(energy)

    Examples
    ========

    attenuation_coefficient(1.6237330026866183e-07, 30)
    0.049371851838870218
    # [1/um]

    """
    if np.array(beta).size is not np.array(energy).size:
        raise Exception('Number of betas and energies do not match.')
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    return 4*np.pi*beta/wavelength


def mass_attenuation_coefficient(mu, rho, convert_to_um=False):
    """
    Calculate the x-ray mass attenuation coefficient (mum) for a given density
    (rho):
        mum = mu/rho

    Parameters
    ==========

    mu: x-ray attenuation coefficient [1/um]
    rho: density [g/cm3]
    covnert_to_um: convert mum to g/um2, default=False

    Returns
    =======

    mum: x-ray mass attenuation coefficient [cm2/g], [um2/g] if
    covnert_to_um=True

    Notes
    =====

    beta and energy need to be the same length, as delta = delta(energy)

    Examples
    ========

    mass_attenuation_coefficient(0.049371851838870218, 19.3)
    25.581270382834308
    # [cm2/g]

    mass_attenuation_coefficient(0.049371851838870218, 19.3,
    convert_to_um=True)
    2558127038.283431
    # [um2/g]

    """
    mum = mu*1e4/rho  # [ (1/um -> 1/cm) / (g/cm3) = cm2/g ]
    if convert_to_um:
        mum = mum*1e8  # [ cm2/g -> um2/g]
    return mum


def absorption_to_height(absorption, material, energy, rho=0,
                         photo_only=False, source='nist'):
    """
    Calculates the necessary height (thickness) of a grating to get the
    required percentage of x-ray absorption for a given material and energy.

    Parameters
    ==========

    absorption: percentage of required x-ray absorption
    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False
    source: material params LUT... default='nist'

    Returns
    =======

    height: grating height (thickness) [um]

    Notes
    =====

    Based on Beer-Lambert law:
        I = I_0 * exp(-mu*x)
        with mu: x-ray attenuation coefficient
        and I/I_0 = transmission = 1-absorption

    Examples
    ========

    absorption_to_height(0.9, 'Au', 30)
    44.209650135346017
    # [um]

    """
    beta = delta_beta(material, energy, rho, photo_only, source)[1]
    logger.debug('Beta is {}.'.format(beta))
    mu = attenuation_coefficient(beta, energy)
    logger.debug('The attenuation coefficient is {} [1/um].'.format(mu))
    return -np.log(1-absorption)/mu


def height_to_absorption(height, material, energy, rho=0, photo_only=False,
                         source='nist'):
    """
    Calculates the resulting x-ray absorption of a grating based on the given
    height (thickness) and for a given material and energy.

    Parameters
    ==========

    height: grating height (thickness) [um]
    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False
    source: material params LUT... default='nist'

    Returns
    =======

    absorption: percentage of required x-ray absorption

    Notes
    =====

    Based on Beer-Lambert law:
    I = I_0 * exp(-mu*x)
    with mu: x-ray attenuation coefficient
    and I/I_0 = transmission = 1-absorption

    Examples
    ========

    height_to_absorption(44.209650135346017, 'Au', 30)
    0.90000000000000002
    # [%]

    """
    beta = delta_beta(material, energy, rho, photo_only, source)[1]
    logger.debug('Beta is {}.'.format(beta))
    mu = attenuation_coefficient(beta, energy)
    logger.debug('The attenuation coefficient is {} [1/um].'.format(mu))
    return 1 - np.exp(-mu*height)


def height_to_transmission(height, material, energy, rho=0, photo_only=False,
                           source='nist'):
    """
    Calculates the resulting x-ray transmission of an object based on the given
    height (thickness) and for a given material and energy.

    Parameters
    ==========

    height: grating height (thickness) [um]
    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False
    source: material params LUT... default='nist'

    Returns
    =======

    transmission: percentage of resulting x-ray transmission

    """
    return 1 - height_to_absorption(height, material, energy, rho, photo_only,
                                    source)


def phase_shift(delta, energy):
    """
    Calculate the x-ray phase shift from delta and the corresponding energy.
    Based on:
        dphi = 2*pi*delta*dx/lambda

    Parameters
    ==========

    delta: real part of index of refraction
    energy: x-ray energy [keV]

    Returns
    =======

    dphi: x-ray phase shift [(rad)/um]

    Notes
    =====

    delta and energy need to be the same length, as delta = delta(energy)

    Examples
    ========

    phase_shift(3.5424041819846902e-06, 30)
    0.53855853806309939
    # [(rad)/um]

    """
    if np.array(delta).size is not np.array(energy).size:
        raise Exception('Number of deltas and energies do not match.')
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    return 2*np.pi*delta/wavelength


def shift_to_height(dphi, material, energy, rho=0, photo_only=False,
                    source='nist'):
    """
    Calculates grating height (thickness) from required phase shift (dphi) for
    a given material and energy.

    Parameters
    ==========

    dphi: required phase shift [(rad)/um]
    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False
    source: material params LUT... default='nist'

    Returns
    =======

    heigth: grating height (thickness) [um]

    Notes
    =====

    Based on:
        dphi = 2*pi*delta*dx/lambda

    Examples
    ========

    shift_to_height(np.pi, 'Au', 30)
    5.8333355272546301
    # [um]

    """
    delta = delta_beta(material, energy, rho, photo_only, source)[0]
    logger.debug('Delta is {}.'.format(delta))
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    return dphi*wavelength / (2*np.pi*delta)


def height_to_shift(height, material, energy, rho=0, photo_only=False,
                    source='nist'):
    """
    Calculates phase shift (dphi) from given grating height (thickness) for
    a given material and energy.

    Parameters
    ==========

    heigth: grating height (thickness) [um]
    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV]
    rho: density in [g/cm3], default=0 (no density given)
    photo_only: boolean for returning photo cross-section component only,
    default=False
    source: material params LUT... default='nist'

    Returns
    =======

    dphi: required phase shift [(rad)/um] (modulus of dphi and pi)

    Notes
    =====

    Based on:
        dphi = 2*pi*delta*dx/lambda

    Examples
    ========

    height_to_shift(5.8333355272546301, 'Au', 30)
    3.1415926535897927
    # [rad]

    """
    delta = delta_beta(material, energy, rho, photo_only, source)[0]
    logger.debug('Delta is {}.'.format(delta))
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    dphi = 2*np.pi*delta*height/wavelength
    return np.mod(dphi, 2.0*np.pi)


def read_sample_values():
    """
    Read delta and mu fom sample files and interpolate for energies
    """
    pass


#if _name__ == '__main__':
#    from scipy import interpolate
#    import matplotlib.pyplot as plt

#    energy = np.array([range(1, 101)])
#
#    rho = 1
#
#    e_lut = np.array([4.00000E-03, 5.00000E-03, 6.00000E-03, 8.00000E-03,
#                      1.00000E-02, 1.50000E-02, 2.00000E-02, 3.00000E-02,
#                      4.00000E-02, 5.00000E-02, 6.00000E-02, 8.00000E-02,
#                      1.00000E-01])
#    e_lut = e_lut*1e3
#    mu_lut = np.array([7.788E+01, 4.027E+01, 2.341E+01, 9.921E+00, 5.120E+00,
#                       1.614E+00, 7.779E-01, 3.538E-01, 2.485E-01, 2.080E-01,
#                       1.875E-01, 1.662E-01, 1.541E-01])
#
#    mu_m = interpolate.spline(e_lut, mu_lut, energy)
#
#    plt.plot(energy, mu_m, 'ro')
#    plt.plot(e_lut, mu_lut, 'bo')
#    plt.show()
#
#    mu = rho * abs(mu_m)
#
#    [delta_Al, beta_Al, rho_Al] = delta_beta('Al', energy)
#
#    mu_Al = attenuation_coefficient(beta_Al, energy)
#
#    filtered_abso = np.exp(-mu_Al*0.3)
#
#    abso = np.exp(-mu*100)
#
#    plt.plot(energy, filtered_abso, 'ro')
#    plt.plot(energy, abso, 'bo')
#    plt.show()
