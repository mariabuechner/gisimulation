"""
GUI mpodule for gi-simulation.

Usage
#####

python maingui.py [Option...]::
    -d, --debug     show debug logs

@author: buechner_m  <maria.buechner@gmail.com>
"""
DEBUGGING = True
import numpy as np
import sys
import re
from functools import partial
import os.path
import logging
# Set kivy logger console output format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
                              '%(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
sys._kivy_logging_handler = console
# Other imports
import kivy
# Check kivy version
kivy.require('1.10.0')
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.logger import Logger
from kivy.app import App
from kivy.garden.filebrowser import FileBrowser
from kivy.utils import platform
from kivy.core.window import Window
# Properties
from kivy.properties import StringProperty
# UIX
from kivy.factory import Factory as F

# Logging
# Set logger before importing simulation modules (to set format for all)
# Use Kivy logger to handle logging.Logger
logging.Logger.manager.root = Logger  # Makes Kivy Logger root for all
                                      # following loggers

logger = logging.getLogger(__name__)

# gisimulation imports
import kivy_test
import simulation.parser_def as parser_def
import simulation.utilities as utilities
import simulation.check_input as check_input


# Set App Window configuration
Window.maximize()  # NOTE: On desktop platforms only
#Window.set_icon('path\to\icon')

# %% Constants

ERROR_MESSAGE_SIZE = (600, 450)  # absolute
FILE_BROWSER_SIZE = (0.9, 0.9)  # relative

# %% Custom Widgets


# Menu

class MenuSpinnerButton(F.Button):
    """
    Custom button for MenuSpinner, defined in .kv.
    """
    pass

class MenuSpinner(F.Spinner):
    """
    Custom Spinner, uses MenuSpinnerButton.
    """
    option_cls = F.ObjectProperty(MenuSpinnerButton)


# FileBrowser: does not work with golbally modified Label, use custom label
# for everything else
class NonFileBrowserLabel(F.Label):
    """
    Custom Label to avoid conflivt with FileBrowser and allow global changes,
    defined in .kv.
    """
    pass

# Inputs


class FloatInput(F.TextInput):
    """
    TextInput which only allows positive floats.

    Note
    ####

    Adapted from 'https://kivy.org/docs/api-kivy.uix.textinput.html'
    (22.10.2017)

    """

    # Set input pattern
    pattern = re.compile('[^0-9]')  # Allowed input numbers

    def insert_text(self, substring, from_undo=False):
        """
        Overwrites the insert_text function to only accept numbers 0...9
        and '.', and 1 line.
        """
        pattern = self.pattern
        if '.' in self.text:
            s = re.sub(pattern, '', substring)
        else:
            s = '.'.join([re.sub(pattern, '', s) for s in substring.split('.',
                          1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class IntInput(F.TextInput):  # Inherit and just change teyt input???
    """
    TextInput which only allows positive integers, and 1 line.
    """

    pattern = re.compile('[^0-9]')  # Allowed input numbers

    def insert_text(self, substring, from_undo=False):
        """
        Overwrites the insert_text function to only accept numbers 0...9.
        """
        pattern = self.pattern
        s = re.sub(pattern, '', substring)
        return super(IntInput, self).insert_text(s, from_undo=from_undo)


# Error popup


class ErrorDisplay():
    """
    Popup window in case an exception is caught. Displays type of error and
    error message.
    """
    def __init__(self, error_title, error_message):
        """
        Init _OKPopupWindow and open popup.
        """
        error_popup = _OKPopupWindow(error_title, error_message)
        error_popup.popup.open()

class WarningDisplay():
    """
    Popup window in case an exception is caught and user can choose to
    continue. Displays type of error and error message.
    """
    def __init__(self, warning_title, warning_message,
                 overwrite, overwrite_finish,
                 cancel_finish):
        """
        Init _ContinueCancelPopupWindow and open popup.
        """
        self.warning_popup = _ContinueCancelPopupWindow(warning_title,
                                                        warning_message,
                                                        overwrite,
                                                        overwrite_finish,
                                                        cancel_finish)
        self.warning_popup.popup.open()



# Help popup


class LabelHelp(NonFileBrowserLabel):
    """
    Label, but upon touch down a help message appears.
    """
    help_message = StringProperty()

    def on_touch_down(self, touch):
        """
        On touch down a popup window is created, with its title indicating
        the variable to which the help is referring and its help message.

        """
        # If mouse clicked on
        if self.collide_point(touch.x, touch.y):
            window_title = 'Help: {}'.format(self.text)
            help_popup = _OKPopupWindow(window_title, self.help_message)
            help_popup.popup.open()
        # To manage input chain corectly
        return super(LabelHelp, self).on_touch_down(touch)


class ScrollableLabel(F.ScrollView):
    """
    Label is scrolable in y direction. See .kv file for more info.
    """
    text = StringProperty('')

# %% Utiliies


class _OKPopupWindow():
    """
    A popup window containing a label and a button.

    The button closes the window.

    Parameters
    ##########

    title [str]:    title of popup window
    message [str]:  message displayed

    """
    def __init__(self, title, message):
        """
        Init function, creates layout and adds functunality.
        """
        # Custom Window with close button
        popup_content = F.BoxLayout(orientation='vertical',
                                    spacing=10)

        message_label = F.ScrollableLabel(text=message)
        popup_content.add_widget(message_label)
        close_popup_button = F.Button(text='OK')

        popup_content.add_widget(close_popup_button)

        self.popup = F.Popup(title=title,
                             title_size=20,
                             auto_dismiss=False,
                             content=popup_content,
                             size_hint=(None, None),
                             size=ERROR_MESSAGE_SIZE)
                             #size=(_scale_popup_window(message)))
        close_popup_button.bind(on_press=self.popup.dismiss)


class _ContinueCancelPopupWindow():
    """
    A popup window containing a label and 2 buttons (cancel and continue).


    Parameters
    ##########

    title [str]:    title of popup window
    message [str]:  message displayed

    Notes
    #####

    _continue stores the choice, True if continue, False if cancel.

    """
    def __init__(self, title, message,
                 overwrite, overwrite_finish,
                 cancel_finish):
        """
        Init function, creates layout and adds functunality.
        """
        # Init continuation state
        self._continue = False
        self.overwrite = overwrite
        self.overwrite_finish = overwrite_finish
        self.cancel_finish = cancel_finish
        # Custom Window with continue and cancel button
        popup_content = F.BoxLayout(orientation='vertical',
                                    spacing=10)

        message_label = F.ScrollableLabel(text=message)
        popup_content.add_widget(message_label)

        button_layout = F.BoxLayout(spacing=10)
        cancel_popup_button = F.Button(text='Cancel')
        continue_popup_button = F.Button(text='Continue')

        button_layout.add_widget(continue_popup_button)
        button_layout.add_widget(cancel_popup_button)

        popup_content.add_widget(button_layout)

        self.popup = F.Popup(title=title,
                             title_size=20,
                             auto_dismiss=False,
                             content=popup_content,
                             size_hint=(None, None),
                             size=ERROR_MESSAGE_SIZE)

        # Close help window when button 'OK' is pressed
        continue_popup_button.bind(on_press=partial(self.close, True))
        cancel_popup_button.bind(on_press=partial(self.close, False))

        self.popup.bind(on_dismiss=self.finish)  # Wait for dismiss

    def close(self, *args):
        """
        Parameters
        ##########

        continue_ [boolean]:    Continue with action or cancel action

        """
        self._continue = args[0]
        self.popup.dismiss()

    def finish(self, *args):
        if self._continue:
            logger.debug("Overwriting file!")
            self.overwrite()
            logger.debug('... done.')
            self.overwrite_finish()
        else:
            logger.warning("... canceled.")
            self.cancel_finish()


def _load_input_file(input_file_path):
    """
    Load (private, check path, check content)
    """
    input_parameters = dict()
    # Read lines from file
    with open(input_file_path) as f:
        input_lines = f.readlines()
    input_lines = [line.strip() for line in input_lines]  # Strip spaces and \n

    # Find all keys
    key_indices = [i for i, str_ in enumerate(input_lines) if '-' in str_]
    # go from key-entry+1 to next-key-entry-1 to get all values in between
    key_indices.append(len(input_lines))  # Add last entry
    for number_key_index, key_index in enumerate(key_indices[:-1]):
        key = input_lines[key_index]
        value = input_lines[key_index+1:key_indices[number_key_index+1]]
        input_parameters[key] = value
    return input_parameters


def _save_input_file(input_file_path, input_parameters):
    """

    """
    with open(input_file_path, 'w') as f:
        for var_key, value in input_parameters.iteritems():
            f.writelines(var_key+'\n')

            if type(value) is np.ndarray:  # For FOV anf Range
                f.writelines(str(value[0])+'\n')
                f.writelines(str(value[1])+'\n')
            else:
                f.writelines(str(value)+'\n')
    return True


def _collect_input(parameters, ids):
    """
    Converts self.ids from widget to dict and then to struct.

    Parameters
    ##########

    parameters [dict]:      dict of already existing parameters
    ids [widget.ids]

    Returns
    #######

    parameters [dict]

    Notes
    #####

    If input is empty, stores None. Input parameters will be overwritten.

    """
    logger.debug("Converting all label inputs...")
    for var_name, value in ids.iteritems():
#        logger.debug("Key is: {0}.\nValue is: {1}.".format(var_name, value))
        if 'CheckBox' in str(value):
            continue
        elif 'TabbedPanel' in str(value):
            continue
        elif 'Layout' in str(value):
            continue
        elif value.text == '':
                parameters[var_name] = None
        elif 'FloatInput' in str(value):
            parameters[var_name] = float(value.text)
        elif 'IntInput' in str(value):
            parameters[var_name] = int(value.text)
        elif 'TextInput' in str(value):
            parameters[var_name] = value.text
        elif 'Spinner' in str(value):
            parameters[var_name] = value.text
        logger.debug("var_name is: {0}".format(var_name))
        logger.debug("value.text is: {0}".format(value.text))

    # Handel double numeric inputs
    # Spectrum range
    if parameters['spectrum_range_min'] is None or \
            parameters['spectrum_range_max'] is None:
        parameters['spectrum_range'] = None
    else:
        parameters['spectrum_range'] = \
            np.array([parameters['spectrum_range_min'],
                     parameters['spectrum_range_max']],
                     dtype=float)
    del parameters['spectrum_range_min']
    del parameters['spectrum_range_max']
    # FOV
    if parameters['field_of_view_x'] is None or \
            parameters['field_of_view_y'] is None:
        parameters['field_of_view'] = None
    else:
        parameters['field_of_view'] = np.array([parameters['field_of_view_x'],
                                               parameters['field_of_view_y']],
                                               dtype=float)
    del parameters['field_of_view_x']
    del parameters['field_of_view_y']

#    parameters = utilities.Struct(**parameters)  # PAST: converted to dict
    logger.debug("... done.")
    return parameters

# Handle exceptions in popup window


class _IgnoreExceptions(ExceptionHandler):
    """
    Kivy Exception Handler to either display the exception or exit the
    program.

    """
    def handle_exception(self, inst):
        """
        Exception Handler disabeling the automatic exiting after any exception
        occured.
        Now: pass. Python needs to handlen all exceptions now.
        """
        return ExceptionManager.PASS


if not DEBUGGING:
    ExceptionManager.add_handler(_IgnoreExceptions())

# %% Main GUI


class giGUI(F.BoxLayout):
    """
    Main Widget, BoxLayout

    Notes
    #####

    File loading and saving
    Based on "https://kivy.org/docs/api-kivy.uix.filechooser.html"
    (23.10.2017)
    """
    # Global variables (must be kivy properties)
    parameters = F.DictProperty()  # Will be params[var_name] = value
    parser_info = F.DictProperty()  # Will be params[var_name]
                                                  # = [var_key, var_help]
    parser_link = F.DictProperty()  # Will be params[var_key] = var_name

    previous_results = F.DictProperty()

    spectrum_file_path = F.StringProperty()
    spectrum_file_loaded = F.BooleanProperty(defaultvalue=False)
    load_input_file_paths = F.ListProperty()
    save_input_file_path = F.StringProperty()

    setup_components = F.ListProperty()  # Lsit of all components in the setup
    sample_added = False
    available_gratings = F.ListProperty()

    def __init__(self, **kwargs):
        super(giGUI, self).__init__(**kwargs)
        # parser_info[var_name] = [var_key, var_help]
        self.parser_info = \
            parser_def.get_arguments_info(parser_def.input_parser())
        for var_name, value in self.parser_info.iteritems():
            self.parser_link[value[0]] = var_name
        # parameters
        self.parameters = _collect_input(self.parameters, self.ids)
        self.parameters['spectrum_file'] = None
        for var_name, value in self.parameters.iteritems():
            logger.debug(var_name)
        # Components trackers
        self.setup_components = ['Source', 'Detector']
        # Avail fixed gratings
        if self.ids.beam_geometry.text == 'parallel':
            self.available_gratings = ['G1', 'G2']
        else:
            self.available_gratings = ['G0', 'G1', 'G2']

    # General simulation functions

    def check_general_input(self):
        """
        """
        try:
            # Convert input
            self.parameters = _collect_input(self.parameters, self.ids)

            # Check values
            # Are required (in parser) defined?
            if not self.parameters['pixel_size']:
                error_message = "Input arguments missing: 'pixel_size' " \
                                "('-pxs')."
                logger.error(error_message)
                raise check_input.InputError(error_message)
            if self.parameters['field_of_view'] is None:
                error_message = "Input argument missing: 'field_of_view' " \
                                "('-fov')."
                logger.error(error_message)
                raise check_input.InputError(error_message)
            else:
                if not all(self.parameters['field_of_view'] > 0):
                    error_message = "FOV must be at least (1, 1)."
                    logger.error(error_message)
                    raise check_input.InputError(error_message)
            if not self.parameters['design_energy']:
                error_message = "Input argument missing: 'design_energy' " \
                                "('-e')."
                logger.error(error_message)
                raise check_input.InputError(error_message)
            # Check rest
            self.parameters = check_input.general_input(self.parameters)

            # Update widget content
            self._set_widgets(self.parameters, from_file=False)

        except check_input.InputError as e:
            ErrorDisplay('Input Error', str(e))

    def calculate_geometry(self):
        """
        """
        self.ids.result_tabs.switch_to(self.ids.geometry_results)

    def calculate_visibility(self):
        """
        """
        self.ids.result_tabs.switch_to(self.ids.visibility_results)

    # Manage global variables and widget behavior

    def on_spectrum_file_path(self, instance, value):
        """
        When spectrum_file_oath changes, set parameters and check load status.
        """
        if value:
            self.spectrum_file_loaded = True
            self.parameters['spectrum_file'] = self.spectrum_file_path
        else:
            self.spectrum_file_loaded = False
            self.parameters['spectrum_file'] = None

    def on_load_input_file_paths(self, instance, value):
        """
        Notes
        #####

        input_parameters [dict]:    input_parameters[var_key] = str(value)

        """
        # Do for all files in load_input_file_paths and merge results.
        # Later fiels overwrite first files.
        for input_file in value:
            logger.debug("Loading input from file at: {0}".format(input_file))
            input_parameters = _load_input_file(input_file)
        # Set widget content
        self._set_widgets(input_parameters, from_file=True)

    def on_save_input_file_path(self, instance, value):
        """
        Notes
        #####

        self.parameters [dict]:     widget_parameters[var_name] = value

        """
        if self.save_input_file_path != '':  # e.g. after reset.
            # Check input
            self.parameters = _collect_input(self.parameters, self.ids)
            # Select parameters to save
            logger.debug("Collecting all paramters to save...")
            input_parameters = dict()
            for var_name, var_value in self.parameters.iteritems():
                if var_name in self.parser_info and var_value is not None:
                    var_key = self.parser_info[var_name][0]
                    input_parameters[var_key] = var_value
            # Save at save_input_file_path (=value)
            logger.debug('... done.')
            logger.debug("Saving input to file...")
            if os.path.isfile(value):
                # File exists
                logger.warning("File '{0}' already exists!".format(value))
                warning = WarningDisplay("File already exists!",
                                         "Do you want to overwrite it?",
                                         partial(_save_input_file,
                                                 value,
                                                 input_parameters),
                                         self.overwrite_save,
                                         self.cancel_save)
            else:
                # File new
                _save_input_file(value, input_parameters)
                logger.debug('... done.')
                self.dismiss_popup()

    def overwrite_save(self):
        self.dismiss_popup()
        self.save_input_file_path = ''  # Reset to allow next save at same file

    def cancel_save(self):
        self.save_input_file_path = ''  # Reset to allow next save at same file

    # Menu spinners

    def on_save_spinner(self, spinner):
        selected = spinner.text
        spinner.text = 'Save...'
        if selected == 'Input file...':
            self.show_input_save()
        elif selected == 'Results...':
            self.save_results()

    def on_help_spinner(self, spinner):
        selected = spinner.text
        spinner.text = 'Help...'
        if selected != 'Help...':
            if selected == 'Spectrum file':
                help_message = ("File format:\n"
                                "energy,photons\n"
                                "e1,p1\n"
                                "e2,p2\n"
                                ".,.\n"
                                ".,.\n"
                                ".,.")
            if selected == 'Input file':
                help_message = ("File type: .txt\n"
                                "Can use multiple files, in case of double "
                                "entries, the last file overwrites the "
                                "previous one(s).\n"
                                "File layout:        Example:\n"
                                "ArgName1                -sr\n"
                                "ArgValue1               100\n"
                                "ArgName2                -p0\n"
                                "ArgValue2               2.4\n"
                                "    .                    .\n"
                                "    .                    .\n"
                                "    .                    .")
            help_popup = _OKPopupWindow("Help: [0]".format(selected),
                                        help_message)
            help_popup.popup.open()

    # Conditional input rules

    def on_geometry(self):
        """
        Set sample position options and activate required gratings.
        """
        # Remove sample if it was set
        if 'Sample' in self.setup_components:
                self.ids.add_sample.active = False
        # Required gratings
        if self.ids.geometry.text != 'free':
            # G1 and G2 required
            self.ids.g1_set.active = True
            self.ids.g2_set.active = True
            # Sample relative to G1
            self.ids.sample_relative_to.text = 'G1'
            self.ids.sample_relative_to.values = ['G1']
        # Sample position
        else:
            # Reset to 'free' (same as start)
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after']
            self.ids.sample_relative_to.text = 'Source'
            if 'Sample' not in self.setup_components:
                self.ids.sample_relative_to.values = self.setup_components
            else:
                self.ids.sample_relative_to.values = \
                    list(self.setup_components).remove('Sample')
        # GI cases
        if self.ids.geometry.text == 'conv':
            self.ids.sample_relative_position.text = 'before'
            self.ids.sample_relative_position.values = ['before']
            if self.ids.beam_geometry.text == 'parallel':
                self.ids.sample_relative_position.values = ['after', 'before']
        elif self.ids.geometry.text == 'inv':
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after']
        else:
            # Symmetrical case
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after', 'before']

    def on_beam_geometry(self):
        """
        Set and deactivate required gratings.
        """
        # Remove sample if it was set
        if 'Sample' in self.setup_components:
                self.ids.add_sample.active = False
        if self.ids.beam_geometry.text == 'parallel':
            # Change GI geometry text
            if self.ids.geometry.text == 'sym' or \
              self.ids.geometry.text == 'inv':
                # Mode changes, reset GI geometry
                self.ids.geometry.text = 'free'
            # Set available and deactive gratings
            self.ids.g0_set.active = False
            self.available_gratings = ['G1', 'G2']
#            if self.ids.fixed_grating.text == 'G0':
#                self.ids.fixed_grating.text = 'G1'
        else:
            # Update geometry conditions for cone beam
            self.on_geometry()
            self.available_gratings = ['G0', 'G1', 'G2']
        self.ids.fixed_grating.text = 'Choose fixed grating...'

    def on_setup_components(self, instance, value):
        # On change in component list, update sample_relative_to spinner text
        if not self.sample_added:
            self.ids.sample_relative_to.text = self.setup_components[0]


    def on_grating_checkbox_active(self, state, checkbox_name):
        if state:
            self.setup_components.append(checkbox_name)
            self.setup_components.sort()
            # After sort, switch Source and Detector
            self.setup_components[0], self.setup_components[-1] = \
              self.setup_components[-1], self.setup_components[0]
        else:
            self.setup_components.remove(checkbox_name)
            # Also uncheck sample_added
            self.ids.add_sample.active = False
            self.ids.sample_relative_to.text = self.setup_components[0]
        logger.debug("Current setup consists of: {0}"
                     .format(self.setup_components))

    def on_sample_relative_to(self):
        if self.ids.sample_relative_to.text == 'Source':
            self.ids.sample_relative_position.values = ['after']
            self.ids.sample_relative_position.text = 'after'
        elif self.ids.sample_relative_to.text == 'Detector':
            self.ids.sample_relative_position.values = ['before']
            self.ids.sample_relative_position.text = 'before'
        elif self.ids.geometry.text == 'free':
            self.ids.sample_relative_position.values = ['after', 'before']

    def on_sample_checkbox_active(self, state):
        if state:
            # Add sample at right position
            self.sample_added = True
            reference_index = \
                self.setup_components.index(self.ids.sample_relative_to.text)
            if self.ids.sample_relative_position.text == 'after':
                self.setup_components.insert(reference_index+1, 'Sample')
            else:
                self.setup_components.insert(reference_index, 'Sample')
        else:
            # Remove sample, in case that geometry is changing
            self.setup_components.remove('Sample')
            self.sample_added = False

        logger.debug("Current setup consists of:\n{0}"
                     .format(self.setup_components))

    # Loading and saving files

    def dismiss_popup(self):
        self._popup.dismiss()

    def _fbrowser_canceled(self, instance):
        logger.debug('FileBrowser canceled, closing itself.')
        self.dismiss_popup()

    # Spectrum

    def show_spectrum_load(self):
        """
        Upon call, open popup with file browser to load spectrum_file_path
        """
        # Define browser
        spectra_path = os.path.join(os.path.dirname(os.path.
                                                    realpath(__file__)),
                                    'data', 'spectra')
        browser = FileBrowser(select_string='Select',
                              path=spectra_path,  # Folder to open at start
                              filters=['*.csv','*.txt'])
        browser.bind(on_success=self._spectra_fbrowser_success,
                     on_canceled=self._fbrowser_canceled)

        # Add to popup
        self._popup = F.Popup(title="Load spectrum", content=browser,
                              size_hint=FILE_BROWSER_SIZE)
        self._popup.open()

    def _spectra_fbrowser_success(self, instance):
        self.spectrum_file_path = instance.selection[0]
        logger.debug("Spectrum filepath is: {}"
                     .format(self.spectrum_file_path))
        self.dismiss_popup()

    # Input file

    # Load input file

    def show_input_load(self):
        """
        Upon call, open popup with file browser to load input file location.
        """
        # Define browser
        input_path = os.path.join(os.path.dirname(os.path.
                                                    realpath(__file__)),
                                    'data')
        browser = FileBrowser(select_string='Select',
                              multiselect=True,
                              path=input_path,  # Folder to open at start
                              filters=['*.txt'])
        browser.bind(on_success=self._input_load_fbrowser_success,
                     on_canceled=self._fbrowser_canceled)

        # Add to popup
        self._popup = F.Popup(title="Load input file", content=browser,
                              size_hint=FILE_BROWSER_SIZE)
        self._popup.open()

    def _input_load_fbrowser_success(self, instance):
        self.load_input_file_paths = instance.selection
        logger.debug("{0} input files loaded."
                     .format(len(self.load_input_file_paths)))
        self.dismiss_popup()


    # Save input file

    def show_input_save(self):
        """
        Upon call, open popup with file browser to save input file.
        """
        # Define browser
        input_path = os.path.join(os.path.dirname(os.path.
                                                    realpath(__file__)),
                                    'data')
        browser = FileBrowser(select_string='Save',
                              path=input_path,  # Folder to open at start
                              filters=['*.txt'])
        browser.bind(on_success=self._input_save_fbrowser_success,
                     on_canceled=self._fbrowser_canceled)

        # Add to popup
        self._popup = F.Popup(title="Save input file", content=browser,
                              size_hint=FILE_BROWSER_SIZE)
        self._popup.open()

    def _input_save_fbrowser_success(self, instance):
        filename = instance.filename
        # Check extension
        if filename.split('.')[-1] == instance.filters[0].split('.')[-1]:
            # Correct extention
            file_path = os.path.join(instance.path, filename)
        elif filename.split('.')[-1] == '':
            # Just '.' set
            file_path = os.path.join(instance.path, filename+'txt')
        elif filename.split('.')[-1] == filename:
            # Not extention set
            file_path = os.path.join(instance.path, filename+'.txt')
        else:
            # Wrong file extention
            error_message = ("Input file must be of type '{0}'"
                             .format(instance.filters[0]))
            logger.error(error_message)
            ErrorDisplay('Saving input file: Wrong file extention.',
                         error_message)
            return
        logger.debug("Save input to file: {0}"
                     .format(file_path))
        self.save_input_file_path = file_path

    # Results

    # Save results

    def save_results(self):
         logger.info("Saving results.")

    # Set widgete values
    def _set_widgets(self, input_parameters, from_file):
        """

        if from file:

            input_parameters [dict]:    input_parameters[var_key] = value

        if from app (not from file):

            input_parameters [dict]:    parameters[var_name] = value

        self.parameters [dict]:         widget_parameters[var_name] = value
        self.parser_link [dict]:        parser_link[var_key] = var_name
        self.parser_info [dict]:        parser_info[var_name] = [var_key,
                                                                 var_help]
        """
        if from_file:
            for var_key, value_str in input_parameters.iteritems():
                logger.debug("var_key is {0}".format(var_key))
                logger.debug("value_str is {0}".format(value_str))
                if var_key not in self.parser_link:
                    # Input key not implemented in parser
                    logger.warning("Key '{0}' read from input file, but not "
                                   "defined in parser. Skipping..."
                                   .format(var_key))
                    continue
                var_name = self.parser_link[var_key]
                logger.debug("var_name is {0}".format(var_name))
                if var_name not in self.parameters:
                    # Input key not implemented in GUI
                    logger.warning("Key '{0}' with name '{1}' read from input "
                                   "file, but not defined in App. Skipping..."
                                   .format(var_key, var_name))
                    continue
                # Set input values to ids.texts
                if var_name == 'spectrum_range':
                    self.ids['spectrum_range_min'].text = value_str[0]
                    self.ids['spectrum_range_max'].text = value_str[1]
                elif var_name == 'field_of_view':
                    self.ids['field_of_view_x'].text = value_str[0]
                    self.ids['field_of_view_y'].text = value_str[1]
                else:
                    logger.debug("Setting text of widget '{0}' to: {1}"
                                 .format(var_name, value_str[0]))
                    self.ids[var_name].text = value_str[0]
        else:
            for var_name, value in input_parameters.iteritems():
                # Skip all the not-set parameters
                if value is not None:
                    logger.debug("var_name is {0}".format(var_name))
                    logger.debug("value is {0}".format(value))
                    if var_name not in self.parser_info:
                        # Input variable not implemented in parser
                        logger.warning("Parameter '{0}' read from app, but not "
                                       "defined in parser. Skipping..."
                                       .format(var_name))
                        continue
                    var_key = self.parser_info[var_name][0]
                    logger.debug("var_key is {0}".format(var_key))
                    # Set input values to ids.texts
                    if var_name == 'spectrum_range':
                        self.ids['spectrum_range_min'].text = str(value[0])
                        self.ids['spectrum_range_max'].text = str(value[1])
                    elif var_name == 'field_of_view':
                        self.ids['field_of_view_x'].text = str(value[0])
                        self.ids['field_of_view_y'].text = str(value[1])
                    else:
                        logger.debug("Setting text of widget '{0}' to: {1}"
                                     .format(var_name, value))
                        self.ids[var_name].text = str(value)

    # Utility functions

    def calc_boxlayout_height(self, childen_height, boxlayout):
        """
        Calculates the height of a boxlayout, in case it is only filled with
        childen of height = children_height.

        Parameters
        ##########

        childen_height [pxls]
        boxlayout [BoxLayout]

        Returns
        #######

        boxlayout_height [pxls]

        """
        boxlayout_height = (childen_height + boxlayout.spacing \
                            + boxlayout.padding[1] + boxlayout.padding[3]) \
                            * len(boxlayout.children)
        return boxlayout_height




# %% Main App


class giGUIApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return giGUI()  # Main widget, root



# %% Main


if __name__ == '__main__':
    giGUIApp().run()
