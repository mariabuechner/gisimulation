"""
GUI mpodule for gi-simulation.

Usage
#####

python maingui.py [Option...]::
    -d, --debug     show debug logs

@author: buechner_m  <maria.buechner@gmail.com>
"""
import numpy as np
import sys
import re
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
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.logger import Logger
from kivy.app import App
from kivy.core.window import Window
# Properties
from kivy.properties import StringProperty
# UIX
from kivy.factory import Factory as F

# Parser
import argparse
parser = argparse.ArgumentParser(description="Set verbose level for debugger.")
parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity level. 'v': error, "
                        "'vv': warning,"
                        "'vvv': info (None=default), 'vvvv': debug")

# Logging
# Set logger before importing simulation modules (to set format for all)
# Use Kivy logger to handle logging.Logger
logging.Logger.manager.root = Logger  # Makes Kivy Logger root for all
                                      # following loggers

logger = logging.getLogger(__name__)

# gisimulation imports
import kivy_test
import simulation.utilities as utilities
import simulation.check_input as check_input


# Set App Window configuration
Window.maximize()  # NOTE: On desktop platforms only
#Window.set_icon('path\to\icon')

# %% Constants
POPUP_WINDOW_SIZE = [550, 70]  # Width: 600 per line, Height: 80 per line
POPUP_WINDOW_MAX_LETTERS = 80.0  # max 80 letters per line
LINE_HEIGHT = 35

# %% Custom Widgets


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


class PopupWindow():
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
        popup_window = F.BoxLayout(orientation='vertical')
        message_label = F.Label(text=str(message),
                                size_hint=(1, None),
                                height=LINE_HEIGHT * (message.count('\n')+1))
        popup_window.add_widget(message_label)
        close_popup_button = F.Button(text='OK')
        popup_window.add_widget(close_popup_button)

        self.popup = F.Popup(title=title,
                             auto_dismiss=False,
                             content=popup_window,
                             size_hint=(None, None),
                             size=(_scale_popup_window(message)))
        # Close help window when button 'OK' is pressed
        close_popup_button.bind(on_press=self.popup.dismiss)


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
            self.help_popup = PopupWindow(window_title, self.help_message)
            self.help_popup.popup.open()
        # To manage input chain corectly
        return super(LabelHelp, self).on_touch_down(touch)

# %% Utiliies


def _convert_input(ids):
    """
    Converts self.ids from widget to dict and then to struct.

    Parameters
    ##########

    ids [widget.ids]

    Returns
    #######

    parameters [Struct]

    Notes
    #####

    If input is empty, stores None.

    """
    parameters = dict()
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
    # Convert dict to struct
    logger.debug("... done.")

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

    parameters = utilities.Struct(**parameters)
    return parameters

# Handle exceptions in popup window


class IgnoreExceptions(ExceptionHandler):
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


ExceptionManager.add_handler(IgnoreExceptions())


class ErrorDisplay():
    """
    Popup window in case an exception is caught. Displays type of error and
    error message.
    """
    def __init__(self, error_title, error_message):
        """
        Init PopupWindow and open popup.
        """
        error_popup = PopupWindow(error_title, error_message)
        error_popup.popup.open()


def _scale_popup_window(message, window_size=None,
                        max_letters=POPUP_WINDOW_MAX_LETTERS):
    """
    Scales popup window size based on number of lines and longest line (number
    of letters.)

    Parameters
    ##########

    message [str]
    window_size [horizontal, vertical]:     One line base size.
                                            Default: POPUP_WINDOW_SIZE
    max_letters [float]:                    Default: POPUP_WINDOW_MAX_LETTERS

    Returns
    #######

    window_size [horizontal, vertical]:     Scaled window size

    """
    # Init window size
    window_size = [0, 0]

    # Count lines in help message to set height
    nlines = message.count('\n')+1
    # At least 2 lines to display title correctly (at one line it dissapears)
    if nlines == 1:
        nlines = 2
    window_size[1] = POPUP_WINDOW_SIZE[1] * nlines
    # Count sets of POPUP_WINDOW_MAX_LETTERS letters to set width
    nletters = float(len(max(message.split('\n'), key=len)))
    nwidth = int(nletters/POPUP_WINDOW_MAX_LETTERS)+1
    window_size[0] = POPUP_WINDOW_SIZE[0] * nwidth
    return window_size


# %% Main GUI


class giGUI(F.BoxLayout):
    """
    Main Widget, BoxLayout
    """
    # Functions callable in .kv file

    def check_general_input(self):
        # Convert input
        parameters = _convert_input(self.ids)
        print(parameters.spectrum_range)
        # Check input
#        try:
#            logger.info("Checking general input...")
#            check_input.general_input(parameters)
#            logger.info("... done.")
#        except check_input.InputError as e:
#            logger.debug("Displaying error...")
#            ErrorDisplay('Input Error', str(e))


# %% Main App


class giGUIApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return giGUI()  # Main widget, root


# %% Main


if __name__ == '__main__':
    giGUIApp().run()

    # If necessary
#    try:
#        giGUIApp().run()
#    except CriticalError as e:
#        close_gracefully()
