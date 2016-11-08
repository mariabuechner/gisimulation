"""
Module to retrieve the complexe refractive index: n = 1 - delta - i*beta and
density rho of an arbritary material or chemical comppsition.

The python package 'nist_lookup' (git@git.psi.ch:tomcat/nist_lookup.git) is
used to retrieve delta and beta. This requires the input of the dentisty,
which for certain materials can be looked up online at
'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe'

Delta:

    real part of index of refraction, with the resulting attenuation
    coefficient mu:
        mu = 4*pi*delta/lambda

Beta:

    complex part of index of refraction

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
    energy: x-ray energy [keV], use np.array for multiple energies
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
    return (H_C/np.array(wavelength))*1e-3 # [keV]

def delta_to_mu(delta, energy):
    """
    Calculate the x-ray absorption coefficient (mu) from delta and
    corresponding energy.

    Parameters
    ==========

    delta: real part of index of refraction
    energy: x-ray energy [keV]

    Returns
    =======



    Notes
    =====

    delta and energy need to be the same length, as delta = delta(energy)

    Examples
    ========


    """
    if np.array(delta).size is not np.array(energy).size:
        raise Exception('Number of deltas and energies do not match.')
    return 4*np.pi*delta/energy_to_wavelength(energy)

def shift_to_height(shift, material, energy):
    """
    .

    Parameters
    ==========



    Returns
    =======



    Notes
    =====



    Examples
    ========


    """


def height_to_shift(height, material, energy):
    """
    .

    Parameters
    ==========



    Returns
    =======



    Notes
    =====



    Examples
    ========


    """


def absorption_to_height(absorption, material, energy):
    """
    .

    Parameters
    ==========



    Returns
    =======



    Notes
    =====



    Examples
    ========


    """


def height_to_absorption(height, material, energy):
    """
    .

    Parameters
    ==========



    Returns
    =======



    Notes
    =====



    Examples
    ========


    """
