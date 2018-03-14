"""
Module to run grating interferometer simulation and metrics calculation

@author: buechner_m <maria.buechner@gmail.com>
"""
import logging
import numpy as np
import scipy.io
import sys
import os
# gisimulation modules
import simulation.utilities as utilities
import simulation.parser_def as parser_def
import simulation.check_input as check_input
import interferometer.geometry as geometry
# import materials
# import geometry
# import gratings
logger = logging.getLogger(__name__)

# %% Constants
NUMERICAL_TYPE = np.float


# %% Functions

# #############################################################################
# Calculations ################################################################


def calculate_geometry(parameters, parser_info, results):
    """
    Calculate the GI geometry based on the set input parameters.

    Parameters
    ==========

    parameters [dict]
    parser_info [dict]
    results [dict]

    Notes
    =====

    parameters and results are passed as references, thus the function changes
    them 'globally'

    """
    # Check input
    logger.info("Checking geometry input...")
    try:
        check_input.geometry_input(parameters, parser_info)
    except check_input.InputError:
        logger.info("Command line error, exiting...")
        sys.exit(2)  # 2: command line syntax errors
    logger.info("... done.")

    # Calculate
    logger.info("Calculationg geometry...")
    gi_geometry = geometry.Geometry(parameters)
    results['geometry'] = gi_geometry.results
    parameters = gi_geometry.update_parameters()
    logger.info("... done.")

# #############################################################################
# Input/Results i/o ###########################################################


def collect_input(parameters, parser_info):
    """
    Selects only input parameters defined in parser from all available
    parameters.

    Parameters
    ==========

    parameters [dict]:      parameters[var_name] = value
    ids [dict]:             ids[var_name] = var_value
    parser_info [dict]:     parser_info[var_name] = [var_key, var_help]

    Returns
    =======

    input_parameters [dict]:    input_parameters[var_key] = var_value

    """
    # Select input parameters to save
    logger.debug("Collecting all paramters to save...")
    input_parameters = dict()
    variables = [(var_name, var_value) for var_name, var_value
                 in parameters.iteritems()
                 if (var_name in parser_info and var_value is not None)]
    for var_name, var_value in variables:
        var_key = parser_info[var_name][0]
        input_parameters[var_key] = var_value
    # Save at save_input_file_path (=value)
    logger.debug('... done.')

    return input_parameters


def save_input(input_file_path, input_parameters, overwrite=False):
    """
    Save string parameter keys and values (as strings) to input file.

    Parameters
    ==========

    input_file_path [str]:      file path to (nes) input file, including name.
    input_parameters [dict]:    input_parameters['var_key'] = var_value
    overwrite [boolean]:        force overwrite without promt (when called
                                from GUI)

    Notes
    =====

    Skip false flags (--)
    Only save var_key if true flags

    """
    continue_ = True
    if os.path.isfile(input_file_path) and not overwrite:
        # File exists, promt decision
        logger.warning("File '{0}' already exists!".format(input_file_path))
        continue_ = _overwrite_file("File '{0}' already exists! Do you want "
                                    "to overwrite it?".format(input_file_path))
    if continue_ or overwrite:
        logger.info("Writing input file...")
        with open(input_file_path, 'w') as f:
            for var_key, value in input_parameters.iteritems():
                if value is not False:
                    f.writelines(var_key+'\n')
                    if type(value) is np.ndarray:  # For FOV and Range
                        f.writelines(str(value[0])+'\n')
                        f.writelines(str(value[1])+'\n')
                    elif value is not True:
                        f.writelines(str(value)+'\n')
        logger.info("... done.")
    else:
        logger.info("Do not overwrite, abort save.")
        logger.warning("Input paramters are NOT saved.")


def save_results(results_dir_path, results, overwrite=False):
    """
    Save results dict to folder.

    Parameters
    ==========

    results_dir_path [str]:     folder path to store /mat files in
    results [dict]
    overwrite [boolean]:        force overwrite without promt (when called
                                from GUI)

    Notes
    =====

    results_dir_path:  path/folder_name

    Structure results:
        results['input'] = dict of input parameters
        results['geometry'] = dict of geometry parameters
        results[...] = dict of ...

    Save as: at path/
        - folder name
            - input dict as foldername_input.text (via save_input)
            - geometry.mat: all keys/values from dict (here: geometry)
            - ... .mat:

    Formats:

        saves booleans (True/False) as 'True'/'False'
        saves None as []

    """
    continue_ = True
    if os.path.isdir(results_dir_path) and not overwrite:
        # Folder exists, promt decision
        logger.warning("Folder '{0}' already exists!".format(results_dir_path))
        continue_ = _overwrite_file("Folder '{0}' already exists! Do you want "
                                    "to overwrite it?"
                                    .format(results_dir_path))
    if continue_ or overwrite:
        if not os.path.exists(results_dir_path):
            os.makedirs(results_dir_path)

        logger.info("Writing results folder...")

        for sub_dict_name in results.keys():
            if not results[sub_dict_name]:
                continue  # Skip empty dicts
            elif sub_dict_name == 'input':
                # Save input
                input_file = os.path.basename(results_dir_path)+'_input.txt'
                input_file_path = os.path.join(results_dir_path, input_file)
                save_input(input_file_path, results['input'], True)
            else:
                # Save sub dictionaries in single .mat (from single dict)
                file_path = os.path.join(results_dir_path,
                                         sub_dict_name+'.mat')
                # None to [] to store on .mat
                result_dict = {key: value if value is not None else []
                               for key, value
                               in results[sub_dict_name].iteritems()}
                # Change True/False to True'/'False'
                true_booleans = [key for key, var in result_dict.iteritems()
                                 if var is True]
                false_booleans = [key for key, var in result_dict.iteritems()
                                  if var is False]
                result_dict = {key: value
                               if key not in true_booleans else 'True'
                               for key, value in result_dict.iteritems()}
                result_dict = {key: value
                               if key not in false_booleans else 'False'
                               for key, value in result_dict.iteritems()}

                scipy.io.savemat(file_path, result_dict)
        # If nothing was saved
        if not os.listdir(results_dir_path):
            logger.info("No results to be saved, aborting...")
            os.rmdir(results_dir_path)
        else:
            logger.info("... done.")
    else:
        logger.info("Do not overwrite, abort save.")
        logger.warning("Results paramters are NOT saved.")


def reset_results():
    """
    Returns an empty dictionary based on the results structure.

    Returns
    =======

    results [dict]

    Notes
    =====

    results = dict()
    results['geometry'] = dict()
    results['input'] = dict()
    # results['analytical'] = dict()
    # results['simulation'] = dict()

    """
    results = dict()
    results['geometry'] = dict()
    results['input'] = dict()
    # results['analytical'] = dict()
    # results['simulation'] = dict()
    return results

# #############################################################################
# Utilities ###################################################################


def compare_dictionaries(a, b):
    """
    Compares if 2 dictionaries are equal (keys and values).

    Parameters
    ==========

    a [dict]
    b [dict]

    Returns
    =======

    True if both dicts have the same keys and the same values, else False.

    """
    if len(a) != len(b):
        return False
    for key, value in a.iteritems():
        if key not in b:
            return False
        elif np.array_equal(value, b[key]):
            return True
        else:
            return False


def _overwrite_file(message, default_answer='n'):
    """
    Promt user to enter y [yes] or n [n] when potentially overwriting a file.
    Default answer is n [no]. Returns bool to continue or not.

    Parameters
    ==========

    message [str]
    default_answer [str] (default: n [no], if user hits enter)

    Returns
    =======

    [boolean]:      True if continue and overwrite

    """
    valid = {"y": True, "n": False}
    if default_answer is None:
        prompt = " [y/n] "
    elif default_answer == "y":
        prompt = " [Y/n] "
    elif default_answer == "n":
        prompt = " [y/N] "
    else:
        default_answer = 'n'
        prompt = " [y/N] "
        logger.warning("Invalid default answer, setting to 'n' [no].")

    while True:
        sys.stdout.write(message + prompt)
        answer = raw_input().lower()
        if default_answer is not None and answer == '':
            return valid[default_answer]
        elif answer in valid:
            return valid[answer]
        else:
            sys.stdout.write("Please choose 'y' [yes] or 'n' [no].\n")

# %% Main

if __name__ == '__main__':
    # Parse from command line

    parser = parser_def.input_parser(NUMERICAL_TYPE)
    parser_info = parser_def.get_arguments_info(parser)

    parameters = vars(parser.parse_args())

    results = reset_results()

    # Config logger output
    logger_level = utilities.get_logger_level(parameters['verbose'])
    # Set logger config
    logging.basicConfig(level=logger_level, format='%(asctime)s - %(name)s '
                        '- %(levelname)s - '
                        '%(message)s', disable_existing_loggers=False)

#    # Check input
#    try:
#        parameters = check_input._test_check_parser(parameters)
#    except check_input.InputError:
#        logger.info("Command line error, exiting...")
#        sys.exit(2)  # 2: command line syntax errors

    # Calc geometries (params check inside)
    calculate_geometry(parameters, parser_info, results)
