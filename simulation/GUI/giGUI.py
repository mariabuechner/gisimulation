"""
GUI mpodule for gi-simulation.

@author: buechner_m  <maria.buechner@gmail.com>
"""
import numpy as np
import re
import logging
import kivy
from kivy.logger import Logger
from kivy.app import App
from kivy.core.window import Window
# Properties
from kivy.properties import StringProperty
# UIX
from kivy.factory import Factory as F


# Check kivy version
kivy.require('1.10.0')

# Use Kivy logger to handle logging.Logger
logging.Logger.manager.root = Logger  # Makes Kivy Logger root for all
                                      # following loggers
logger = logging.getLogger(__name__)

# Set App Window configuration
#Window.clearcolor = (248, 255, 255, 1)  # If not black
Window.maximize()  # NOTE: On desktop platforms only
#Window.set_icon('path\to\icon')

# Constants
POPUP_WINDOW_SIZE = [550, 80]  # Width: 600 per line, Height: 80 per line
POPUP_WINDOW_MAX_LETTERS = 80.0  # max 80 letters per line

###############################################################################
# Custom Widgets
###############################################################################


class FloatInput(F.TextInput):
    """
    Allows only numbers 0...9 and one dot as text input (for numerical input)
    """
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        """
        Overwrites the insert_text function to only accept pat and '.'.
        """
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


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
        """
        # Custom Window with close button
        popup_window = F.BoxLayout(orientation='vertical')
        popup_window.add_widget(F.Label(text=str(message)))
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
        window_title = 'Help: {}'.format(self.text)
        self.help_popup = PopupWindow(window_title, self.help_message)
        self.help_popup.popup.open()
        # To manage input chain corectly
        return super(LabelHelp, self).on_touch_down(touch)


###############################################################################
# Utility functions
###############################################################################


def _scale_popup_window(message, window_size=None,
                        max_letters=POPUP_WINDOW_MAX_LETTERS):
    """
    Scales popup window size based on number of lines and longes line (number
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
    window_size[1] = POPUP_WINDOW_SIZE[1] * nlines
    # Count sets of POPUP_WINDOW_MAX_LETTERS letters to set width
    nletters = float(len(max(message.split('\n'), key=len)))
    nwidth = int(nletters/POPUP_WINDOW_MAX_LETTERS)+1
    window_size[0] = POPUP_WINDOW_SIZE[0] * nwidth
    return window_size

###############################################################################
# Main GUI
###############################################################################


class giGUI(F.BoxLayout):
    pass

# Main App


class giGUIApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return giGUI()  # Main widget, root


if __name__ == '__main__':
    # Config logger
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                        '%(message)s')

    # Run app
    giGUIApp().run()
