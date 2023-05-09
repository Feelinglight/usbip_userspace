from PyQt5 import QtWidgets

from usbip_gui.ui.py.add_server_dialog import Ui_about_dialog as AddServerForm


class AddServerDialog(QtWidgets.QDialog):

    def __init__(self, a_parent=None):
        super().__init__(a_parent)

        self.ui = AddServerForm()
        self.ui.setupUi(self)
        self.show()

        self.ui.ok_button.clicked.connect(self.accept)
        self.ui.close_button.clicked.connect(self.reject)

