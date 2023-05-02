# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_with_text.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dialog_with_text(object):
    def setupUi(self, dialog_with_text):
        dialog_with_text.setObjectName("dialog_with_text")
        dialog_with_text.resize(558, 559)
        dialog_with_text.setSizeGripEnabled(False)
        self.gridLayout = QtWidgets.QGridLayout(dialog_with_text)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QTextEdit(dialog_with_text)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.textEdit.setFont(font)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

        self.retranslateUi(dialog_with_text)
        QtCore.QMetaObject.connectSlotsByName(dialog_with_text)

    def retranslateUi(self, dialog_with_text):
        _translate = QtCore.QCoreApplication.translate
        dialog_with_text.setWindowTitle(_translate("dialog_with_text", "Dialog"))
        self.textEdit.setPlaceholderText(_translate("dialog_with_text", "Здесь мог бы быть ваш текст"))
