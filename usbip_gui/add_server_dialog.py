from PyQt5 import QtWidgets
from qt_utils.helpers import show_error

from usbip_gui.ui.py.add_server_dialog import Ui_about_dialog as AddServerForm


class AddServerDialog(QtWidgets.QDialog):

    def __init__(self, a_parent=None):
        super().__init__(a_parent)

        self.ui = AddServerForm()
        self.ui.setupUi(self)
        self.show()

        self.__server_name = ""
        self.__server_address = ""

        self.ui.ok_button.clicked.connect(self.ok_pressed)
        self.ui.close_button.clicked.connect(self.reject)

    def server_name(self):
        return self.__server_name

    def server_address(self):
        return self.__server_address

    def ok_pressed(self):
        self.__server_name = self.ui.server_name_edit.text().strip()
        self.__server_address = self.ui.server_address_edit.text().strip()
        if self.__server_name and self.__server_address:
            self.accept()
        else:
            show_error(self, 'Поля "Имя сервера" и "Адрес" должны быть заполнены')
