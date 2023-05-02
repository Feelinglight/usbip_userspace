from typing import Tuple
import logging

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget

from irspy.qt.custom_widgets.CustomLineEdit import QEditDoubleClick

from irspy.utils import exception_decorator_print


class TransparentPainterForView(QtWidgets.QStyledItemDelegate):
    """
    Делегат для рисования выделения ячеек QTableView прозрачным цветом
    """
    def __init__(self, a_parent=None, a_default_color="#f5f0f0"):
        """
        :param a_default_color: Цвет выделения
        """
        super().__init__(a_parent)
        self.color_default = QtGui.QColor(a_default_color)

    @exception_decorator_print
    def paint(self, painter, option, index):
        if option.state & QtWidgets.QStyle.State_Selected:
            option.palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
            color = self.combineColors(self.color_default, self.background(option, index))
            option.palette.setColor(QtGui.QPalette.Highlight, color)
        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

    def background(self, option, index):
        background = index.data(QtCore.Qt.BackgroundRole)
        if background != QtGui.QBrush():
            return background.color()
        if self.parent().alternatingRowColors():
            if index.row() % 2 == 1:
                return option.palette.color(QtGui.QPalette.AlternateBase)
        return option.palette.color(QtGui.QPalette.Base)

    @staticmethod
    def combineColors(c1, c2):
        c3 = QtGui.QColor()
        c3.setRed((c1.red() + c2.red()) / 2)
        c3.setGreen((c1.green() + c2.green()) / 2)
        c3.setBlue((c1.blue() + c2.blue()) / 2)
        return c3


class TransparentPainterForWidget(TransparentPainterForView):
    """
    Делегат для рисования выделения ячеек QTableWidget прозрачным цветом
    """
    def __init__(self, a_parent=None, a_default_color="#f5f0f0"):
        """
        :param a_default_color: Цвет выделения
        """
        super().__init__(a_parent, a_default_color)
        self.color_default = QtGui.QColor(a_default_color)

    def background(self, option, index):
        item = self.parent().itemFromIndex(index)
        if item:
            if item.background() != QtGui.QBrush():
                return item.background().color()
        if self.parent().alternatingRowColors():
            if index.row() % 2 == 1:
                return option.palette.color(QtGui.QPalette.AlternateBase)
        return option.palette.color(QtGui.QPalette.Base)


class TableEditDoubleClick(QtWidgets.QItemDelegate):
    def __init__(self, a_parent):
        super().__init__(a_parent)

    def createEditor(self, parent: QWidget, option, index: QtCore.QModelIndex) -> QWidget:
        return QEditDoubleClick(parent)


class ComboboxIgnoreWheel(QtWidgets.QComboBox):
    def __init__(self, a_parent):
        super().__init__(a_parent)

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        e.ignore()


class SpinboxIgnoreWheel(QtWidgets.QSpinBox):
    def __init__(self, a_parent):
        super().__init__(a_parent)

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        e.ignore()


class ComboboxCellDelegate(QtWidgets.QItemDelegate):
    """
    Делегат для задания комбобокса в ячейки таблицы
    """
    def __init__(self, a_parent: QtCore.QObject, a_values: Tuple):
        super().__init__(a_parent)
        self.cb_values = a_values

    def createEditor(self, parent: QWidget, option, index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        editor = ComboboxIgnoreWheel(parent)
        for val in self.cb_values:
            editor.addItem(val)
        editor.setCurrentText(index.data())
        return editor

    def setEditorData(self, editor: QWidget, index: QtCore.QModelIndex) -> None:
        editor.setCurrentText(index.data())
