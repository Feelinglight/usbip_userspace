from typing import Iterable, Union
from math import isclose
import logging

from PyQt5 import QtCore, QtWidgets, QtGui

import irspy.constants as constants


QSTYLE_COLOR_WHITE = "background-color: rgb(255, 255, 255);"
QSTYLE_COLOR_YELLOW = "background-color: rgb(250, 250, 170);"
QSTYLE_COLOR_RED = "background-color: rgb(245, 206, 203);"


def update_edit_color(a_actual_value, a_current_value, a_edit: QtWidgets.QLineEdit):
    try:
        if isclose(a_actual_value, float(a_current_value), rel_tol=constants.FLOAT_EPSILON):
            a_edit.setStyleSheet(QSTYLE_COLOR_WHITE)
        else:
            a_edit.setStyleSheet(QSTYLE_COLOR_YELLOW)
    except ValueError:
        a_edit.setStyleSheet(QSTYLE_COLOR_RED)


def get_wheel_steps(event: QtGui.QWheelEvent):
    degrees_num = event.angleDelta() / 8
    steps_num = degrees_num / 15
    return steps_num.y()


def qtablewidget_append_row(a_table: QtWidgets.QTableWidget, a_row_data: Iterable):
    """
    Вставляет в конец QTableWidget строку с QTableWidgetItem's, содержащими текст из a_row_data
    :param a_table: QTableWidget
    :param a_row_data: Данные, которые будут вставлены в таблицу
    """
    row_num = a_table.rowCount()
    a_table.insertRow(row_num)
    for col, data in enumerate(a_row_data):
        a_table.setItem(row_num, col, QtWidgets.QTableWidgetItem(str(data)))


def get_selected_row(a_qtablewidget: QtWidgets.QTableWidget):
    rows = a_qtablewidget.selectionModel().selectedRows()
    return None if not rows else rows[0].row()


def qtablewidget_delete_selected(a_table: QtWidgets.QTableWidget):
    rows = a_table.selectionModel().selectedRows()
    if rows:
        for idx_model in reversed(rows):
            a_table.removeRow(idx_model.row())


def qtablewidget_get_only_selected_cell(a_table_widget: QtWidgets.QTableWidget) -> Union[None, QtCore.QModelIndex]:
    selected_indexes = a_table_widget.selectionModel().selectedIndexes()
    if len(selected_indexes) == 1:
        return selected_indexes[0]
    elif len(selected_indexes) > 1:
        QtWidgets.QMessageBox.critical(None, "Ошибка", "Необходимо выбрать ровно одну ячейку",
                                       QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
    else:
        return None


def qtablewidget_get_only_selected_row(a_table_widget: QtWidgets.QTableWidget) -> Union[None, int]:
    selected_indexes = a_table_widget.selectionModel().selectedRows()
    if len(selected_indexes) == 1:
        return selected_indexes[0].row()
    elif len(selected_indexes) > 1:
        QtWidgets.QMessageBox.critical(None, "Ошибка", "Необходимо выбрать ровно одну строку",
                                       QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
    return None


def wrap_in_layout(a_widget: QtWidgets.QWidget):
    """
    Заворачивает виджет в layout. Нужно для вставки виджетов в ячейки таблицы, при вставке как есть, виджеты
    не выравниваются в ячейке
    """
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout(widget)
    layout.addWidget(a_widget)
    layout.setAlignment(QtCore.Qt.AlignCenter)
    layout.setContentsMargins(0, 0, 0, 0)
    return widget


def unwrap_from_layout(a_widget: QtWidgets.QWidget):
    """
    Достает виджет из layout'а, см. wrap_in_layout выше
    """
    return a_widget.layout().itemAt(0).widget()


def open_or_activate_dialog(a_dialog_object_name: str, a_dialog_parent, a_dialog: QtWidgets.QDialog, *args, **kwargs):
    """
    Проверяет, открыт ли диалог с заданным именем, если не открыт, то открывает его, иначе просто активирует
    :param a_dialog_object_name: Имя диалога
    :param a_dialog_parent: Родитель диалога
    :param a_dialog: Объект диалога
    :param args: Аргументы конструктора диалога
    :param kwargs: Аргументы конструктора диалога
    :return: Объект диалога
    """
    dialog = a_dialog_parent.findChild(QtWidgets.QDialog, a_dialog_object_name)
    if dialog:
        dialog.activateWindow()
    else:
        dialog = a_dialog(*args, **kwargs)
        dialog.exec()
    return dialog


class TableHeaderContextMenu:
    """
    Добавляет к хэдеру QTableView контекстное меню, которое содержит чекбоксы для сокрытия его колонок
    Перед закрытием виджета QTableView необходимо вызвать self.delete_connections(), иначе лямбда соединения могут
    помешать удалению ссылающихся на них объектов (по хорошему надо переписать на слабые ссылки)
    """
    def __init__(self, a_parent: QtWidgets.QWidget, a_table: QtWidgets.QTableView, a_hide_first_column: bool = False):
        table_header = a_table.horizontalHeader()
        table_header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.table = a_table
        self.hide_first_col = a_hide_first_column
        self.menu = QtWidgets.QMenu(a_parent)
        self.lambda_connections = []
        for column in range(a_table.model().columnCount()):
            if column == 0 and a_hide_first_column:
                continue
            header_name = a_table.model().headerData(column, QtCore.Qt.Horizontal)
            menu_checkbox = QtWidgets.QAction(header_name, self.menu)
            menu_checkbox.setCheckable(True)
            if not a_table.isColumnHidden(column):
                menu_checkbox.setChecked(True)
            self.menu.addAction(menu_checkbox)

            self.lambda_connections.append((menu_checkbox.triggered, menu_checkbox.triggered.connect(
                lambda state, col=column: a_table.setColumnHidden(col, not state))))

        self.lambda_connections.append((table_header.customContextMenuRequested,
                                        table_header.customContextMenuRequested.connect(self.show_context_menu)))

    def show_context_menu(self, a_position):
        self.menu.popup(self.table.horizontalHeader().viewport().mapToGlobal(a_position))
        for column, action in enumerate(self.menu.actions()):
            col_idx = column + 1 if self.hide_first_col else column
            action.setChecked(not self.table.isColumnHidden(col_idx))

    def delete_connections(self):
        # Нужно потому что лямбда соединения сами не удаляются
        for signal, connection in self.lambda_connections:
            signal.disconnect(connection)


class QTextEditLogger(logging.Handler):
    """
    Связывает QTextEdit и logging. Выделяет разные уровни сообщений цветом.
    """
    def __init__(self, a_text_edit: QtWidgets.QTextEdit):
        super().__init__()

        assert type(a_text_edit) is QtWidgets.QTextEdit

        self.text_edit = a_text_edit

    def emit(self, record):
        msg = self.format(record)

        if record.levelno == logging.CRITICAL:
            color = QtCore.Qt.darkRed
        elif record.levelno == logging.ERROR:
            color = QtCore.Qt.red
        elif record.levelno == logging.WARNING:
            color = QtCore.Qt.darkYellow
        elif record.levelno == logging.INFO:
            color = QtCore.Qt.blue
        else:  # DEBUG or NOTSET
            color = QtCore.Qt.black

        self.text_edit.setTextColor(color)
        self.text_edit.insertPlainText(msg + '\n')
        self.text_edit.ensureCursorVisible()
