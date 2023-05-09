from collections import OrderedDict
from typing import List, Iterable
from sys import float_info

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal

from irspy.qt.custom_widgets.CustomLineEdit import QEditDoubleClick
from irspy.qt.custom_widgets.ui_py.edited_list_widget import Ui_edited_list_widget as EditedListForm
from irspy.qt.custom_widgets.ui_py.ok_cancel_dialog import Ui_ok_cancel_dialog as OkCancelForm
import irspy.utils as utils


class EditedListWidget(QtWidgets.QWidget):
    """
    Класс для контролируемого ввода в QListWidget. Можно унаследоваться и перегрузить process_input и get_list,
    чтобы QListWidget подстраивал ввод в нужном формате
    """
    def __init__(self, parent=None, a_init_items=(), a_min_value=None, a_max_value=None,
                 a_optional_widget=None, a_list_header=""):
        super().__init__(parent)

        self.ui = EditedListForm()
        self.ui.setupUi(self)
        if a_optional_widget is not None:
            self.ui.optional_widget_layout.addWidget(a_optional_widget)

        if not a_list_header:
            self.ui.list_header.hide()
        else:
            self.ui.list_header.setText(a_list_header)

        self.min_value = a_min_value if a_min_value is not None else float_info.min
        self.max_value = a_max_value if a_max_value is not None else float_info.max

        self.delete_key_sc = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self.ui.list_widget)
        self.delete_key_sc.activated.connect(self.delete_selected_row)

        self.ui.add_list_item_button.clicked.connect(self.add_list_item_button_clicked)
        self.ui.delete_list_item_button.clicked.connect(self.delete_selected_row)

        for item in a_init_items:
            self.add_item(item, False)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if self.ui.list_widget.hasFocus():
            key = event.key()
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                rows = self.ui.list_widget.selectedItems()
                if rows:
                    self.ui.list_widget.editItem(rows[0])
        else:
            event.accept()

    def item_editing_finished(self, a_index: QtCore.QModelIndex):
        edit = self.ui.list_widget.itemFromIndex(a_index)
        edit.setText(self.process_input(edit.text()))

    def process_input(self, a_input: str):
        return a_input

    def bound_input(self, a_value):
        return utils.bound(a_value, self.min_value, self.max_value)

    def add_item(self, a_init_value="0", a_edit_item=True):
        list_item = QtWidgets.QListWidgetItem(self.process_input(a_init_value), self.ui.list_widget)
        list_item.setFlags(int(list_item.flags()) | QtCore.Qt.ItemIsEditable)
        self.ui.list_widget.addItem(list_item)
        self.ui.list_widget.setCurrentItem(list_item)
        if a_edit_item:
            self.ui.list_widget.editItem(list_item)

    def delete_selected_row(self):
        self.ui.list_widget.takeItem(self.ui.list_widget.currentRow())

    def add_list_item_button_clicked(self):
        self.add_item()

    def get_list(self):
        out_list = []
        for idx in range(self.ui.list_widget.count()):
            item = self.ui.list_widget.item(idx).text()
            if item not in out_list:
                out_list.append(item)
        return out_list


class QRegExpDelegator(QtWidgets.QItemDelegate):
    editing_finished = pyqtSignal(QtCore.QModelIndex)

    def __init__(self, parent, a_regexp_pattern):
        super().__init__(parent)
        self.regexp_pattern = a_regexp_pattern

    def createEditor(self, parent: QtWidgets.QWidget, option, index: QtCore.QModelIndex):
        edit = QEditDoubleClick(parent)
        regex = QtCore.QRegExp(self.regexp_pattern)
        validator = QtGui.QRegExpValidator(regex, parent)
        edit.setValidator(validator)
        return edit

    def destroyEditor(self, editor: QEditDoubleClick, index: QtCore.QModelIndex):
        self.editing_finished.emit(index)
        return super().destroyEditor(editor, index)


class EditedListOnlyNumbers(EditedListWidget):
    def __init__(self, parent=None, a_init_items: Iterable[float] = (), a_min_value=None, a_max_value=None,
                 a_optional_widget=None, a_list_header=""):
        str_items = (str(item) for item in a_init_items)
        super().__init__(parent, str_items, a_min_value, a_max_value, a_optional_widget, a_list_header)

        delegator = QRegExpDelegator(self, utils.find_number_re.pattern)
        delegator.editing_finished.connect(self.item_editing_finished)
        self.ui.list_widget.setItemDelegate(delegator)

    def process_input(self, a_input: str):
        value = float(a_input.replace(",", "."))
        value = self.bound_input(value)
        return utils.float_to_string(value)

    def get_list(self):
        out_list = []
        for idx in range(self.ui.list_widget.count()):
            item = float(self.ui.list_widget.item(idx).text().replace(',', '.'))
            if item not in out_list:
                out_list.append(item)
        return out_list


class EditedListWithUnits(EditedListWidget):
    def __init__(self, parent=None, units: str = "В", a_init_items=(), a_min_value=None, a_max_value=None,
                 a_optional_widget=None):
        self.value_to_user = utils.value_to_user_with_units(units)
        items_with_units = (self.value_to_user(item) for item in a_init_items)
        super().__init__(parent, items_with_units, a_min_value, a_max_value, a_optional_widget)

        delegator = QRegExpDelegator(self, utils.check_input_no_python_re.pattern)
        delegator.editing_finished.connect(self.item_editing_finished)
        self.ui.list_widget.setItemDelegate(delegator)

    def process_input(self, a_input: str):
        try:
            processed_value = utils.parse_input(a_input)
            processed_value = self.bound_input(processed_value)
        except ValueError:
            processed_value = self.bound_input(0)
        return self.value_to_user(processed_value)

    def get_list(self) -> List[float]:
        out_list = []
        try:
            for idx in range(self.ui.list_widget.count()):
                item = self.ui.list_widget.item(idx).text()
                if item not in out_list:
                    out_list.append(utils.parse_input(item))
            return out_list
        except ValueError:
            return list()

    def sort_list(self):
        items = OrderedDict()
        for idx in range(self.ui.list_widget.count()):
            text = self.ui.list_widget.item(idx).text()
            value = utils.parse_input(text)
            items[value] = text
        self.ui.list_widget.clear()
        items = OrderedDict(sorted(items.items()))
        for value in items.values():
            self.ui.list_widget.addItem(QtWidgets.QListWidgetItem(value))
        return list(items.keys())


class OkCancelDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, a_title="dialog"):
        super().__init__(parent)

        self.ui = OkCancelForm()
        self.ui.setupUi(self)
        self.setObjectName("ok_cancel_" + a_title)
        self.setWindowTitle(a_title)
        self.main_widget = None

        self.ui.accept_button.clicked.connect(self.accept)
        self.ui.cancel_button.clicked.connect(self.reject)

    def set_main_widget(self, a_widget: QtWidgets.QWidget):
        self.main_widget = a_widget
        self.ui.main_widget_layout.addWidget(self.main_widget)

    def get_main_widget(self):
        return self.main_widget
