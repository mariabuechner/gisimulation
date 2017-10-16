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
# Graphics
from kivy.graphics import Color, Rectangle
# UIX
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup

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


class FloatInput(TextInput):
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


class LabelHelp(Label):
    """
    Label, but upon touch down a help message appears
    """
    help_message = StringProperty()

#    def __init__(self, *args, **kwargs):
#        super(LabelHelp, self).__init__(*args, **kwargs)
#        self.help_popup = Popup(title='Help',
#                                content=Label(text=str(self.help_message)),
#                                pos=self.pos,
#                                size_hint=(None, None),
#                                size=(HELP_WINDOW_SIZE))
    def on_touch_down(self, touch):
        """
        """
        # Custom Window with close button
        popup_window = BoxLayout(orientation='vertical')
        popup_window.add_widget(Label(text=str(self.help_message)))
        close_popup_button = Button(text='OK')
        popup_window.add_widget(close_popup_button)

        self.help_popup = Popup(title='Help: {}'.format(self.text),
                                auto_dismiss=False,
                                content=popup_window,
                                pos=self.pos,
                                size_hint=(None, None),
                                size=(_scale_popup_window(self.help_message)))
        self.help_popup.open()
        # Close help window when button 'OK' is pressed
        close_popup_button.bind(on_press=self.help_popup.dismiss)


###############################################################################
# Utility functions

def _scale_popup_window(message, window_size=POPUP_WINDOW_SIZE,
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
    # Count lines in help message to set height
    nlines = message.count('\n')+1
    window_size[1] = window_size[1] * nlines
    # Count sets of POPUP_WINDOW_MAX_LETTERS letters to set width
    nletters = float(len(max(message.split('\n'), key=len)))
    nwidth = int(nletters/max_letters)+1
    window_size[0] = window_size[0] * nwidth
    return window_size

###############################################################################
# Main GUI


class giGUI(BoxLayout):
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
