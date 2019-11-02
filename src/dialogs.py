#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""


**Modal dialogs**

 * :class:`DiscardChangesDialog`
 * :class:`ApproveWarningDialog`
 * :class:`DataEntryDialog`
 * :class:`GridShapeDialog`
 * (:class:`FileDialogBase`)
 * :class:`FileOpenDialog`
 * :class:`FileSaveDialog`
 * :class:`ImageFileOpenDialog`
 * :class:`FindDialog`
 * :class:`ChartDialog`

"""

from dataclasses import dataclass
from functools import partial

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog, QLineEdit
from PyQt5.QtWidgets import QLabel, QFormLayout, QVBoxLayout, QGroupBox
from PyQt5.QtWidgets import QDialogButtonBox, QSplitter, QTextBrowser
from PyQt5.QtWidgets import QCheckBox, QGridLayout, QLayout
from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtGui import QIntValidator, QImageWriter

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
except ImportError:
    Figure = None

from lib.spelltextedit import SpellTextEdit
from actions import ChartDialogActions
from toolbar import ChartTemplatesToolBar
from icons import PYSPREAD_PATH

MPL_TEMPLATE_PATH = PYSPREAD_PATH / 'share/templates/matplotlib'


class DiscardChangesDialog:
    """Modal dialog that asks if the user wants to discard or save unsaved data

    The modal dialog is shown on accessing the property choice.

    """

    title = "Unsaved changes"
    text = "There are unsaved changes.\nDo you want to save?"
    choices = QMessageBox.Discard | QMessageBox.Cancel | QMessageBox.Save
    default_choice = QMessageBox.Save

    def __init__(self, main_window):
        self.main_window = main_window

    @property
    def choice(self):
        """User choice

        Returns True if the user confirms in a user dialog that unsaved
        changes will be discarded if conformed.
        Returns False if the user chooses to save the unsaved data
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.main_window, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == QMessageBox.Discard:
            return True
        elif button_approval == QMessageBox.Save:
            return False


class ApproveWarningDialog:
    """Modal warning dialog for approving files to be evaled

    The modal dialog is shown on accessing the property choice.

    """

    title = "Security warning"
    text = ("You are going to approve and trust a file that you have not "
            "created yourself. After proceeding, the file is executed.\n \n"
            "It may harm your system as any program can. Please check all "
            "cells thoroughly before proceeding.\n \n"
            "Proceed and sign this file as trusted?")
    choices = QMessageBox.No | QMessageBox.Yes
    default_choice = QMessageBox.No

    def __init__(self, parent):
        self.parent = parent

    @property
    def choice(self):
        """User choice

        Returns True iif the user approves leaving safe_mode.
        Returns False iif the user chooses to stay in safe_mode
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.parent, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == QMessageBox.Yes:
            return True
        elif button_approval == QMessageBox.No:
            return False


class DataEntryDialog(QDialog):
    """Modal dialog for entering multiple values

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * title: str
    \tDialog title
    * labels: list or tuple of str
    \tLabels for the values in the dialog
    * initial_data: list or tuple of str, defaults to None
    \tInitial values to be displayed in the dialog, must match no. labels
    * validators: list or tuple of QValidator, defaults to None
    \tValidators for the editors of the dialog, must match no. labels

    """

    def __init__(self, parent, title, labels, initial_data=None,
                 groupbox_title=None, validators=None):
        super().__init__(parent)

        self.labels = labels
        self.groupbox_title = groupbox_title

        if initial_data is None:
            self.initial_data = [""] * len(labels)
        elif len(initial_data) != len(labels):
            raise ValueError("Length of labels and initial_data not equal")
        else:
            self.initial_data = initial_data

        if validators is None:
            self.validators = [None] * len(labels)
        elif len(validators) != len(labels):
            raise ValueError("Length of labels and validators not equal")
        else:
            self.validators = validators

        self.editors = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_form())
        layout.addStretch(1)
        layout.addWidget(self.create_buttonbox())
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)

    @property
    def data(self):
        """Executes the dialog and returns a tuple of strings

        Returns None if the dialog is canceled.

        """

        result = self.exec_()

        if result == QDialog.Accepted:
            return tuple(editor.text() for editor in self.editors)

    def create_form(self):
        """Returns form inside a QGroupBox"""

        form_group_box = QGroupBox()
        if self.groupbox_title:
            form_group_box.setTitle(self.groupbox_title)
        form_layout = QFormLayout()

        for label, initial_value, validator in zip(self.labels,
                                                   self.initial_data,
                                                   self.validators):
            editor = QLineEdit(str(initial_value))
            editor.setAlignment(Qt.AlignRight)
            if validator:
                editor.setValidator(validator)
            form_layout.addRow(QLabel(label + " :"), editor)
            self.editors.append(editor)

        form_layout.setLabelAlignment(Qt.AlignRight)
        form_group_box.setLayout(form_layout)

        return form_group_box

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        return button_box


class GridShapeDialog(DataEntryDialog):
    """Modal dialog for entering the number of rows, columns and tables

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * shape: 3-tuple of Integer
    \tInitial shape to be displayed in the dialog: (rows, columns, tables)

    """

    def __init__(self, parent, shape, title="Create a new Grid"):
        groupbox_title = "Grid Shape"
        labels = ["Number of Rows", "Number of Columns", "Number of Tables"]
        validator = QIntValidator()
        validator.setBottom(0)  # Do not allow negative values
        validators = [validator] * len(labels)
        super().__init__(parent, title, labels, shape, groupbox_title,
                         validators)

    @property
    def shape(self):
        """Executes the dialog and returns an int tuple rows, columns, tables

        Returns None if the dialog is canceled.

        """

        data = self.data
        if data is not None:
            try:
                return tuple(map(int, data))
            except ValueError:
                return


class PreferencesDialog(DataEntryDialog):
    """Modal dialog for entering pyspread preferences"""

    def __init__(self, parent):
        title = "Preferences"
        groupbox_title = "Global settings"
        labels = ["Signature key for files", "Cell calculation timeout [ms]",
                  "Frozen cell refresh period [ms]"]
        self.keys = ["signature_key", "timeout", "refresh_timeout"]
        self.mappers = [str, int, int]
        data = [getattr(parent.settings, key) for key in self.keys]
        validator = QIntValidator()
        validator.setBottom(0)  # Do not allow negative values
        validators = [None, validator, validator]
        super().__init__(parent, title, labels, data, groupbox_title,
                         validators)

    @property
    def data(self):
        """Executes the dialog and returns a dict containing preferences data

        Returns None if the dialog is canceled.

        """

        data = super().data
        if data is not None:
            data_dict = {}
            for key, mapper, data in zip(self.keys, self.mappers, data):
                data_dict[key] = mapper(data)
            return data_dict


class CellKeyDialog(DataEntryDialog):
    """Modal dialog for entering a cell key, i.e. row, column and table

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * shape: 3-tuple of Integer
    \tShape of the grid: (rows, columns, tables)

    """

    def __init__(self, parent, shape):
        title = "Go to cell"
        groupbox_title = "Cell index"
        labels = ["Row", "Column", "Table"]

        row_validator = QIntValidator()
        row_validator.setRange(0, shape[0] - 1)
        column_validator = QIntValidator()
        column_validator.setRange(0, shape[1] - 1)
        table_validator = QIntValidator()
        table_validator.setRange(0, shape[2] - 1)
        validators = [row_validator, column_validator, table_validator]

        super().__init__(parent, title, labels, None, groupbox_title,
                         validators)

    @property
    def key(self):
        """Executes the dialog and returns an int tuple rows, columns, tables

        Returns None if the dialog is canceled.

        """

        data = self.data
        if data is not None:
            try:
                return tuple(map(int, data))
            except ValueError:
                return


class FileDialogBase:
    """Base class for modal file dialogs

    The choosen filename is stored in the filepath attribute
    The choosen name filter is stored in the chosen_filter attribute
    If the dialog is aborted then both filepath and chosen_filter are None

    _get_filepath must be overloaded

    """
    file_path = None
    suffix = None

    title = "Choose file"

    filters_list = [
        "Pyspread un-compressed (*.pysu)",
        "Pyspread compressed (*.pys)"
    ]
    selected_filter = None

    @property
    def filters(self):
        """Formatted filters for qt"""
        return ";;".join(self.filters_list)

    @property
    def suffix(self):
        if self.filters_list.index(self.selected_filter):
            return ".pys"
        else:
            return ".pysu"

    def __init__(self, main_window):

        self.main_window = main_window
        self.selected_filter = self.filters_list[0]

        self.show_dialog()

    def show_dialog(self):
        """Sublasses must overload this method"""
        raise Exception("show_dialog() - Needs method overload")


class FileOpenDialog(FileDialogBase):
    """Modal dialog for opening a pyspread file"""

    title = "Open"

    def show_dialog(self):
        """Present dialog and update values"""
        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class FileSaveDialog(FileDialogBase):
    """Modal dialog for saving a pyspread file"""

    title = "Save"

    def show_dialog(self):
        """Present dialog and update values"""
        path = self.main_window.settings.last_file_output_path
        self.file_path, self.selected_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class ImageFileOpenDialog(FileDialogBase):
    """Modal dialog for inserting an image"""

    title = "Insert image"

    img_formats = QImageWriter.supportedImageFormats()
    img_format_strings = ("*." + fmt.data().decode('utf-8')
                          for fmt in img_formats)
    img_format_string = " ".join(img_format_strings)
    name_filter = "Images ({})".format(img_format_string) + ";;" \
                  "Scalable Vector Graphics (*.svg *.svgz)"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window,
                                        self.title,
                                        str(path),
                                        self.name_filter)


@dataclass
class FindDialogState:
    """Dataclass for FindDialog state storage"""

    pos: QPoint
    case: bool
    results: bool
    more: bool
    backward: bool
    word: bool
    regex: bool
    start: bool


class FindDialog(QDialog):
    """Find dialog that is launched from the main menu"""

    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        workflows = main_window.workflows

        self._create_widgets()
        self._layout()

        self.setWindowTitle("Find")

        self.extension.hide()

        self.more_button.toggled.connect(self.extension.setVisible)
        self.find_button.clicked.connect(
                partial(workflows.find_dialog_on_find, self))

        # Restore state
        state = self.main_window.settings.find_dialog_state
        if state is not None:
            self.restore(state)

    def _create_widgets(self):
        """Create find dialog widgets"""

        self.search_text_label = QLabel("Search for:")
        self.search_text_editor = QLineEdit()
        self.search_text_label.setBuddy(self.search_text_editor)

        self.case_checkbox = QCheckBox("Match &case")
        self.results_checkbox = QCheckBox("Code and &results")

        self.find_button = QPushButton("&Find")
        self.find_button.setDefault(True)

        self.more_button = QPushButton("&More")
        self.more_button.setCheckable(True)
        self.more_button.setAutoDefault(False)

        self.extension = QWidget()

        self.backward_checkbox = QCheckBox("&Backward")
        self.word_checkbox = QCheckBox("&Whole words")
        self.regex_checkbox = QCheckBox("Regular e&xpression")
        self.from_start_checkbox = QCheckBox("From &start")

        self.button_box = QDialogButtonBox(Qt.Vertical)
        self.button_box.addButton(self.find_button,
                                  QDialogButtonBox.ActionRole)
        self.button_box.addButton(self.more_button,
                                  QDialogButtonBox.ActionRole)

    def _layout(self):
        """Find dialog layout"""

        self.extension_layout = QVBoxLayout()
        self.extension_layout.setContentsMargins(0, 0, 0, 0)
        self.extension_layout.addWidget(self.backward_checkbox)
        self.extension_layout.addWidget(self.word_checkbox)
        self.extension_layout.addWidget(self.regex_checkbox)
        self.extension_layout.addWidget(self.from_start_checkbox)
        self.extension.setLayout(self.extension_layout)

        self.text_layout = QGridLayout()
        self.text_layout.addWidget(self.search_text_label, 0, 0)
        self.text_layout.addWidget(self.search_text_editor, 0, 1)
        self.text_layout.setColumnStretch(0, 1)

        self.search_layout = QVBoxLayout()
        self.search_layout.addLayout(self.text_layout)
        self.search_layout.addWidget(self.case_checkbox)
        self.search_layout.addWidget(self.results_checkbox)

        self.main_layout = QGridLayout()
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.main_layout.addLayout(self.search_layout, 0, 0)
        self.main_layout.addWidget(self.button_box, 0, 1)
        self.main_layout.addWidget(self.extension, 1, 0, 1, 2)
        self.main_layout.setRowStretch(2, 1)

        self.setLayout(self.main_layout)

    def restore(self, state):
        """Restores state from FindDialogState"""

        self.move(state.pos)
        self.case_checkbox.setChecked(state.case)
        self.results_checkbox.setChecked(state.results)
        self.more_button.setChecked(state.more)
        self.backward_checkbox.setChecked(state.backward)
        self.word_checkbox.setChecked(state.word)
        self.regex_checkbox.setChecked(state.regex)
        self.from_start_checkbox.setChecked(state.start)

    # Overrides

    def closeEvent(self, event):
        """Store state for next invocation and close"""

        state = FindDialogState(pos=self.pos(),
                                case=self.case_checkbox.isChecked(),
                                results=self.results_checkbox.isChecked(),
                                more=self.more_button.isChecked(),
                                backward=self.backward_checkbox.isChecked(),
                                word=self.word_checkbox.isChecked(),
                                regex=self.regex_checkbox.isChecked(),
                                start=self.from_start_checkbox.isChecked())
        self.main_window.settings.find_dialog_state = state

        super().closeEvent(event)


class ReplaceDialog(FindDialog):
    """Replace dialog that is launched from the main menu"""

    def __init__(self, main_window):
        super().__init__(main_window)

        workflows = main_window.workflows

        self.setWindowTitle("Replace")

        self.replace_text_label = QLabel("Replace with:")
        self.replace_text_editor = QLineEdit()
        self.replace_text_label.setBuddy(self.replace_text_editor)

        self.text_layout.addWidget(self.replace_text_label, 1, 0)
        self.text_layout.addWidget(self.replace_text_editor, 1, 1)

        self.replace_button = QPushButton("&Replace")
        self.replace_all_button = QPushButton("Replace &all")

        self.button_box.addButton(self.replace_button,
                                  QDialogButtonBox.ActionRole)
        self.button_box.addButton(self.replace_all_button,
                                  QDialogButtonBox.ActionRole)

        self.replace_button.clicked.connect(
                partial(workflows.replace_dialog_on_replace, self))


class ChartDialog(QDialog):
    """The chart dialog"""

    def __init__(self, parent):
        if Figure is None:
            raise ModuleNotFoundError

        super().__init__(parent)

        self.actions = ChartDialogActions(self)

        self.chart_templates_toolbar = ChartTemplatesToolBar(self)

        self.setWindowTitle("Chart dialog")
        self.setModal(True)
        self.resize(800, 600)
        self.parent = parent

        self.actions = ChartDialogActions(self)

        self.dialog_ui()

    def on_template(self):
        """Event handler for pressing a template toolbar button"""

        chart_template_name = self.sender().data()
        chart_template_path = MPL_TEMPLATE_PATH / chart_template_name
        try:
            with open(chart_template_path) as template_file:
                chart_template_code = template_file.read()
        except OSError:
            return

        self.editor.insertPlainText(chart_template_code)

    def dialog_ui(self):
        """Sets up dialog UI"""

        msg = "Enter Python code into the editor to the left. Globals " + \
              "such as X, Y, Z, S are available as they are in the grid. " + \
              "The last line must result in a matplotlib figure.\n \n" + \
              "Pressing Apply displays the figure or an error message in " + \
              "the right area."

        self.message = QTextBrowser(self)
        self.message.setText(msg)
        self.editor = SpellTextEdit(self)
        self.splitter = QSplitter(self)

        buttonbox = self.create_buttonbox()

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.message)
        self.splitter.setOpaqueResize(False)
        self.splitter.setSizes([9999, 9999])

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.chart_templates_toolbar)

        layout.addWidget(self.splitter)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

    def apply(self):
        """Executes the code in the dialog and updates the canvas"""

        # Get current cell
        key = self.parent.grid.current
        code = self.editor.toPlainText()

        figure = self.parent.grid.model.code_array._eval_cell(key, code)

        if isinstance(figure, Figure):
            canvas = FigureCanvasQTAgg(figure)
            self.splitter.replaceWidget(1, canvas)
            canvas.draw()
        else:
            if isinstance(figure, Exception):
                self.message.setText("Error:\n{}".format(figure))
            else:
                msg_text = "Error:\n{} has type '{}', " + \
                           "which is no instance of {}."
                msg = msg_text.format(figure,
                                      type(figure).__name__,
                                      Figure)
                self.message.setText(msg)
            self.splitter.replaceWidget(1, self.message)

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Apply
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        return button_box
