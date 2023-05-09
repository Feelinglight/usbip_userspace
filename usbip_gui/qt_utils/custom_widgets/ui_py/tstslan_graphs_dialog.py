# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tstslan_graphs_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_tstlan_graphs_dialog(object):
    def setupUi(self, tstlan_graphs_dialog):
        tstlan_graphs_dialog.setObjectName("tstlan_graphs_dialog")
        tstlan_graphs_dialog.resize(838, 554)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/graph_2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        tstlan_graphs_dialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(tstlan_graphs_dialog)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.chart_layout = QtWidgets.QHBoxLayout()
        self.chart_layout.setObjectName("chart_layout")
        self.verticalLayout.addLayout(self.chart_layout)

        self.retranslateUi(tstlan_graphs_dialog)
        QtCore.QMetaObject.connectSlotsByName(tstlan_graphs_dialog)

    def retranslateUi(self, tstlan_graphs_dialog):
        _translate = QtCore.QCoreApplication.translate
        tstlan_graphs_dialog.setWindowTitle(_translate("tstlan_graphs_dialog", "Графики tstlan"))
from irspy.qt.resources import icons
