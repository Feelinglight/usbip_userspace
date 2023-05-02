# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edited_list_widget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_edited_list_widget(object):
    def setupUi(self, edited_list_widget):
        edited_list_widget.setObjectName("edited_list_widget")
        edited_list_widget.resize(221, 288)
        font = QtGui.QFont()
        font.setPointSize(10)
        edited_list_widget.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(edited_list_widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 5, -1, 5)
        self.horizontalLayout_2.setSpacing(7)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.optional_widget_layout = QtWidgets.QVBoxLayout()
        self.optional_widget_layout.setObjectName("optional_widget_layout")
        self.horizontalLayout_2.addLayout(self.optional_widget_layout)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.add_list_item_button = QtWidgets.QPushButton(edited_list_widget)
        self.add_list_item_button.setMinimumSize(QtCore.QSize(35, 0))
        self.add_list_item_button.setMaximumSize(QtCore.QSize(35, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.add_list_item_button.setFont(font)
        self.add_list_item_button.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.add_list_item_button.setIcon(icon)
        self.add_list_item_button.setObjectName("add_list_item_button")
        self.horizontalLayout_2.addWidget(self.add_list_item_button)
        self.delete_list_item_button = QtWidgets.QPushButton(edited_list_widget)
        self.delete_list_item_button.setMinimumSize(QtCore.QSize(35, 0))
        self.delete_list_item_button.setMaximumSize(QtCore.QSize(35, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.delete_list_item_button.setFont(font)
        self.delete_list_item_button.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/minus2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delete_list_item_button.setIcon(icon1)
        self.delete_list_item_button.setObjectName("delete_list_item_button")
        self.horizontalLayout_2.addWidget(self.delete_list_item_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.list_header = QtWidgets.QLabel(edited_list_widget)
        self.list_header.setText("")
        self.list_header.setWordWrap(True)
        self.list_header.setObjectName("list_header")
        self.verticalLayout.addWidget(self.list_header)
        self.list_widget = QtWidgets.QListWidget(edited_list_widget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.list_widget.setFont(font)
        self.list_widget.setStyleSheet("selection-color: rgb(0, 0, 0);\n"
"selection-background-color: rgb(170, 170, 255);")
        self.list_widget.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.list_widget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setMovement(QtWidgets.QListView.Free)
        self.list_widget.setFlow(QtWidgets.QListView.TopToBottom)
        self.list_widget.setProperty("isWrapping", False)
        self.list_widget.setResizeMode(QtWidgets.QListView.Fixed)
        self.list_widget.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.list_widget.setViewMode(QtWidgets.QListView.ListMode)
        self.list_widget.setModelColumn(0)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setSelectionRectVisible(False)
        self.list_widget.setObjectName("list_widget")
        self.verticalLayout.addWidget(self.list_widget)

        self.retranslateUi(edited_list_widget)
        QtCore.QMetaObject.connectSlotsByName(edited_list_widget)
        edited_list_widget.setTabOrder(self.add_list_item_button, self.delete_list_item_button)
        edited_list_widget.setTabOrder(self.delete_list_item_button, self.list_widget)

    def retranslateUi(self, edited_list_widget):
        _translate = QtCore.QCoreApplication.translate
        edited_list_widget.setWindowTitle(_translate("edited_list_widget", "Form"))
        self.list_widget.setSortingEnabled(False)
from irspy.qt.resources import icons
