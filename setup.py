########################################################################
#
# setup.py
#
# setup file
#
# Author: Maria Buechner
#
# History:
# 28.10.2016: started
#
########################################################################

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='simulation',
    description='Simulation toolbox for x-ray grating interferometry',
    long_description=long_description,
    url="https://github.com/mariabuechner/gi_simulation",
    author='Maria Buechner',
    author_email='maria.buechner@gmail.com',
    license="MIT",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'numpy',
        'scipy',
        'h5py',
    ],
)
