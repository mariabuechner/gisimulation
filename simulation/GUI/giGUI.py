"""
GUI mpodule for gi-simulation.

@author: buechner_m  <maria.buechner@gmail.com>
"""
import numpy as np
import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
#from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.label import Label
from kivy.uix.button import Button

# Check kivy version
kivy.require('1.10.0')

# Set App Window configuration
#Window.clearcolor = (248, 255, 255, 1)  # If not black
Window.maximize()  # NOTE: On desktop platforms only
#Window.set_icon('path\to\icon')


class giGUI(BoxLayout):
    pass


class giGUIApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return giGUI()  # Main widget, root


if __name__ == '__main__':
    giGUIApp().run()
