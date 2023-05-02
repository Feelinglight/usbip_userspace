# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ok_cancel_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ok_cancel_dialog(object):
    def setupUi(self, ok_cancel_dialog):
        ok_cancel_dialog.setObjectName("ok_cancel_dialog")
        ok_cancel_dialog.resize(255, 288)
        self.verticalLayout = QtWidgets.QVBoxLayout(ok_cancel_dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.main_widget_layout = QtWidgets.QVBoxLayout()
        self.main_widget_layout.setObjectName("main_widget_layout")
        self.verticalLayout.addLayout(self.main_widget_layout)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.buttons_layout.addItem(spacerItem)
        self.accept_button = QtWidgets.QPushButton(ok_cancel_dialog)
        self.accept_button.setObjectName("accept_button")
        self.buttons_layout.addWidget(self.accept_button)
        self.cancel_button = QtWidgets.QPushButton(ok_cancel_dialog)
        self.cancel_button.setObjectName("cancel_button")
        self.buttons_layout.addWidget(self.cancel_button)
        self.verticalLayout.addLayout(self.buttons_layout)

        self.retranslateUi(ok_cancel_dialog)
        QtCore.QMetaObject.connectSlotsByName(ok_cancel_dialog)

    def retranslateUi(self, ok_cancel_dialog):
        _translate = QtCore.QCoreApplication.translate
        ok_cancel_dialog.setWindowTitle(_translate("ok_cancel_dialog", "Dialog"))
        self.accept_button.setText(_translate("ok_cancel_dialog", "Принять"))
        self.cancel_button.setText(_translate("ok_cancel_dialog", "Отмена"))
