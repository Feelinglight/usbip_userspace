# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tstlan_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(738, 356)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.upadte_time_spinbox = QtWidgets.QDoubleSpinBox(Form)
        self.upadte_time_spinbox.setDecimals(1)
        self.upadte_time_spinbox.setMinimum(0.1)
        self.upadte_time_spinbox.setSingleStep(0.5)
        self.upadte_time_spinbox.setProperty("value", 1.5)
        self.upadte_time_spinbox.setObjectName("upadte_time_spinbox")
        self.gridLayout.addWidget(self.upadte_time_spinbox, 1, 1, 1, 1)
        self.name_filter_edit = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name_filter_edit.sizePolicy().hasHeightForWidth())
        self.name_filter_edit.setSizePolicy(sizePolicy)
        self.name_filter_edit.setObjectName("name_filter_edit")
        self.gridLayout.addWidget(self.name_filter_edit, 1, 4, 1, 1)
        self.show_marked_checkbox = QtWidgets.QCheckBox(Form)
        self.show_marked_checkbox.setObjectName("show_marked_checkbox")
        self.gridLayout.addWidget(self.show_marked_checkbox, 1, 3, 1, 1)
        self.graphs_button = QtWidgets.QPushButton(Form)
        self.graphs_button.setAutoDefault(False)
        self.graphs_button.setObjectName("graphs_button")
        self.gridLayout.addWidget(self.graphs_button, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.variables_table = QtWidgets.QTableWidget(Form)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.variables_table.setFont(font)
        self.variables_table.setObjectName("variables_table")
        self.variables_table.setColumnCount(7)
        self.variables_table.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.variables_table.setHorizontalHeaderItem(6, item)
        self.variables_table.horizontalHeader().setSortIndicatorShown(True)
        self.variables_table.horizontalHeader().setStretchLastSection(True)
        self.variables_table.verticalHeader().setVisible(False)
        self.variables_table.verticalHeader().setDefaultSectionSize(22)
        self.variables_table.verticalHeader().setMinimumSectionSize(22)
        self.verticalLayout.addWidget(self.variables_table)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.name_filter_edit.setPlaceholderText(_translate("Form", "Поиск..."))
        self.show_marked_checkbox.setText(_translate("Form", "Оставить отмеченныеs"))
        self.graphs_button.setText(_translate("Form", "Графики"))
        self.label.setText(_translate("Form", "Время обновления, с"))
        self.variables_table.setSortingEnabled(True)
        item = self.variables_table.horizontalHeaderItem(0)
        item.setText(_translate("Form", "№"))
        item = self.variables_table.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Индекс"))
        item = self.variables_table.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Имя"))
        item = self.variables_table.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Граф."))
        item = self.variables_table.horizontalHeaderItem(5)
        item.setText(_translate("Form", "Тип"))
        item = self.variables_table.horizontalHeaderItem(6)
        item.setText(_translate("Form", "Значение"))
