# -*- coding: utf-8 -*-

import os
import importlib

from PyQt5 import QtWidgets, QtGui, QtCore

from icons import Icon


PY_EXTRAS = (
    ["xlrd", ">=0.9.2", "loading excel files"],
    ["xlwt", ">=0.9.2", "saving excel files"],
    ["jedi", "(>=0.8.0", "for tab completion and context help in the entry line"],
    ["pyrsvg", ">=2.32", "displaying SVG files in cells"],
    ["pyenchant", ">=1.1",  "spell checking"],
    ["basemap", ">=1.0.7", "for the weather example pys file"],
)

def is_lib_installed(name):
    """Attempts to import lib
    :param name: Lib to load eg xwrd"""
    try:
        importlib.import_module(name)
        return True
    except Exception as e:
        print(e)
        pass
    return False

class InstallerDialog(QtWidgets.QDialog):
    """Installer dialog for python dependencies"""

    class C:
        """Column nos"""
        button = 0
        status = 1
        package = 2
        version = 3
        description = 4

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Installer")
        self.setMinimumWidth(600)

        ## Button group for install buttons
        self.selIdx = None
        self.buttGroup = QtWidgets.QButtonGroup()
        self.buttGroup.buttonClicked.connect(self.on_butt_install)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10,10,10,10)
        self.setLayout(self.mainLayout)

        self.tree = QtWidgets.QTreeWidget()
        self.mainLayout.addWidget(self.tree, 4)

        self.tree.setHeaderLabels(["","Status", "Package", "Version", "Description"])
        self.tree.setRootIsDecorated(False)
        #self.tree.setSelectionMode(NoSelection ?)


        self.load()

    def load(self):

        C = self.C
        self.tree.clear()

        for idx, package in enumerate(PY_EXTRAS):
            pkg, ver, desc = package

            item = QtWidgets.QTreeWidgetItem()
            item.setText(C.package, pkg)
            item.setText(C.version, ver)
            item.setText(C.description, desc)
            self.tree.addTopLevelItem(item)


            if not is_lib_installed(pkg):
                status = "Not installed"
                color = "#F3FFBB"
                butt = QtWidgets.QToolButton()
                butt.setText("Install")
                self.tree.setItemWidget(item, C.button, butt)
                self.buttGroup.addButton(butt, idx)
            else:
                color = "#DBFEAC"
                status = "Installed"

            item.setText(C.status, status)
            item.setBackground(C.status, QtGui.QColor(color))


    def on_butt_install(self, butt):
        """One of install buttons pressed"""

        idx = self.buttGroup.id(butt)
        butt.setDisabled(True)

        dial = InstallPackageDialog(self, package=PY_EXTRAS[idx])
        dial.exec_()
        self.load()


    def update_cmd_line(self, *unused):

        pkg, ver, desc  = PY_EXTRAS[self.selIdx]

        print("Install: %s" % pkg)
        ## Umm ?? sudo, virtual env ??
        # its gonna be > pip3 install foo ?
        cmd = ""
        if self.buttSudo.isChecked():
            cmd += "sudo "

        cmd += "pip3 install %s" % pkg

        self.txtCommand.setText(cmd)

    def on_butt_execute(self):
        self.buttSudo.setDisabled(True)
        self.buttExecute.setDisabled(True)




class InstallPackageDialog(QtWidgets.QDialog):
    """Shows a dialog to execute command"""


    def __init__(self, parent=None, package=None):
        super().__init__(parent)

        self.setWindowTitle("Install Package")
        self.setMinimumWidth(600)

        self.package = package

        self.process = QtCore.QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_read_standard)
        self.process.readyReadStandardError.connect(self.on_read_error)
        self.process.finished.connect(self.on_finished)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10,10,10,10)
        self.setLayout(self.mainLayout)

        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setTitle("Shell Command")
        self.groupBoxLayout = QtWidgets.QHBoxLayout()
        self.groupBox.setLayout(self.groupBoxLayout)
        self.mainLayout.addWidget(self.groupBox)

        self.buttSudo = QtWidgets.QPushButton()
        self.buttSudo.setText("Sudo")
        self.buttSudo.setCheckable(True)
        self.groupBoxLayout.addWidget(self.buttSudo, 0)
        self.buttSudo.toggled.connect(self.update_cmd_line)

        self.txtCommand = QtWidgets.QLineEdit()
        self.groupBoxLayout.addWidget(self.txtCommand, 10)

        self.buttExecute = QtWidgets.QPushButton()
        self.buttExecute.setText("Execute")
        self.groupBoxLayout.addWidget(self.buttExecute, 0)
        self.buttExecute.clicked.connect(self.on_butt_execute)

        self.txtStdOut = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdOut)

        self.txtStdErr = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdErr)

        self.update_cmd_line()

    def update_cmd_line(self, *unused):

        if os.name == "nt":
            self.buttSudo.hide()

        pkg = self.package[0]

        ## Umm ?? sudo, virtual env ??
        # its gonna be > pip3 install foo ?
        cmd = ""
        if self.buttSudo.isChecked():
            cmd += "sudo "

        cmd += "pip3 install %s" % pkg

        self.txtCommand.setText(cmd)

    def on_butt_execute(self):
        self.buttSudo.setDisabled(True)
        self.buttExecute.setDisabled(True)

        self.process.start(self.txtCommand.text())

    def on_read_standard(self):
        c = str(self.txtStdOut.toPlainText())
        s = str(self.process.readAllStandardOutput())

        ss = c + "\n-------------------------------------------------------\n" + s

        self.txtStdOut.setPlainText(ss)
        self.txtStdOut.moveCursor(QtGui.QTextCursor.End)

    def on_read_error(self):
        c = str(self.txtStdErr.toPlainText())
        s = str(self.process.readAllStandardError())
        # print "errro-", s
        ss = c + "\n-------------------------------------------------------\n" + s
        self.txtStdErr.setPlainText(ss)
        self.txtStdErr.moveCursor(QtGui.QTextCursor.End)

    def on_finished(self):
        pass

