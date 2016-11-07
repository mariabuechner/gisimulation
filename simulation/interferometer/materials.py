"""
Module to retrieve the complexe refractive index: n = 1 - delta - i*beta and
density rho .

With delta:

    real part of index of refraction, with the resulting attenuation
    coefficient mu:
        mu = 4*pi*delta/lambda

With beta:

    complex part of index of refraction

With rho: density in [g/cm3]


The python package 'nist_lookup' (git@git.psi.ch:tomcat/nist_lookup.git) is
used to retrieve delta and beta. This requires the input pf the dentisty


"""
import logging
import nist_lookup.xraydb_plugin as xdb
import urllib2
import numpy as np
import csv
logger = logging.getLogger(__name__)




def delta_beta(material, energy, rho=0):
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
    if rho is not 0:
        [delta, beta, attenuation_length] = xdb.xray_delta_beta(material, rho,
        energy)
        return delta,beta
    else:
        density_dict = get_densities()
        materials = density_dict.keys()
        rhos = density_dict.values()

def get_densities():
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

def rho(material_name):
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
