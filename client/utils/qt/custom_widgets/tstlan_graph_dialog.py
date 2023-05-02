from typing import List, Dict, Tuple
import logging

from PyQt5 import QtGui, QtWidgets
import pyqtgraph

from irspy.qt.custom_widgets.ui_py.tstslan_graphs_dialog import Ui_tstlan_graphs_dialog as GraphForm
from irspy.qt.qt_settings_ini_parser import QtSettings
import irspy.utils as utils


class TstlanGraphDialog(QtWidgets.QDialog):
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

    def __init__(self, a_graph_data: Dict[str, Tuple[List[float], List[float]]], a_settings: QtSettings,
                 a_parent=None):
        super().__init__(a_parent)

        self.ui = GraphForm()
        self.ui.setupUi(self)

        self.settings = a_settings
        self.settings.restore_qwidget_state(self)
        self.show()

        self.graph_widget = pyqtgraph.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setLabel('bottom', 'Время, с', color='black', size=20)
        self.graph_widget.showGrid(x=True, y=True)
        self.graph_widget.addLegend()

        self.ui.chart_layout.addWidget(self.graph_widget)

        self.graph_items: Dict[str, pyqtgraph.PlotCurveItem] = {}
        for graph_name in a_graph_data.keys():
            self.add_graph(graph_name)

    def update_graphs(self, a_graph_data: Dict[str, List[Tuple[float, float]]]):
        try:
            for graph_name in a_graph_data.keys():
                pg_item = self.graph_items[graph_name]
                pg_item.setData(x=a_graph_data[graph_name][0], y=a_graph_data[graph_name][1], name=graph_name)
        except Exception as err:
            logging.debug(utils.exception_handler(err))

    def add_graph(self, a_graph_name):
        graph_number = len(self.graph_widget.listDataItems())
        graph_color = TstlanGraphDialog.GRAPH_COLORS[graph_number % len(TstlanGraphDialog.GRAPH_COLORS)]

        pg_item = pyqtgraph.PlotCurveItem(pen=pyqtgraph.mkPen(color=graph_color, width=2),
                                          name=a_graph_name)
        self.graph_items[a_graph_name] = pg_item
        self.graph_widget.addItem(pg_item)

    def remove_graph(self, a_graph_name):
        self.graph_widget.removeItem(self.graph_items[a_graph_name])
        del self.graph_items[a_graph_name]

    def __del__(self):
        print("tstlan graphs deleted")

    def closeEvent(self, a_event: QtGui.QCloseEvent) -> None:
        self.settings.save_qwidget_state(self)
        a_event.accept()
