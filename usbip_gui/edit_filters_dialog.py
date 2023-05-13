from typing import List, Tuple

from PyQt5 import QtWidgets

from common.usb import UsbFilterRule
from usbip_gui.ui.py.edit_filters_dialog import Ui_edit_filters_dialog as EditFiltersForm
from qt_utils.helpers import show_error


class EditFiltersDialog(QtWidgets.QDialog):

    def __init__(self, title: str, a_parent=None):
        super().__init__(a_parent)

        self.ui = EditFiltersForm()
        self.ui.setupUi(self)
        self.ui.filters_title_label.setText(f"Фильтры ({title})")
        self.show()

        self.__filters: List[UsbFilterRule] = []

        self.ui.swap_filter_button.setEnabled(False)

        self.ui.ok_button.clicked.connect(self.accept)
        self.ui.close_button.clicked.connect(self.reject)

    def get_filters(self):
        return self.__filters

    def __save_filters(self):
        self.__filters = []

    def ok_pressed(self):
        self.__save_filters()
        self.accept()

