from typing import Tuple, Dict, List
from enum import IntEnum
from math import floor
import logging
import time

from PyQt5 import QtGui, QtWidgets, QtCore

from irspy.qt.custom_widgets.ui_py.tstlan_dialog import Ui_tstlan_dialog as TstlanForm
from irspy.qt.custom_widgets.tstlan_graph_dialog import TstlanGraphDialog
from irspy.qt.qt_settings_ini_parser import QtSettings
from irspy.clb.clb_dll import ClbDrv
import irspy.clb.network_variables as nv
import irspy.utils as utils


class TstlanDialog(QtWidgets.QDialog):
    class Column(IntEnum):
        NUMBER = 0
        INDEX = 1
        MARK = 2
        NAME = 3
        GRAPH = 4
        TYPE = 5
        VALUE = 6

    def __init__(self, a_variables: nv.NetworkVariables, a_calibrator: ClbDrv,
                 a_settings: QtSettings, a_parent=None):
        super().__init__(a_parent)

        self.ui = TstlanForm()
        self.ui.setupUi(self)
        self.show()

        self.netvars = a_variables
        self.calibrator = a_calibrator

        self.settings = a_settings
        self.settings.restore_qwidget_state(self)

        self.variables_to_graph: Dict[str, nv.BufferedVariable] = {}
        self.graphs_data: Dict[str, Tuple[List[float], List[float]]] = {}
        self.ui.graphs_button.clicked.connect(self.show_graphs)
        self.start_timestamp = time.time()
        self.graphs_dialog = None

        # Обязательно вызывать до восстановления состояния таблицы !!!
        self.fill_variables_table()

        self.settings.restore_qwidget_state(self.ui.variables_table)
        self.ui.variables_table.resizeRowsToContents()

        self.ui.show_marked_checkbox.setChecked(self.settings.tstlan_show_marks)

        self.ui.upadte_time_spinbox.setValue(self.settings.tstlan_update_time)

        self.read_variables_timer = QtCore.QTimer(self)
        self.read_variables_timer.timeout.connect(self.read_variables)
        self.read_variables_timer.start(self.ui.upadte_time_spinbox.value() * 1000)

        self.ui.variables_table.itemChanged.connect(self.write_variable)
        self.ui.name_filter_edit.textChanged.connect(self.filter_variables)
        self.ui.upadte_time_spinbox.valueChanged.connect(self.update_time_changed)
        self.ui.show_marked_checkbox.toggled.connect(self.show_marked_toggled)

        self.filter_variables()

    def __del__(self):
        print("tstlan deleted")

    # noinspection PyTypeChecker
    def fill_variables_table(self):
        for row, variable in enumerate(self.netvars.get_variables_info()):
            if variable.name:
                self.ui.variables_table.insertRow(row)
                index = variable.index if variable.type != "bit" else f"{variable.index}.{variable.bit_index}"

                item = NumberTableWidgetItem(f"{variable.number}")
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.ui.variables_table.setItem(row, self.Column.NUMBER, item)

                item = NumberTableWidgetItem(f"{index}")
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.ui.variables_table.setItem(row, self.Column.INDEX, item)

                try:
                    mark_state = self.settings.tstlan_marks[row]
                except IndexError:
                    mark_state = False
                mark_widget, _ = self.create_table_checkbox(mark_state)
                self.ui.variables_table.setCellWidget(row, self.Column.MARK, mark_widget)

                try:
                    graph_state = self.settings.tstlan_graphs[row]
                except IndexError:
                    graph_state = False
                graph_widget, graph_cb = self.create_table_checkbox(graph_state)
                graph_cb.toggled.connect(self.graph_checkbox_clicked)
                self.ui.variables_table.setCellWidget(row, self.Column.GRAPH, graph_widget)

                item = QtWidgets.QTableWidgetItem(variable.name)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.ui.variables_table.setItem(row, self.Column.NAME, item)

                item = QtWidgets.QTableWidgetItem(variable.type)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.ui.variables_table.setItem(row, self.Column.TYPE, item)

                self.ui.variables_table.setItem(row, self.Column.VALUE, NumberTableWidgetItem(""))

                if graph_state:
                    self.update_graph_variables(row, graph_state)

    @staticmethod
    def create_table_checkbox(a_cb_state) -> Tuple[QtWidgets.QWidget, QtWidgets.QCheckBox]:
        widget = QtWidgets.QWidget()
        cb = QtWidgets.QCheckBox()
        cb.setChecked(a_cb_state)

        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget, cb

    @staticmethod
    def get_table_checkbox_state(a_table_widget: QtWidgets.QWidget) -> int:
        return int(a_table_widget.layout().itemAt(0).widget().isChecked())

    def graph_checkbox_clicked(self, a_state):
        try:
            checkbox = self.sender()
            pos = checkbox.mapTo(self.ui.variables_table.viewport(), checkbox.pos())
            cell_index = self.ui.variables_table.indexAt(pos)

            self.update_graph_variables(cell_index.row(), a_state)
        except Exception as err:
            logging.debug(utils.exception_handler(err))

    def update_graph_variables(self, a_table_row, a_graph_state):
        variable_info = self.get_variable_info_by_row(a_table_row)

        if a_graph_state:
            variable = nv.BufferedVariable(variable_info, self.calibrator, nv.BufferedVariable.Mode.R)

            self.variables_to_graph[variable_info.name] = variable
            self.graphs_data[variable_info.name] = [], []

            if self.graphs_dialog is not None:
                self.graphs_dialog.add_graph(variable_info.name)
        else:
            if self.graphs_dialog is not None:
                self.graphs_dialog.remove_graph(variable_info.name)

            del self.variables_to_graph[variable_info.name]
            del self.graphs_data[variable_info.name]

    def get_variable_info_by_row(self, a_row):
        name = self.ui.variables_table.item(a_row, TstlanDialog.Column.NAME).text()
        _type = self.ui.variables_table.item(a_row, TstlanDialog.Column.TYPE).text()
        float_index = float(self.ui.variables_table.item(a_row, TstlanDialog.Column.INDEX).text())
        if _type == "bit":
            index = floor(float_index)
            bit_index = int(round((float_index - index) * 10, 2))
        else:
            index = int(float_index)
            bit_index = 0

        return nv.VariableInfo(a_index=index, a_bit_index=bit_index, a_type=_type, a_name=name)

    def show_graphs(self):
        try:
            if self.graphs_dialog is None:
                self.graphs_dialog = TstlanGraphDialog(self.graphs_data, self.settings, self)
                self.graphs_dialog.exec()
                self.graphs_dialog = None
        except Exception as err:
            logging.debug(utils.exception_handler(err))

    def update_graph_variables_data(self):
        timestamp = time.time()
        if not self.variables_to_graph:
            self.start_timestamp = timestamp

        for graph_name in self.variables_to_graph.keys():
            self.graphs_data[graph_name][0].append(timestamp - self.start_timestamp)
            self.graphs_data[graph_name][1].append(self.variables_to_graph[graph_name].get())

        if self.graphs_dialog is not None:
            self.graphs_dialog.update_graphs(self.graphs_data)

    def read_variables(self):
        self.ui.variables_table.blockSignals(True)

        try:
            if self.netvars.connected():
                for visual_row in range(self.ui.variables_table.rowCount()):
                    row = int(self.ui.variables_table.item(visual_row, self.Column.NUMBER).text())

                    value = self.netvars.read_variable(row)
                    self.ui.variables_table.item(visual_row, self.Column.VALUE).setText(
                        utils.float_to_string(round(value, 7)))

                self.update_graph_variables_data()
        except Exception as err:
            logging.debug(utils.exception_handler(err))

        self.ui.variables_table.blockSignals(False)

    def write_variable(self, a_item: QtWidgets.QTableWidgetItem):
        try:
            if self.netvars.connected():
                variable_number = int(self.ui.variables_table.item(a_item.row(), self.Column.NUMBER).text())
                try:
                    variable_value = utils.parse_input(a_item.text())
                    self.netvars.write_variable(variable_number, variable_value)
                except ValueError:
                    pass
        except Exception as err:
            logging.debug(utils.exception_handler(err))

    def filter_variables(self):
        filter_text = self.ui.name_filter_edit.text()
        regexp = QtCore.QRegExp(filter_text)
        regexp.setPatternSyntax(QtCore.QRegExp.Wildcard)
        regexp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        for i in range(self.ui.variables_table.rowCount()):
            cell_text = self.ui.variables_table.item(i, self.Column.NAME).text()
            if any(regex_symb in filter_text for regex_symb in ['?', '*', '[', ']']):
                match = regexp.exactMatch(cell_text)
            else:
                match = filter_text in cell_text

            if self.ui.show_marked_checkbox.isChecked():
                marked_cb = self.ui.variables_table.cellWidget(i, self.Column.MARK).layout().itemAt(0).widget()
                match = match & marked_cb.isChecked()
            self.ui.variables_table.setRowHidden(i, not match)

    def show_marked_toggled(self, a_enable):
        self.filter_variables()
        self.settings.tstlan_show_marks = int(a_enable)

    def update_time_changed(self, a_value):
        self.read_variables_timer.start(a_value * 1000)
        self.settings.tstlan_update_time = a_value

    def closeEvent(self, a_event: QtGui.QCloseEvent) -> None:
        self.settings.save_qwidget_state(self.ui.variables_table)
        self.settings.save_qwidget_state(self)

        mark_states = [0] * self.ui.variables_table.rowCount()
        graph_states = [0] * self.ui.variables_table.rowCount()
        for i in range(self.ui.variables_table.rowCount()):
            cb_number = int(self.ui.variables_table.item(i, self.Column.NUMBER).text())

            mark_state = self.get_table_checkbox_state(self.ui.variables_table.cellWidget(i, self.Column.MARK))
            graph_state = self.get_table_checkbox_state(self.ui.variables_table.cellWidget(i, self.Column.GRAPH))

            mark_states[cb_number] = mark_state
            graph_states[cb_number] = graph_state

        self.settings.tstlan_marks = mark_states
        self.settings.tstlan_graphs = graph_states

        a_event.accept()


class NumberTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __lt__(self, other: QtWidgets.QTableWidgetItem):
        try:
            return float(self.text().replace(',', '.')) < float(other.text().replace(',', '.'))
        except ValueError:
            return False
