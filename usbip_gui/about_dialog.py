from PyQt5 import QtWidgets

from usbip_gui.ui.py.about_dialog import Ui_about_dialog as AboutForm
from usbip_gui import app_info


class AboutDialog(QtWidgets.QDialog):

    def __init__(self, a_parent=None):
        super().__init__(a_parent)

        self.ui = AboutForm()
        self.ui.setupUi(self)
        self.show()

        self.ui.version_label.setText(f"Версия программы: {app_info.VERSION}")

        self.ui.close_button.clicked.connect(self.reject)

