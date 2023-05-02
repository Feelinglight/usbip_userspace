from typing import Dict, Tuple, Iterable
from collections import OrderedDict
from sys import float_info
from enum import IntEnum
import logging
import bisect

from PyQt5 import QtGui, QtWidgets, QtCore
import pyqtgraph

from irspy.qt.custom_widgets.ui_py.graph_dialog import Ui_graph_dialog as GraphForm
from irspy.qt.qt_settings_ini_parser import QtSettings
from irspy import metrology
import irspy.utils as utils


class GraphParameters:
    def __init__(self):
        self.points_count = 0
        self.x_min = float_info.max
        self.x_max = float_info.min
        self.y_min = float_info.max
        self.y_max = float_info.min
        self.y_average = 0
        self.x_range = 0
        self.delta_2 = 0
        self.sko = 0
        self.sko_percents = 0
        self.student_95 = 0
        self.student_99 = 0
        self.student_999 = 0

    def reset(self):
        self.points_count = 0
        self.x_min = float_info.max
        self.x_max = float_info.min
        self.y_min = float_info.max
        self.y_max = float_info.min
        self.y_average = 0
        self.x_range = 0
        self.delta_2 = 0
        self.sko = 0
        self.sko_percents = 0
        self.student_95 = 0
        self.student_99 = 0
        self.student_999 = 0


class GraphDialog(QtWidgets.QDialog):
    GRAPH_COLORS = (
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 204, 204),
        (204, 0, 102),
        (204, 204, 0),
        (255, 0, 255),
        (102, 153, 153),
        (255, 153, 0),
        (102, 204, 255),
        (0, 255, 153),
        (204, 102, 255),
    )

    class ParametersColumn(IntEnum):
        PARAMETER = 0
        VALUE = 1

    class ParametersRow(IntEnum):
        POINTS_COUNT = 0
        X_MIN = 1
        X_MAX = 2
        Y_MIN = 3
        Y_MAX = 4
        Y_AVERAGE = 5
        X_RANGE = 6
        DELTA_2 = 7
        SKO = 8
        SKO_PERCENTS = 9
        STUDENT_95 = 10
        STUDENT_99 = 11
        STUDENT_999 = 12
        COUNT = 13

    PARAMETER_TO_STR = {
        ParametersRow.POINTS_COUNT: "Количество точек",
        ParametersRow.X_MIN: "Xmin",
        ParametersRow.X_MAX: "Xmax",
        ParametersRow.Y_MIN: "Ymin",
        ParametersRow.Y_MAX: "Ymax",
        ParametersRow.Y_AVERAGE: "Yaverage",
        ParametersRow.X_RANGE: "Xmax - Xmin",
        ParametersRow.DELTA_2: "|Ymax - Ymin|/|Yaverage|*100/2, %",
        ParametersRow.SKO: "СКО",
        ParametersRow.SKO_PERCENTS: "СКО / |Yaverage| * 100, %",
        ParametersRow.STUDENT_95: "Доверительный интервал 0,95, %",
        ParametersRow.STUDENT_99: "Доверительный интервал 0,99, %",
        ParametersRow.STUDENT_999: "Доверительный интервал 0,999, %",
    }

    def __init__(self, a_graph_data: Dict[str, Tuple[Iterable[float], Iterable[float]]], a_settings: QtSettings,
                 a_parent=None):
        super().__init__(a_parent)

        self.ui = GraphForm()
        self.ui.setupUi(self)

        self.open_icon = QtGui.QIcon(QtGui.QPixmap(":/icons/icons/right.png"))
        self.close_icon = QtGui.QIcon(QtGui.QPixmap(":/icons/icons/left.png"))

        self.settings = a_settings
        self.settings.restore_qwidget_state(self)
        self.settings.restore_qwidget_state(self.ui.graph_dialog_splitter)
        self.settings.restore_qwidget_state(self.ui.parameters_table)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowMinMaxButtonsHint)

        self.ui.parameters_widget.setHidden(True)
        splitter_sizes = self.ui.graph_dialog_splitter.sizes()
        self.ui.graph_dialog_splitter.setSizes([0, splitter_sizes[0] + splitter_sizes[1]])

        self.fill_parameters_table()
        self.ui.parameters_table.resizeRowsToContents()

        self.show()

        pyqtgraph.setConfigOption('leftButtonPan', False)
        self.graph_widget = pyqtgraph.PlotWidget()
        self.graph_widget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Preferred))
        self.graph_widget.setSizeIncrement(1, 1)
        self.graph_widget.setBackground('w')
        self.graph_widget.showGrid(x=True, y=True)
        self.graph_widget.addLegend()

        self.ui.chart_layout.addWidget(self.graph_widget)

        self.graph_items: Dict[str, pyqtgraph.PlotCurveItem] = OrderedDict()
        self.graphs_data = OrderedDict(((name, (list(data_x), list(data_y))) for name, (data_x, data_y) in a_graph_data.items()))

        for (data_x, data_y) in self.graphs_data.values():
            assert all(data_x[i] <= data_x[i + 1] for i in range(len(data_x) - 1)), \
                "Данные по оси икс должны быть неубывающими!"

        for graph_name in a_graph_data.keys():
            self.ui.graphs_combobox.addItem(graph_name)
            self.add_graph(graph_name)

        self.graph_parameters = GraphParameters()

        self.ui.graph_parameters_button.clicked.connect(self.show_graph_parameters)
        self.ui.update_pparameters_button.clicked.connect(self.update_graph_parameters_button_pressed)
        self.ui.graphs_combobox.currentTextChanged.connect(self.change_parameters_graph)
        self.ui.auto_update_checkbox.toggled.connect(self.auto_update_checkbox_toggled)
        self.graph_widget.sigRangeChanged.connect(self.update_graph_parameters)

    def fill_parameters_table(self):
        self.ui.parameters_table.setRowCount(GraphDialog.ParametersRow.COUNT)
        for row in range(GraphDialog.ParametersRow.COUNT):
            self.ui.parameters_table.setItem(row, GraphDialog.ParametersColumn.PARAMETER,
                                             QtWidgets.QTableWidgetItem(GraphDialog.PARAMETER_TO_STR[row]))

            self.ui.parameters_table.setItem(row, GraphDialog.ParametersColumn.VALUE, QtWidgets.QTableWidgetItem(""))

    def show_graph_parameters(self, _):
        hide_parameters = not self.ui.parameters_widget.isHidden()
        self.ui.parameters_widget.setHidden(hide_parameters)

        if hide_parameters:
            sizes = self.ui.graph_dialog_splitter.sizes()
            self.settings.graph_parameters_splitter_size = sizes[0]
            self.ui.graph_dialog_splitter.setSizes([0, sizes[0] + sizes[1]])

            self.ui.graph_parameters_button.setIcon(self.open_icon)
        else:
            sizes = self.ui.graph_dialog_splitter.sizes()
            size_left = self.settings.graph_parameters_splitter_size
            self.ui.graph_dialog_splitter.setSizes([size_left, sizes[1] - size_left])

            self.ui.graph_parameters_button.setIcon(self.close_icon)

    def add_graph(self, a_graph_name):
        graph_number = len(self.graph_widget.listDataItems())
        graph_color = GraphDialog.GRAPH_COLORS[graph_number % len(GraphDialog.GRAPH_COLORS)]

        pg_item = pyqtgraph.PlotCurveItem(pen=pyqtgraph.mkPen(color=graph_color, width=2), name=a_graph_name)
        pg_item.setData(x=self.graphs_data[a_graph_name][0], y=self.graphs_data[a_graph_name][1], name=a_graph_name)
        self.graph_widget.addItem(pg_item)

    def update_graph_parameters(self, _):
        if self.ui.auto_update_checkbox.isChecked():
            self.update_graph_parameters_button_pressed()

    def auto_update_checkbox_toggled(self, a_enable):
        if a_enable:
            self.update_graph_parameters(None)

    def change_parameters_graph(self, _):
        self.update_graph_parameters(None)

    def update_graph_parameters_button_pressed(self):
        x_min, x_max = self.graph_widget.getAxis('bottom').range
        y_min, y_max = self.graph_widget.getAxis('left').range

        current_graph_name = self.ui.graphs_combobox.currentText()
        data_x, data_y = self.graphs_data[current_graph_name]

        self.calculate_graph_parameters(data_x, data_y, x_min, x_max, y_min, y_max)
        self.update_graph_parameters_table()

    def calculate_graph_parameters(self, data_x, data_y, x_min, x_max, y_min, y_max):
        self.graph_parameters.reset()

        first_x_index = bisect.bisect_left(data_x, x_min)
        last_x_index = bisect.bisect_right(data_x, x_max)

        data_x_in_range = data_x[first_x_index:last_x_index]

        if data_x_in_range:
            self.graph_parameters.x_min = data_x_in_range[0]
            self.graph_parameters.x_max = data_x_in_range[-1]
            self.graph_parameters.x_range = self.graph_parameters.x_max - self.graph_parameters.x_min

            data_y_in_range = []
            moving_sko = metrology.MovingSKO()

            for y in data_y[first_x_index:last_x_index]:
                if y_min <= y <= y_max:
                    data_y_in_range.append(y)

                    if y > self.graph_parameters.y_max:
                        self.graph_parameters.y_max = y

                    if y < self.graph_parameters.y_min:
                        self.graph_parameters.y_min = y

                    moving_sko.add(y)

            if data_y_in_range:
                self.graph_parameters.points_count = len(data_y_in_range)
                self.graph_parameters.y_average = moving_sko.average()

                if self.graph_parameters.y_average:
                    abs_average = abs(self.graph_parameters.y_average)
                    self.graph_parameters.delta_2 = \
                        abs(self.graph_parameters.y_max - self.graph_parameters.y_min) / abs_average * 100 / 2

                    self.graph_parameters.sko = moving_sko.get()
                    self.graph_parameters.sko_percents = self.graph_parameters.sko / abs_average * 100

                    self.graph_parameters.student_95 = self.graph_parameters.sko_percents * \
                        metrology.student_t_inverse_distribution_2x(0.95, len(data_y_in_range))

                    self.graph_parameters.student_99 = self.graph_parameters.sko_percents * \
                        metrology.student_t_inverse_distribution_2x(0.99, len(data_y_in_range))

                    self.graph_parameters.student_999 = self.graph_parameters.sko_percents * \
                        metrology.student_t_inverse_distribution_2x(0.999, len(data_y_in_range))
            else:
                self.graph_parameters.y_min = 0
                self.graph_parameters.y_max = 0
        else:
            self.graph_parameters.x_min = 0
            self.graph_parameters.x_max = 0
            self.graph_parameters.y_min = 0
            self.graph_parameters.y_max = 0

    def set_number_to_table(self, a_row: int, a_column: int, a_value: float):
        self.ui.parameters_table.item(a_row, a_column).setText(utils.float_to_string(a_value, a_precision=15))

    def update_graph_parameters_table(self):
        column = GraphDialog.ParametersColumn.VALUE
        self.set_number_to_table(GraphDialog.ParametersRow.POINTS_COUNT, column, self.graph_parameters.points_count)

        self.set_number_to_table(GraphDialog.ParametersRow.X_MIN, column, self.graph_parameters.x_min)
        self.set_number_to_table(GraphDialog.ParametersRow.X_MAX, column, self.graph_parameters.x_max)
        self.set_number_to_table(GraphDialog.ParametersRow.Y_MIN, column, self.graph_parameters.y_min)
        self.set_number_to_table(GraphDialog.ParametersRow.Y_MAX, column, self.graph_parameters.y_max)
        self.set_number_to_table(GraphDialog.ParametersRow.Y_AVERAGE, column, self.graph_parameters.y_average)

        self.set_number_to_table(GraphDialog.ParametersRow.X_RANGE, column, self.graph_parameters.x_range)
        self.set_number_to_table(GraphDialog.ParametersRow.DELTA_2, column, self.graph_parameters.delta_2)
        self.set_number_to_table(GraphDialog.ParametersRow.SKO, column, self.graph_parameters.sko)
        self.set_number_to_table(GraphDialog.ParametersRow.SKO_PERCENTS, column, self.graph_parameters.sko_percents)

        self.set_number_to_table(GraphDialog.ParametersRow.STUDENT_95, column, self.graph_parameters.student_95)
        self.set_number_to_table(GraphDialog.ParametersRow.STUDENT_99, column, self.graph_parameters.student_99)
        self.set_number_to_table(GraphDialog.ParametersRow.STUDENT_999, column, self.graph_parameters.student_999)

    def __del__(self):
        print("graphs deleted")

    def closeEvent(self, a_event: QtGui.QCloseEvent) -> None:
        if not self.ui.parameters_widget.isHidden():
            # Здесь сохраняются размеры сплиттера
            self.show_graph_parameters(None)

        self.settings.save_qwidget_state(self.ui.parameters_table)
        self.settings.save_qwidget_state(self.ui.graph_dialog_splitter)
        self.settings.save_qwidget_state(self)

        a_event.accept()
