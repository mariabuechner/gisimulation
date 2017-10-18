from setuptools import setup

setup(name='gisimulation',
      version='0.1',
      description='Simulation toolbox for x-ray grating interferometry',
      url='https://github.com/mariabuechner/gisimulation',
      author='Maria Buechner',
      author_email='maria.buechner@gmail.com',
	  license='MIT',
      packages=['gisimulation'],
	  install_requires=[
          'logging',
		  'numpy',
		  'sys',
      ],
      zip_safe=False)