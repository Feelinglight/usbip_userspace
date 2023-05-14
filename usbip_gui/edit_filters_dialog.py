from typing import List, Tuple, Optional

from PyQt5 import QtWidgets, QtCore, QtGui

from common import usb
from usbip_gui.ui.py.edit_filters_dialog import Ui_edit_filters_dialog as EditFiltersForm
from qt_utils.helpers import show_error


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
        c3.setRed(int((c1.red() + c2.red()) / 2))
        c3.setGreen(int((c1.green() + c2.green()) / 2))
        c3.setBlue(int((c1.blue() + c2.blue()) / 2))
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


class EditFiltersDialog(QtWidgets.QDialog):

    FILTER_PASS_TO_COLOR = {
        '+': QtGui.QColor(177, 227, 190),
        '-': QtGui.QColor(227, 184, 177),
    }

    def __init__(self, title: str, filters: List[usb.UsbFilterRule], a_parent=None):
        super().__init__(a_parent)

        self.ui = EditFiltersForm()
        self.ui.setupUi(self)
        self.ui.filters_title_label.setText(f"Фильтры ({title})")
        self.ui.filters_list_table.setItemDelegate(
            TransparentPainterForWidget(self.ui.filters_list_table, "#d4d4ff"))
        self.show()

        self.__filters: List[usb.UsbFilterRule] = []

        self.fill_filters_table(filters)
        self.__update_toggle_button()

        self.ui.add_filter.clicked.connect(self.add_filter)
        self.ui.remove_filter.clicked.connect(self.remove_filter)
        self.ui.swap_filter_button.clicked.connect(self.toggle_filter)

        self.ui.filters_list_table.clicked.connect(self.table_clicked)

        self.ui.ok_button.clicked.connect(self.accept)
        self.ui.close_button.clicked.connect(self.reject)

    def fill_filters_table(self, filters: List[usb.UsbFilterRule]):
        for idx, filter in enumerate(filters):
            self.ui.filters_list_table.insertRow(idx)
            item = QtWidgets.QTableWidgetItem()
            filter_pass = '+' if filter.pass_ == usb.FilterRulePass.ALLOW else '-'
            item.setData(QtCore.Qt.UserRole, filter_pass)
            item.setBackground(self.FILTER_PASS_TO_COLOR[filter_pass])

            if filter.type_ == usb.FilterRuleType.CLASS:
                item.setText(usb.UsbClass(filter.rule).name.lower())
            else:
                item.setText(filter.rule)
            self.ui.filters_list_table.setItem(idx, 0, item)

    def get_selected_row(self) -> Optional[int]:
        selected_row = self.ui.filters_list_table.selectionModel().selectedRows()
        if selected_row:
            return selected_row[0].row()
        else:
            return None

    def add_filter(self):
        selected_row = self.get_selected_row()
        new_row_idx = selected_row + 1 if selected_row is not None else 0
        self.ui.filters_list_table.insertRow(new_row_idx)
        new_filter = QtWidgets.QTableWidgetItem("*")
        new_filter.setData(QtCore.Qt.UserRole, "+")
        new_filter.setBackground(self.FILTER_PASS_TO_COLOR['+'])
        self.ui.filters_list_table.setItem(new_row_idx, 0, new_filter)

    def remove_filter(self):
        selected_row = self.get_selected_row()
        if selected_row is not None:
            self.ui.filters_list_table.removeRow(selected_row)

    def toggle_filter(self):
        selected_row = self.get_selected_row()
        if selected_row is not None:
            item = self.ui.filters_list_table.item(selected_row, 0)
            current_pass = item.data(QtCore.Qt.UserRole)
            new_pass = "+" if current_pass == '-' else "-"
            item.setData(QtCore.Qt.UserRole, new_pass)
            item.setBackground(self.FILTER_PASS_TO_COLOR[new_pass])
            self.__update_toggle_button()

    def __update_toggle_button(self):
        selected_row = self.get_selected_row()
        if selected_row is not None:
            item = self.ui.filters_list_table.item(selected_row, 0)
            current_pass = item.data(QtCore.Qt.UserRole)
            icon = ":/icons/icons/disable.png" if current_pass == '-' else \
                ":/icons/icons/enable.png"
            self.ui.swap_filter_button.setIcon(QtGui.QIcon(icon))
            self.ui.swap_filter_button.setEnabled(True)
        else:
            self.ui.swap_filter_button.setEnabled(False)

    def table_clicked(self, _):
        self.__update_toggle_button()

    def get_filters(self):
        self.__filters.clear()
        for i in range(self.ui.filters_list_table.rowCount()):
            item = self.ui.filters_list_table.item(i, 0)
            if item.text():
                pass_str = item.data(QtCore.Qt.UserRole)

                filter_pass = usb.FilterRulePass.ALLOW if pass_str == '+' else \
                    usb.FilterRulePass.FORBID
                try:
                    rule = usb.usb_class_from_name(item.text()).value
                    filter_type = usb.FilterRuleType.CLASS
                except KeyError:
                    rule = item.text()
                    filter_type = usb.FilterRuleType.VID_PID

                self.__filters.append(usb.UsbFilterRule(
                    filter_pass,
                    filter_type,
                    rule,
                ))
        return self.__filters

    def __save_filters(self):
        self.__filters = []

    def ok_pressed(self):
        self.__save_filters()
        self.accept()

