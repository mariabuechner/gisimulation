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
        '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"'.format(material))
        raise

def delta_beta(material, energy, rho=0):
    """
    Calculate delta and beta values for given material and energy.

    Parameters
    ==========

    material: chemical formula  ('Fe2O3', 'CaMg(CO3)2', 'La1.9Sr0.1CuO4')
    energy: x-ray energy [keV], use np.array for multiple energies
    rho: density in [g/cm3], optional, default=0 (no density given)

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
    logger.info('Getting delta and beta for "{}" at [{}] keV'.format(material,
    energy))
    if rho is not 0:
        logger.info('Density entered manually: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
        energy*1000)
        logger.debug('delta: {}\nbeta: {}\nattenuation length: {}'.format(
        delta, beta, attenuation_length))
    else:
        logger.info('Retrieve density (rho) from',
        '"http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe"')
        rho = density(material)
        logger.debug('Density calculated: rho = {}'.format(rho))
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
        energy*1000)
        logger.debug('delta: {}\nbeta: {}\nattenuation length: {}'.format(
        delta, beta, attenuation_length))
    return delta,beta,rho
