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
    multiline = False  # On enter, loose focus on textinput
    write_tab = False  # On tab, loose focus on textinput

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
    multiline = False  # On enter, loose focus on textinput
    write_tab = False  # On tab, loose focus on textinput

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
        Init PopupWindow and open popup.
        """
        error_popup = _PopupWindow(error_title, error_message)
        error_popup.popup.open()

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
            help_popup = _PopupWindow(window_title, self.help_message)
            help_popup.popup.open()
        # To manage input chain corectly
        return super(LabelHelp, self).on_touch_down(touch)


class ScrollableLabel(F.ScrollView):
    """
    Label is scrolable in y direction. See .kv file for more info.
    """
    text = StringProperty('')

# %% Utiliies


class _PopupWindow():
    """
    A popup window containing a label and a button.
    The size of the window is determined by the number of lines and the
    length of the longest line of the help message.
    The button closes the window.

    Parameters
    ##########

    title [str]:    titel of popup window
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
                             size=(600, 450))
                             #size=(_scale_popup_window(message)))
        # Close help window when button 'OK' is pressed
        close_popup_button.bind(on_press=self.popup.dismiss)

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


def _save_input_file(input_file_path, parameters):
    """
    """
#    for var_key, value in key_parameters.iteritem():
#        print key in line
#        print value in next line
    pass

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
        logger.debug("Key is: {0}.\nValue is: {1}.".format(var_name, value))
        if 'CheckBox' in str(value):
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
#    # FOV (FUTURE)
#    if parameters['field_of_view_x'] is None or \
#            parameters['field_of_view_y'] is None:
#        parameters['spectrum_range'] = None
#    else:
#        parameters['field_of_view'] = np.array([parameters['field_of_view_x'],
#                                               parameters['field_of_view_y']],
#                                               dtype=float)
#    del parameters['field_of_view_x']
#    del parameters['field_of_view_y']

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
#    parameters = dict()  # Will be params[var_name] = value

    spectrum_file_path = F.StringProperty()
    spectrum_file_loaded = F.BooleanProperty(defaultvalue=False)
    load_input_file_paths = F.ListProperty()


    def __init__(self, **kwargs):
        super(giGUI, self).__init__(**kwargs)
        # parser_info[var_name] = [var_key, var_help]
        self.parser_info = \
            parser_def.get_arguments_info(parser_def.input_parser())
        for var_name, value in self.parser_info.iteritems():
            self.parser_link[value[0]] = var_name
        # Init self.parameters
        self.parameters = _collect_input(self.parameters, self.ids)

    # General simulation functions

    def check_general_input(self):
        # Convert input
        self.parameters = _collect_input(self.parameters, self.ids)
        logger.debug(self.parameters['design_energy'])

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
        self.parameters [dict]:     widget_parameters[var_name] = value
        self.parser_link [dict]:    parser_link[var_key] = var_name

        """
        # Do for all files in load_input_file_paths and merge results.
        # Later fiels overwrite first files.
        for input_file in value:
            logger.debug("Loading input from file at: {0}".format(input_file))
            input_parameters = _load_input_file(input_file)
        # Set widget content
        for var_key, value_str in input_parameters.iteritems():
            logger.debug("var_key is {0}".format(var_key))
            logger.debug("value_str is {0}".format(value_str))
            if var_key not in self.parser_link:
                # Input key not implemented in parser
                logger.warning("Key '{0}' read from input file, but not "
                               "defined in parser.".format(var_key))
                continue
            var_name = self.parser_link[var_key]
            logger.debug("var_name is {0}".format(var_name))
            if var_name not in self.parameters:
                # Input key not implemented in GUI
                logger.warning("Key '{0}' with name '{1}' read from input file, "
                               "but not defined in App.".format(var_key, var_name))
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



    def on_save_spinner(self, spinner):
        selected = spinner.text
        spinner.text = 'Save...'
        if selected == 'Input file...':
            self.save_input()
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
            help_popup = _PopupWindow("Help: [0]".format(selected),
                                      help_message)
            help_popup.popup.open()

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
                              size_hint=(0.9, 0.9))
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
                              size_hint=(0.9, 0.9))
        self._popup.open()

    def _input_load_fbrowser_success(self, instance):
        self.load_input_file_paths = instance.selection
        logger.debug("{0} input files loaded."
                     .format(len(self.load_input_file_paths)))
        self.dismiss_popup()


    # Save input file

    def save_input(self):
         logger.info("Saving info file.")

    # Results

    # Save results

    def save_results(self):
         logger.info("Saving results.")

    # Utility functions

    def exit_app(self):
        logger.info("Exiting App...")
        sys.exit(2)

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

    # When app window is closed
    def on_stop(self):
        logger.info("Exiting App...")
        sys.exit(2)


# %% Main


if __name__ == '__main__':
    giGUIApp().run()
