from typing import Dict, Tuple
from enum import IntEnum
import numbers
import sys

from PyQt5 import QtGui, QtWidgets, QtCore

from irspy.qt.custom_widgets.QTableDelegates import ComboboxIgnoreWheel, SpinboxIgnoreWheel
from irspy.qt.custom_widgets.CustomLineEdit import QEditDoubleClick
from irspy.qt import qt_utils
import irspy.utils as utils


class ObjectFieldsVisualizer(QtWidgets.QWidget):
    """
    Виджет для визуализации и изменения полей других классов
    Содержит таблицу, которая может выводить некоторые типы данных и изменять их
    Пример использования внизу
    """
    class Column(IntEnum):
        PARAMETER = 0
        VALUE = 1

    PARAMETER_TO_NAME = {
        Column.PARAMETER: "Параметр",
        Column.VALUE: "Значение"
    }

    def __init__(self, a_variables_owner: object, a_parent=None):
        super().__init__(a_parent)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.__settings_table = QtWidgets.QTableWidget()
        self.__settings_table.setColumnCount(2)
        self.__settings_table.setHorizontalHeaderLabels([
            ObjectFieldsVisualizer.PARAMETER_TO_NAME[ObjectFieldsVisualizer.Column.PARAMETER],
            ObjectFieldsVisualizer.PARAMETER_TO_NAME[ObjectFieldsVisualizer.Column.VALUE],
        ])
        self.__settings_table.horizontalHeader().setStretchLastSection(True)
        self.__settings_table.setWordWrap(True)
        self.layout().addWidget(self.__settings_table)

        self.__variables_owner = a_variables_owner
        self.__fields: Dict[str, Tuple[str, type]] = {}
        self.__widget_rows = {}

    def add_new_name(self, a_name):
        row = self.__settings_table.rowCount()
        self.__settings_table.insertRow(row)
        self.__settings_table.setItem(row, ObjectFieldsVisualizer.Column.PARAMETER, QtWidgets.QTableWidgetItem(a_name))
        return row

    def get_object_field_by_row(self, a_row):
        name = self.__settings_table.item(a_row, ObjectFieldsVisualizer.Column.PARAMETER).text()
        return self.__fields[name]

    def add_parameter_to_table(self, a_name: str, a_object_field, a_widget: QtWidgets.QWidget, a_type):
        row = self.add_new_name(a_name)
        self.__settings_table.setCellWidget(row, ObjectFieldsVisualizer.Column.VALUE, a_widget)

        self.__widget_rows[a_widget] = row
        self.__fields[a_name] = (a_object_field, a_type)

    def get_parameter_name_type(self, a_widget: QtWidgets.QWidget):
        row = self.__widget_rows[a_widget]
        name, type_ = self.get_object_field_by_row(row)
        return name, type_

    def add_combobox_param(self, a_name, a_object_field, a_value: Dict):
        items = list(a_value.keys())[0]
        assert all(map(lambda el: type(items[0]) == type(el), items)), \
            "Все элементы последовательности должны быть одного типа"

        combobox = ComboboxIgnoreWheel(self.__settings_table)
        combobox.setModel(QtCore.QStringListModel())
        combobox.addItems((str(item) for item in items))
        combobox.setCurrentIndex(list(a_value.values())[0])

        self.add_parameter_to_table(a_name, a_object_field, combobox, type(items[0]))
        combobox.currentIndexChanged.connect(self.set_combobox_param)

    def set_combobox_param(self, a_idx: int):
        combobox = self.sender()
        object_field, type_ = self.get_parameter_name_type(combobox)
        set_new_dict = tuple(type_(item) for item in combobox.model().stringList())
        setattr(self.__variables_owner, object_field, {set_new_dict: a_idx})

    def add_checkbox_param(self, a_name, a_object_field, a_value):
        checkbox = QtWidgets.QCheckBox(self.__settings_table)
        checkbox.setChecked(a_value)
        cb_widget = qt_utils.wrap_in_layout(checkbox)

        row = self.add_new_name(a_name)
        self.__settings_table.setCellWidget(row, ObjectFieldsVisualizer.Column.VALUE, cb_widget)

        self.__widget_rows[checkbox] = row
        self.__fields[a_name] = (a_object_field, bool)

        checkbox.toggled.connect(self.set_checkbox_param)

    @utils.exception_decorator_print
    def set_checkbox_param(self, a_enable):
        object_field, type_ = self.get_parameter_name_type(self.sender())
        setattr(self.__variables_owner, object_field, type_(a_enable))

    def add_spinbox_param(self, a_name, a_object_field, a_value):
        spinbox = SpinboxIgnoreWheel(self.__settings_table)
        spinbox.setMinimum(0)
        spinbox.setMaximum(1000000)
        spinbox.setValue(a_value)

        self.add_parameter_to_table(a_name, a_object_field, spinbox, int)
        spinbox.valueChanged.connect(self.set_spinbox_param)

    def set_spinbox_param(self, a_value):
        name, type_ = self.get_parameter_name_type(self.sender())
        setattr(self.__variables_owner, name, type_(a_value))

    def add_float_edit_param(self, a_name, a_object_field, a_value):
        edit = QEditDoubleClick(self.__settings_table)
        edit.setText(utils.float_to_string(a_value))

        self.add_parameter_to_table(a_name, a_object_field, edit, float)
        edit.editingFinished.connect(self.set_float_edit_param)

    @utils.exception_decorator_print
    def set_float_edit_param(self):
        edit = self.sender()
        object_field, type_ = self.get_parameter_name_type(edit)
        try:
            value = utils.parse_input(edit.text())
            edit.setText(utils.float_to_string(value))
            setattr(self.__variables_owner, object_field, type_(value))
        except ValueError:
            edit.setText("0")
            setattr(self.__variables_owner, object_field, type_(0.))

    def add_string_param(self, a_name, a_object_field, a_value):
        edit = QEditDoubleClick(self.__settings_table)
        edit.setText(a_value)

        self.add_parameter_to_table(a_name, a_object_field, edit, str)
        edit.textChanged.connect(self.set_edit_param)

    def set_edit_param(self):
        edit = self.sender()
        object_field, type_ = self.get_parameter_name_type(edit)

        value_str = edit.text()
        edit.setText(value_str)
        setattr(self.__variables_owner, object_field, type_(value_str))

    def add_setting(self, a_name, a_object_field):
        if a_object_field in self.__fields:
            raise ValueError(f"Параметр {a_object_field} уже существует")

        value = getattr(self.__variables_owner, a_object_field)

        if isinstance(value, str):
            # Проверка на str должна быть перед Sequence!
            self.add_string_param(a_name, a_object_field, value)
        elif isinstance(value, dict) and len(value) == 1 and \
                all([isinstance(k, tuple) and isinstance(v, numbers.Integral) for k, v in value.items()]):
            self.add_combobox_param(a_name, a_object_field, value)
        elif isinstance(value, bool):
            self.add_checkbox_param(a_name, a_object_field, value)
        elif isinstance(value, numbers.Integral):
            self.add_spinbox_param(a_name, a_object_field, value)
        elif isinstance(value, numbers.Real):
            self.add_float_edit_param(a_name, a_object_field, value)
        else:
            raise TypeError(f'Параметр "{a_object_field}"; Неподдерживаемый тип параметра {type(value)}')

        self.__settings_table.resizeColumnsToContents()
        self.__settings_table.resizeRowsToContents()


if __name__ == "__main__":

    class PropertyHolder:
        def __init__(self):
            self.bool_field = True
            self.bool_field2 = False
            self.int_field = 33
            self.float_field = 33.
            self.str_field = 'haha'
            self.list_field = {(1, 2, 3, 4): 2}

        def __repr__(self):
            return f"{self.bool_field}\n" \
                   f"{self.int_field}\n" \
                   f"{self.float_field}\n" \
                   f"{self.str_field}\n" \
                   f"{self.list_field}\n" \



    @utils.exception_decorator_print
    def test():
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle("Fusion")
        window = QtWidgets.QMainWindow()
        window.setLayout(QtWidgets.QGridLayout())

        cls = PropertyHolder()
        settings = ObjectFieldsVisualizer(cls)

        settings.add_setting("Bool", "bool_field")
        settings.add_setting("Bool2", "bool_field2")
        settings.add_setting("Integral", "int_field")
        settings.add_setting("Float", "float_field")
        settings.add_setting("String", "str_field")
        settings.add_setting("List", "list_field")

        window.setCentralWidget(settings)
        window.show()
        app.exec()

        print(cls)


    test()
