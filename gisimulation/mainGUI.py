"""
GUI module for gi-simulation.

Usage
#####

python maingui.py [Option...]::
    -d, --debug     show debug logs

@author: buechner_m  <maria.buechner@gmail.com>
"""
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
from kivy.core.window import Window
# UIX
from kivy.factory import Factory as F

# Logging
# Set logger before importing simulation modules (to set format for all)
# Use Kivy logger to handle logging.Logger
logging.Logger.manager.root = Logger  # Makes Kivy Logger root for all
                                      # following loggers

logger = logging.getLogger(__name__)

# gisimulation imports
import simulation.parser_def as parser_def
import simulation.utilities as utilities
import simulation.check_input as check_input


# Set App Window configuration
Window.maximize()  # NOTE: On desktop platforms only

# %% Constants

ERROR_MESSAGE_SIZE = (600, 450)  # absolute
FILE_BROWSER_SIZE = (0.9, 0.9)  # relative
LINE_HEIGHT = 35

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
    TextInput which only allows positive integers.
    """

    pattern = re.compile('[^0-9]')  # Allowed input numbers

    def insert_text(self, substring, from_undo=False):
        """
        Overwrites the insert_text function to only accept numbers 0...9.
        """
        pattern = self.pattern
        s = re.sub(pattern, '', substring)
        return super(IntInput, self).insert_text(s, from_undo=from_undo)


class Distances(F.GridLayout):
    def __init__(self, **kwargs):
        """
        Init for free and parallel beam, minimum required is Source to Detector
        distance.
        """
        super(Distances, self).__init__(**kwargs)
        self.cols = 1
        self.update(['Source', 'Detector'])

    def update(self, component_list, beam_geometry='parallel',
               geometry='free'):
        """
        Update the distance widgets according to the component list or any
        special geometry/beam geometry.

        Parameters
        ##########

        component_list [list]
        beam_geometry [str]
        geometry [str]

        Notes
        #####

        required:               not disabled and check for it
        optional:               not disabled, no problem if not set
        display:                disabled

        'free':                 have to set all distances manually, based
                                on component list

        'parallel'&'conv':      none needs to be set, display only G1-G2

        'cone'& not 'free':     required:   S/G0_G1 OR S/G0_G2
                                            if G0, than S_G0
                                optional:   G2_Dectector
                                display:    all based on component list

        """
        # Remove sample from list (if necessary)
        if 'Sample' in component_list:
            component_list.remove('Sample')
        # Set relevant components
        if beam_geometry == 'parallel' and geometry != 'free':
            component_list = ['G1', 'G2']
        # Remove all old widgets
        self.clear_widgets()
        # Add new ones for all comonents
        height = (len(component_list)-1) * LINE_HEIGHT  # Height of self
        for index, component in enumerate(component_list[:-1]):
            logger.debug("component: {}".format(component))
            distance_container = F.BoxLayout()

            distance_text = ("Distance from {0} to {1} [mm]"
                             .format(component, component_list[index+1]))
            distance_label = NonFileBrowserLabel(text=distance_text)

            distance_value = FloatInput(sixe_hint_x=0.2)
            distance_id = "{0}_{1}".format(component, component_list[index+1])
            distance_value.id = distance_id

            # Just displays
            if beam_geometry == 'parallel' and geometry != 'free':
                distance_value.disabled = True
            elif beam_geometry == 'cone' and geometry != 'free':
                if distance_id == 'G1_G2':
                    distance_value.disabled = True

            distance_container.add_widget(distance_label)
            distance_container.add_widget(distance_value)
            self.add_widget(distance_container)
            logger.debug("Added label '{0}' with input ID '{1}'"
                         .format(distance_text, distance_id))

            # Add option to set S/G0 to G2 distance
            if (distance_id == 'Source_G1' or distance_id == 'G0_G1') and \
                    geometry != 'free':
                # Add extra line for total length option
                height = (len(component_list)) * LINE_HEIGHT

                if distance_id == 'Source_G1':
                    extra_distance_text = "Distance from Source to G2 [mm]"
                    extra_distance_id = "Source_G2"
                else:
                    extra_distance_text = "Distance from G0 to G2 [mm]"
                    extra_distance_id = "G0_G2"
                # Add extra distance
                extra_distance_container = F.BoxLayout()

                extra_distance_label = \
                    NonFileBrowserLabel(text=extra_distance_text)

                extra_distance_value = FloatInput(sixe_hint_x=0.2)
                extra_distance_value.id = extra_distance_id
                # Connect to only set one (if other is not empty, disabled)

                distance_value.bind(text=partial(self.on_text,
                                                 extra_distance_value))
                extra_distance_value.bind(text=partial(self.on_text,
                                                       distance_value))

                # Add wisgets
                extra_distance_container.add_widget(extra_distance_label)
                extra_distance_container.add_widget(extra_distance_value)
                self.add_widget(extra_distance_container)
                logger.debug("Added label '{0}' with input ID '{1}'"
                             .format(extra_distance_text, extra_distance_id))

        # Fill with new widgets
        self.size_hint_y = None
        self.height = height

    def on_text(self, linked_instance, instance, value):
        if value != '':
            linked_instance.disabled = True
        else:
            linked_instance.disabled = False

# Error popup


class ErrorDisplay():
    """
    Popup window in case an exception is caught. Displays type of error and
    error message.

    Parameters
    ##########

    error_title [str]:      type of error
    error_message [str]:    error message

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
    continue. Displays type of warning and warning message.

    Parameters
    ##########

    warning_title [str]:        type of warning
    warning_message [str]:      warning message

    overwrite [func]:           function to execute if 'continue'
    overwrite_finish [func]:    after overwrite, finish up
    cancel_finish [func]:       after cancel, finish up

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

    Parameters
    ##########

    help_message [StringProperty]

    """
    help_message = F.StringProperty()

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
    Label is scrolable in y direction. See .kv file for more information.
    """
    text = F.StringProperty('')

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
        Executed on press of any button, stores continuation indicator.

        Parameters
        ##########

        continue_ [boolean]:    Continue (True) with action or cancel (False)
                                action

        """
        self._continue = args[0]
        self.popup.dismiss()

    def finish(self, *args):
        """
        Finishing function bound to popup's dismiss. If 'continue' was pressed,
        execute 'overwrite()' and the 'overwrite_finish()', else the
        'cancel_finish'.
        """
        if self._continue:
            logger.info("Overwriting file!")
            self.overwrite()
            logger.info('... done.')
            self.overwrite_finish()
        else:
            logger.info("... canceled.")
            self.cancel_finish()


def _load_input_file(input_file_path):
    """
    Load string parameter keys and string values from input file.

    Parameters
    ##########

    input_file_path [str]:      file path to input file, including name.

    Returns
    #######

    input_parameters [dict]:    input_parameters['var_key'] = var_value

    Notes
    #####

    var_value is string, var_key is string

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
    Save string parameter keys and values (as strings) to input file.

    Parameters
    ##########

    input_file_path [str]:      file path to (nes) input file, including name.
    input_parameters [dict]:    input_parameters['var_key'] = var_value

    Returns
    #######

    input_parameters [dict]:    input_parameters['var_key'] = var_value

    """
    with open(input_file_path, 'w') as f:
        for var_key, value in input_parameters.iteritems():
            f.writelines(var_key+'\n')

            if type(value) is np.ndarray:  # For FOV anf Range
                f.writelines(str(value[0])+'\n')
                f.writelines(str(value[1])+'\n')
            else:
                f.writelines(str(value)+'\n')


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
        if 'CheckBox' in str(value):
            continue
        elif 'TabbedPanel' in str(value):
            continue
        elif 'Layout' in str(value):
            continue
        elif 'Distances' in str(value):
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

# If kivy NOT set to debug, disable kivy error handling
if Logger.level > 10:
    ExceptionManager.add_handler(_IgnoreExceptions())

# %% Main GUI


class giGUI(F.BoxLayout):
    """
    Main Widget, BoxLayout

    Notes
    #####

    File loading and saving based on
    "https://kivy.org/docs/api-kivy.uix.filechooser.html" (23.10.2017)
    """
    # Global variables (must be kivy properties)
    parameters = F.DictProperty()  # Will be params[var_name] = value
    parser_info = F.DictProperty()  # Will be params[var_name]
                                    #           = [var_key, var_help]
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
        self.parser_info = \
            parser_def.get_arguments_info(parser_def.input_parser())
        for var_name, value in self.parser_info.iteritems():
            self.parser_link[value[0]] = var_name
        # parameters
        self.parameters = _collect_input(self.parameters, self.ids)
        self.parameters['spectrum_file'] = None
        # Components trackers
        self.setup_components = ['Source', 'Detector']
        # Avail fixed gratings
        self.ids.g0_set.disabled = True
        if self.ids.beam_geometry.text == 'parallel':
            self.available_gratings = ['G1', 'G2']
        else:
            self.available_gratings = ['G0', 'G1', 'G2']
        # Sample
        self.update_sample_distance_label()
        self.parameters['sample_position'] = None

    # General simulation functions

    def check_general_input(self):
        """
        Check general input, by
            1) load values from all widgets,
            2) check manually the required parameters from parser
            3) check values with check_input.general_input(...)
            4) Reset widget values to include newly calculated parameters
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
        When spectrum_file_path changes, set parameters and update load status.
        """
        if value:
            self.spectrum_file_loaded = True
            self.parameters['spectrum_file'] = self.spectrum_file_path
        else:
            self.spectrum_file_loaded = False
            self.parameters['spectrum_file'] = None

    def on_load_input_file_paths(self, instance, value):
        """
        When load_input_file_paths changes, laod keys and values from all files
        in selection list.
        Update widget content accordingly.

        Notes
        #####

        input_parameters [dict]:    input_parameters[var_key] = str(value)

        """
        # Do for all files in load_input_file_paths and merge results.
        # Later fiels overwrite first files.
        for input_file in value:
            logger.info("Loading input from file at: {0}".format(input_file))
            input_parameters = _load_input_file(input_file)
        # Set widget content
        try:
            self._set_widgets(input_parameters, from_file=True)
        except check_input.InputError as e:
            ErrorDisplay('Input Error', str(e))

    def on_save_input_file_path(self, instance, value):
        """
        When save_input_file_path changes, try to save parameters var_name and
        value pairs that are listed in parser to file.

        Notes
        #####

        self.parameters [dict]:     widget_parameters[var_name] = value

        If file exists:             Popup to ask to 'continue' or 'cancel',
                                    give following functions to popup:
                                    _save_input_file:       overwrite
                                    self.overwrite_save:    overwrite_finish
                                    self.cancel_save:       cancel_finish

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
            logger.info("Saving input to file...")
            if os.path.isfile(value):
                # File exists
                logger.warning("File '{0}' already exists!".format(value))
                WarningDisplay("File already exists!",
                               "Do you want to overwrite it?",
                               partial(_save_input_file,
                                       value,
                                       input_parameters),
                               self.overwrite_save,
                               self.cancel_save)
            else:
                # File new
                _save_input_file(value, input_parameters)
                logger.info('... done.')
                self.dismiss_popup()

    def overwrite_save(self):
        """
        Finish action if file is overwritten.

        Notes
        #####

        Reset save_input_file_path to '' to allow next save at same file.

        """
        self.dismiss_popup()
        self.save_input_file_path = ''

    def cancel_save(self):
        """
        Finish action if file saving is canceled (do not overwrite).

        Notes
        #####

        Reset save_input_file_path to '' to allow next save at same file.

        """
        self.save_input_file_path = ''

    # Menu spinners

    def on_save_spinner(self, spinner):
        """
        On save_spinner change, keep text the same and call respective
        functions to execute.
        """
        selected = spinner.text
        spinner.text = 'Save...'
        if selected == 'Input file...':
            self.show_input_save()
        elif selected == 'Results...':
            self.save_results()

    def on_help_spinner(self, spinner):
        """
        On help_spinner change, keep text the same and show popup with
        corresponding help message.
        """
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

    def on_dual_phase_checkbox_active(self):
        """
        """
        if self.ids.dual_phase.disabled:
            self.ids.dual_phase.active = False
        if self.ids.dual_phase.active:
            self.ids.fixed_grating.values = ['G1', 'G2']  # Disable G0
            self.ids.g0_set.active = False
            self.ids.g0_set.disabled = True
            if self.ids.geometry.text != 'free':
                if self.ids.type_g2.text == 'abs':
                    self.ids.type_g2.text = 'phase'
                self.ids.type_g2.values = ['mix', 'phase']
        else:
            if self.ids.beam_geometry.text == 'Cone':
                self.ids.fixed_grating.values = ['G0', 'G1', 'G2']
            self.ids.g0_set.disabled = False
            if self.ids.geometry.text != 'free':
                if self.ids.type_g2.text == 'phase':
                    self.ids.type_g2.text = 'abs'
                self.ids.type_g2.values = ['mix', 'abs']

    def on_geometry(self):
        """
        Set sample position options and activate required gratings.
        """
        #======================================================================
        #   Dirty fix for issue #12
        self.ids.fixed_grating.text = 'G0'
        self.ids.fixed_grating.text = 'Choose fixed grating...'
        #======================================================================
        # Remove sample if it was set before (to start fresh)
        if 'Sample' in self.setup_components:
                self.ids.add_sample.active = False
        else:
            logger.debug("Current setup consists of: {0}"
                         .format(self.setup_components))
        # Required gratings
        if self.ids.geometry.text != 'free':
            # G1 and G2 required
            self.ids.g1_set.active = True
            self.ids.g2_set.active = True
            # Sample relative to G1
            self.ids.sample_relative_to.text = 'G1'
            self.ids.sample_relative_to.values = ['G1']
            # Grating types
            if self.ids.type_g0.text == 'phase':
                self.ids.type_g0.text = ''
            self.ids.type_g0.values = ['mix', 'abs']
            if self.ids.type_g1.text == 'abs':
                self.ids.type_g1.text = ''
            self.ids.type_g1.values = ['mix', 'phase']
            if self.ids.dual_phase.active:
                if self.ids.type_g2.text == 'abs':
                    self.ids.type_g2.text = ''
                self.ids.type_g2.values = ['mix', 'phase']
            else:
                if self.ids.type_g2.text == 'phase':
                    self.ids.type_g2.text = ''
                self.ids.type_g2.values = ['mix', 'abs']
        else:
            # Reset to 'free' (same as start)
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after']
            self.ids.sample_relative_to.text = 'Source'
            self.ids.sample_relative_to.values = self.setup_components
            # Grating types
            self.ids.type_g0.text = ''
            self.ids.type_g0.values = ['mix', 'phase', 'abs']
            self.ids.type_g1.text = ''
            self.ids.type_g1.values = ['mix', 'phase', 'abs']
            self.ids.type_g2.text = ''
            self.ids.type_g2.values = ['mix', 'phase', 'abs']
        # GI cases
        if self.ids.geometry.text == 'conv':
            self.ids.sample_relative_position.text = 'before'
            self.ids.sample_relative_position.values = ['before']
            if self.ids.beam_geometry.text == 'parallel':
                self.ids.sample_relative_position.values = ['after', 'before']
        elif self.ids.geometry.text == 'inv':
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after']
        elif self.ids.geometry.text == 'sym':
            # Symmetrical case
            self.ids.sample_relative_position.text = 'after'
            self.ids.sample_relative_position.values = ['after', 'before']
        # Update distances options
        self.ids.distances.update(self.setup_components,
                                  self.ids.beam_geometry.text,
                                  self.ids.geometry.text)
        # Reset fixed grating input
        self.ids.fixed_grating.text = 'Choose fixed grating...'
        # Update dual_phase options
        self.on_dual_phase_checkbox_active()

    def on_beam_geometry(self):
        """
        Set availabel gratings, update geometry options and deactivate
        required gratings.
        """
        # Remove sample if it was set
        if 'Sample' in self.setup_components:
                self.ids.add_sample.active = False
        else:
            logger.debug("Current setup consists of: {0}"
                         .format(self.setup_components))
        # Reset fixed grating input
        self.ids.fixed_grating.text = 'Choose fixed grating...'

        if self.ids.beam_geometry.text == 'parallel':
            # Change GI geometry text
            if self.ids.geometry.text == 'sym' or \
              self.ids.geometry.text == 'inv':
                # Mode changes, reset GI geometry
                self.ids.geometry.text = 'free'
            # Set available and deactive gratings
            self.ids.g0_set.active = False
            self.ids.g0_set.disabled = True
            self.available_gratings = ['G1', 'G2']
            # Update distances options
            self.ids.distances.update(self.setup_components,
                                      self.ids.beam_geometry.text,
                                      self.ids.geometry.text)
        else:
            # Update geometry conditions for cone beam
            self.on_geometry()  # Includes update distances
            self.ids.g0_set.disabled = False
            self.available_gratings = ['G0', 'G1', 'G2']
        # Update dual_phase options
        self.on_dual_phase_checkbox_active()

    def on_setup_components(self, instance, value):
        """
        On change in component list, update sample_relative_to spinner text.
        """
        if not self.sample_added:
            self.ids.sample_relative_to.text = self.setup_components[0]

    def on_grating_checkbox_active(self, state, checkbox_name):
        """
        Add/remove activate/deactivaded grating to/from component list and
        update distances.
        """
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
        # Update sample_relative_to and sample_relative_position
        self.on_geometry()
        self.on_beam_geometry()  # Includes update distances

    def on_sample_relative_to(self):
        """
        Update sample_relative_position values and text accoring to selected
        sample_relative_to, update sample in components.
        """
        self.update_sample_distance_label()
        if self.ids.sample_relative_to.text == 'Source':
            self.ids.sample_relative_position.values = ['after']
            self.ids.sample_relative_position.text = 'after'
        elif self.ids.sample_relative_to.text == 'Detector':
            self.ids.sample_relative_position.values = ['before']
            self.ids.sample_relative_position.text = 'before'
        elif self.ids.geometry.text == 'free':
            self.ids.sample_relative_position.values = ['after', 'before']
        # If sample is selected, Update component list and distances
        if self.sample_added:
            self.on_sample_checkbox_active(False)
            self.on_sample_checkbox_active(True)

    def on_sample_relative_position(self):
        """
        Update sample_relative_position values and text accoring to selected
        sample_relative_position, update sample in components.
        """
        self.update_sample_distance_label()
        # If sample is selected, Update component list and distances
        if self.sample_added:
            self.on_sample_checkbox_active(False)
            self.on_sample_checkbox_active(True)

    def on_sample_checkbox_active(self, state):
        """
        Add/Remove sample to/from component list and update distances.
        """
        if state:
            # Add sample at right position
            self.sample_added = True
            reference_index = \
                self.setup_components.index(self.ids.sample_relative_to.text)
            if self.ids.sample_relative_position.text == 'after':
                self.setup_components.insert(reference_index+1, 'Sample')
            else:
                self.setup_components.insert(reference_index, 'Sample')
            # Set sample_position in parameters (after G1: ag1, before
            # Detector: bd)
            if self.ids.sample_relative_to.text in ['Source', 'Detector']:
                # Only first letter of component
                self.parameters['sample_position'] = \
                    self.ids.sample_relative_position.text[0] + \
                    self.ids.sample_relative_to.text[0].lower()
            else:
                # All component name
                self.parameters['sample_position'] = \
                    self.ids.sample_relative_position.text[0] + \
                    self.ids.sample_relative_to.text.lower()
        else:
            # Remove sample, in case that geometry is changing
            self.setup_components.remove('Sample')
            self.sample_added = False
            self.parameters['sample_position'] = None

        logger.debug("Current setup consists of: {0}"
                     .format(self.setup_components))

    def update_sample_distance_label(self):
        """
        """
        if self.ids.sample_relative_position.text == 'after':
            label = ("Distance from {0} to Sample [mm]"
                     .format(self.ids.sample_relative_to.text))
        else:
            label = ("Distance from Sample to {0} [mm]"
                     .format(self.ids.sample_relative_to.text))
        self.ids.sample_distance_label.text = label

    # Loading and saving files

    def dismiss_popup(self):
        """
        Dismisses current self._popup.
        """
        self._popup.dismiss()

    def _fbrowser_canceled(self, instance):
        """
        Closes current FileBrowser.
        """
        logger.debug('FileBrowser canceled, closing itself.')
        self.dismiss_popup()

    # Spectrum

    def show_spectrum_load(self):
        """
        Open popup with FileBrowser to load spectrum_file_path.

        Notes
        #####

        Default path:               ./data/spectra/
        Available file extentions:  ['*.csv','*.txt']

        """
        # Define browser
        spectra_path = os.path.join(os.path.dirname(os.path.
                                                    realpath(__file__)),
                                    'data', 'spectra')
        browser = FileBrowser(select_string='Select',
                              path=spectra_path,  # Folder to open at start
                              filters=['*.csv', '*.txt'])
        browser.bind(on_success=self._spectra_fbrowser_success,
                     on_canceled=self._fbrowser_canceled)

        # Add to popup
        self._popup = F.Popup(title="Load spectrum", content=browser,
                              size_hint=FILE_BROWSER_SIZE)
        self._popup.open()

    def _spectra_fbrowser_success(self, instance):
        """
        On spectrum file path selection, store and close FileBrowser.
        """
        self.spectrum_file_path = instance.selection[0]
        logger.debug("Spectrum filepath is: {}"
                     .format(self.spectrum_file_path))
        self.dismiss_popup()

    # Input file

    # Load input file

    def show_input_load(self):
        """
        Open popup with file browser to load input file location.

        Notes
        #####

        Default path:               ./data/inputs/
        Available file extentions:  [*.txt']

        """
        # Define browser
        input_path = os.path.join(os.path.dirname(os.path.
                                                  realpath(__file__)),
                                  'data', 'inputs')
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
        """
        On input file path selection, store and close FileBrowser.
        """
        self.load_input_file_paths = instance.selection
        logger.debug("{0} input files loaded."
                     .format(len(self.load_input_file_paths)))
        self.dismiss_popup()

    # Save input file

    def show_input_save(self):
        """
        Open popup with file browser to save input file.

        Notes
        #####

        Default path:               ./data/
        Available file extentions:  [*.txt']

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
        """
        On input file path selection, save to file and close FileBrowser.
        """
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
        logger.info("Saving results...")

    # Set widgete values
    def _set_widgets(self, input_parameters, from_file):
        """
        Update widget content (text) to values stored in parameters.

        Notes
        #####

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
            logger.info("Setting widget values from file...")
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
                    # Check if it is integer
                    if '.' in value_str[0] or '.' in value_str[1]:
                        error_message = "FOV must be integer, not float."
                        logger.error(error_message)
                        raise check_input.InputError(error_message)
                    self.ids['field_of_view_x'].text = value_str[0]
                    self.ids['field_of_view_y'].text = value_str[1]
                else:
                    logger.debug("Setting text of widget '{0}' to: {1}"
                                 .format(var_name, value_str[0]))
                    self.ids[var_name].text = value_str[0]
            logger.info("...done.")
        else:
            logger.info("Setting widget values from parameters...")
            for var_name, value in input_parameters.iteritems():
                # Skip all the not-set parameters
                if value is not None:
                    logger.debug("var_name is: {0}".format(var_name))
                    logger.debug("value is: {0}".format(value))
                    if var_name not in self.parser_info:
                        # Input variable not implemented in parser
                        logger.warning("Parameter '{0}' read from app, but "
                                       "not defined in parser. Skipping..."
                                       .format(var_name))
                        continue
                    var_key = self.parser_info[var_name][0]
                    logger.debug("var_key is: {0}".format(var_key))
                    # Set input values to ids.texts
                    if var_name == 'spectrum_range':
                        self.ids['spectrum_range_min'].text = str(value[0])
                        self.ids['spectrum_range_max'].text = str(value[1])
                    elif var_name == 'field_of_view':
                        self.ids['field_of_view_x'].text = str(int(value[0]))
                        self.ids['field_of_view_y'].text = str(int(value[1]))
                    else:
                        logger.debug("Setting text of widget '{0}' to: {1}"
                                     .format(var_name, value))
                        self.ids[var_name].text = str(value)
            logger.info("...done.")

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
        boxlayout_height = ((childen_height + boxlayout.spacing +
                             boxlayout.padding[1] + boxlayout.padding[3]) *
                            len(boxlayout.children))
        return boxlayout_height

# %% Main App


class giGUIApp(App):
    def build(self):
        self.title = 'GI Simumlation'
        return giGUI()  # Main widget, root

# %% Main

if __name__ == '__main__':
    giGUIApp().run()
