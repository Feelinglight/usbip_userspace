from PyQt5 import QtWidgets

from usbip_gui.ui.py.edit_filters_dialog import Ui_edit_filters_dialog as EditFiltersForm


class EditFiltersDialog(QtWidgets.QDialog):

    def __init__(self, title: str, a_parent=None):
        super().__init__(a_parent)

        self.ui = EditFiltersForm()
        self.ui.setupUi(self)
        self.setWindowTitle(title)
        self.show()

        self.ui.swap_filter_button.setEnabled(False)

        self.ui.ok_button.clicked.connect(self.accept)
        self.ui.close_button.clicked.connect(self.reject)

