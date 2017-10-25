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
# ActionBar
from kivy.base import runTouchApp
from kivy.uix.actionbar import ActionBar
from kivy.uix.actionbar import ActionView
from kivy.uix.actionbar import ActionButton
from kivy.uix.actionbar import ActionPrevious
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
    """
    pass

class MenuSpinner(F.Spinner):
    """
    """
    option_cls = F.ObjectProperty(MenuSpinnerButton)


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


class LabelHelp(F.Label):
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
                             auto_dismiss=False,
                             content=popup_content,
                             size_hint=(None, None),
                             size=(550, 300))
                             #size=(_scale_popup_window(message)))
        # Close help window when button 'OK' is pressed
        close_popup_button.bind(on_press=self.popup.dismiss)


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
    for key, value in ids.iteritems():
#        logger.debug("Key is: {0}.\nValue is: {1}.".format(key, value))
        if 'CheckBox' in str(value):
            continue
        elif value.text == '':
                parameters[key] = None
        elif 'FloatInput' in str(value):
            parameters[key] = float(value.text)
        elif 'IntInput' in str(value):
            parameters[key] = int(value.text)
        elif 'TextInput' in str(value):
            parameters[key] = value.text

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
    parameters = F.DictProperty()
    spectrum_file_path = F.StringProperty()
    spectrum_file_loaded = F.BooleanProperty(defaultvalue=False)


    # Manage global variables and widget behavior

    def on_spectrum_file_path(self, instance, value):
        """
        Option: if parameters global, set spectrum_file here
        ALSO: consider dict for parameters...
        """
        if value:
            self.spectrum_file_loaded = True
            self.parameters['spectrum_file'] = self.spectrum_file_path
        else:
            self.spectrum_file_loaded = False
            self.parameters['spectrum_file'] = None

    def on_save_spinner(self, spinner):
        selected = spinner.text
        spinner.text = 'Save...'
        if selected == 'Input file...':
            self.save_input()
        elif selected == 'Results...':
            self.save_results()

    # Loading and saving files

    def dismiss_popup(self):
        self._popup.dismiss()

    # Spectrum

    def show_spectrum_load(self):
        """
        Upon call, open popup with file browser to load spectrum_file_path
        """
        # Define browser
        spectra_path = os.path.join(os.path.dirname(os.path.
                                                    realpath(__file__)),
                                    'data', 'spectra')
        logger.debug("Start path is {}".format(spectra_path))
        browser = FileBrowser(select_string='Select',
                              path=spectra_path,  # Folder to open at start
                              filters=['*.csv','*.txt'])
        browser.bind(on_success=self._spectra_fbrowser_success,
                     on_canceled=self._fbrowser_canceled)

        # Add to popup
        self._popup = F.Popup(title="Load spectrum", content=browser,
                              size_hint=(0.9, 0.9))
        self._popup.open()

    def _fbrowser_canceled(self, instance):
        logger.debug('FileBrowser canceled, closing itself.')
        self.dismiss_popup()

    def _spectra_fbrowser_success(self, instance):
        logger.debug("type of selection is {}".format(instance.selection[0]))
        self.spectrum_file_path = instance.selection[0]
        logger.debug("Spectrum filepath is: {}"
                     .format(self.spectrum_file_path))
        self.dismiss_popup()

    # Load input file

    def load_input(self):
        logger.info("Loading from info file.")

    # Save input file

    def save_input(self):
         logger.info("Saving info file.")

    # Save results

    def save_results(self):
         logger.info("Saving results.")


    # General functions

    def check_general_input(self):
        # Convert input
        self.parameters = _collect_input(self.parameters, self.ids)
        print(self.parameters)

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
