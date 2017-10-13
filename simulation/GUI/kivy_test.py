"""
test gui.

@author: buechner_m  <maria.buechner@gmail.com>
"""
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import ListProperty

import random

# Check kivy version
kivy.require('1.10.0')

# Set App Window configuration
Window.clearcolor = (248, 255, 255, 1)
Window.maximize()  # NOTE: On desktop platforms only
#Window.set_icon('path\to\icon')


class testGUI(BoxLayout):
    # Define kivy properties
    # NOTE: on_property etc. is also possible for user defined properties!!!
    #       can also be defined on python side... def on_text_color():
    text_color = ListProperty([1,0,0,1])  # Default color red
    # Function to change label color on text change
    def change_label_color(self, *args):
        color = [random.random() for i in xrange(3)] + [1]
#        label = self.ids.my_label # use ids from .kv to get label instance
#        label.color = color  # same properties as in .kv file
#        # Change also the other 2 label's color
#        label1 = self.ids.label1
#        label2 = self.ids.label2
#        label1.color = color
#        label2.color = color
        # Use kivy property to set colors directly in the labels rules in .kv
        self.text_color = color # needs to be defined in class (s.o.)


class testApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return testGUI()  # Main widget, root


if __name__ == '__main__':
    testApp().run()
