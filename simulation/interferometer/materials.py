"""
Module to retrieve the complexe refractive index: n = 1 - delta - i*beta and
density rho of an arbritary material or chemical comppsition.

The python package 'nist_lookup' (git@git.psi.ch:tomcat/nist_lookup.git) is
used to retrieve delta and beta. This requires the input of the dentisty,
which for certain materials can be looked up online at
'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'

Delta:

    real part of index of refraction, with the resulting phase shift phi:
        phi = 2*pi*delta*dz/lambda

Beta:

    complex part of index of refraction, with the resulting attenuation
    coefficient mu:
        mu = 4*pi*beta/lambda

Rho: density in [g/cm3]

"""
import nist_lookup.xraydb_plugin as xdb
import urllib2
import numpy as np
import logging
logger = logging.getLogger(__name__)

# Constants
H_C = 1.23984193 # [eV um]

###############################################################################
# Material constants look ups
###############################################################################

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

    materials.rho("Au")
    19.3

    """
    url_material = ('http://x-server.gmca.aps.anl.gov/cgi/'
        'www_dbli.exe?x0hdb=amorphous%2Batoms')
    try:
        page=urllib2.urlopen(url_material).read()
        # Format of page, using \r\n to seperate lines
        #   Header
        #   Ac              *Amorphous*     rho=10.05     /Ac/
        #   Ag              *Amorphous*     rho=10.5      /Ag/
        page = page.splitlines() # Split in lines
        page = [row for row in page if '*Amorphous*' in row] # Remove header
        page = [row.split(' ') for row in page] # Split strings
        page = [filter(None, row) for row in page] # Remove spaces
        for row in page:
            del row[1] # delete second column '*Amorphous*'
            del row[-1] # delete last column '/name/'
        page = [[row[0],np.float(row[1].split('=')[1])] for row in page]
        page = dict(page)
        return page[material] # return density belonging to material
    except urllib2.URLError as err:
        logger.error('URL "{}" cannot be accessed, check internet connection'
            .format(url_material))
        raise
    except KeyError as err:
        logger.error('Density of material "{}" not accessible at '
            '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"'.format(
            material))
        raise

def delta_beta(material, energy, rho=0, photo_only=False):
    """
    Calculate delta and beta values for given material and energy.

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
    'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe', the desnity must be
    given manually and a error message is shown.

    Examples
    ========

    delta_beta('Au',30)
    (3.5424041819846902e-06, 1.712907107947311e-07, 19.3)

    delta_beta('Au',[30,35,46])
    (array([  3.54036290e-06,   2.59984680e-06,   1.49671119e-06]),
    array([  1.71290711e-07,   9.71481951e-08,   3.61364422e-08]),
    19.3)

    """
    energy = np.array(energy)
    logger.info('Getting delta and beta for "{}" at [{}] keV.'.format(material,
        energy))
    if photo_only:
        logger.info('Only consider photo cross-section component.')
    else:
        logger.info('Consider total cross-section.')
    if rho is not 0:
        logger.info('Density entered manually: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
            energy*1e3, photo_only)
        logger.debug('delta: {}\nbeta: {}\nattenuation length: {}'.format(
            delta, beta, attenuation_length))
    else:
        logger.info('Retrieve density (rho) from',
            '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"')
        rho = density(material)
        logger.debug('Density calculated: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
            energy*1e3, photo_only)
        logger.debug('delta: {}\nbeta: {}\nattenuation length: {}'.format(
            delta, beta, attenuation_length))
    return delta,beta,rho

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
    energy = np.array(energy)*1e3 # [eV]
    logger.debug('Energy is {} [eV].'.format(energy))
    return H_C / energy # [um]

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
    return energy*1e-3 # [keV]

def attenuation_coefficient(beta, energy):
    """
    Calculate the x-ray attenuation coefficient (mu) from beta and
    corresponding energy.

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
    mum = mu*1e4/rho # [ (1/um -> 1/cm) / (g/cm3) = cm2/g ]
    if convert_to_um:
        mum = mum*1e8 # [ cm2/g -> um2/g]
    return mum

def absorption_to_height(absorption, material, energy, rho=0,
photo_only=False):
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
    beta = delta_beta(material, energy, rho, photo_only)[1]
    logger.debug('Beta is {}.'.format(beta))
    mu = attenuation_coefficient(beta, energy)
    logger.debug('The attenuation coefficient is {} [1/um].'.format(mu))
    return -np.log(1-absorption)/mu

def height_to_absorption(height, material, energy, rho=0, photo_only=False):
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
    beta = delta_beta(material, energy, rho, photo_only)[1]
    logger.debug('Beta is {}.'.format(beta))
    mu = attenuation_coefficient(beta, energy)
    logger.debug('The attenuation coefficient is {} [1/um].'.format(mu))
    return 1 - np.exp(-mu*height)

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

def shift_to_height(dphi, material, energy, rho=0, photo_only=False):
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
    delta = delta_beta(material, energy, rho, photo_only)[0]
    logger.debug('Delta is {}.'.format(delta))
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    return dphi*wavelength/ (2*np.pi*delta)

def height_to_shift(height, material, energy, rho=0, photo_only=False):
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

    Returns
    =======

    dphi: required phase shift [(rad)/um]

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
    delta = delta_beta(material, energy, rho, photo_only)[0]
    logger.debug('Delta is {}.'.format(delta))
    wavelength = energy_to_wavelength(energy)
    logger.debug('Wavelengthis {} [um].'.format(wavelength))
    return 2*np.pi*delta*height/wavelength
