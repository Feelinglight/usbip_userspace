from logging.handlers import RotatingFileHandler
from typing import List, Optional
import logging

from PyQt5 import QtWidgets, QtGui, QtCore

from usbip_gui.qt_utils.helpers import exception_decorator
from usbip_gui.qt_utils.settings_ini_parser import BadIniException
from usbip_gui.qt_utils.helpers import QTextEditLogger, show_error
from usbip_gui.about_dialog import AboutDialog
from usbip_gui.edit_filters_dialog import EditFiltersDialog
from usbip_gui.add_server_dialog import AddServerDialog

from usbip_gui.ui.py.mainwindow import Ui_MainWindow as MainForm
from usbip_gui import app_info
from usbip_gui import settings
import common.usb
from servers_manager import ServersManager, UsbipServer


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = MainForm()
        self.ui.setupUi(self)
        self.setWindowTitle(app_info.NAME)

        try:
            self.settings = settings.get_ini_settings()
        except BadIniException:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Файл настроек поврежден, "
                                                           "удалите settings.ini и перезапустите программу")
            self.close()
        else:
            self.settings.restore_qwidget_state(self)
            self.settings.restore_qwidget_state(self.ui.splitter)

            self.set_up_logger()

            self.servers_manager = ServersManager()
            self.usbip_servers: List[UsbipServer] = []

            self.ui.add_server_action.triggered.connect(self.open_add_server_dialog)
            self.ui.remove_server_action.triggered.connect(self.remove_selected_server)
            self.ui.filters_action.triggered.connect(self.open_common_filters)
            self.ui.about_action.triggered.connect(self.open_about)

            self.tick_timer = QtCore.QTimer(self)
            self.tick_timer.timeout.connect(self.tick)
            self.tick_timer.start(100)

            self.show()

    def set_up_logger(self):
        log = QTextEditLogger(self.ui.log_text_edit)
        log.setFormatter(logging.Formatter('%(asctime)s - %(module)s - %(message)s', datefmt='%H:%M:%S'))

        file_log = RotatingFileHandler(
            f"{app_info.NAME}.log", maxBytes=30*1024*1024, backupCount=3, encoding='utf8')
        file_log.setLevel(logging.DEBUG)
        file_log.setFormatter(
            logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))

        logging.getLogger().addHandler(file_log)
        logging.getLogger().addHandler(log)
        logging.getLogger().setLevel(logging.DEBUG)

    def tick(self):
        usbip_servers = self.servers_manager.get_servers_list()
        if self.usbip_servers != usbip_servers:
            self.usbip_servers = usbip_servers

            logging.debug("Данные о серверах изменились:")
            for server in self.usbip_servers:
                logging.debug(f"{server}")

    def open_add_server_dialog(self):
        add_server_dialog = AddServerDialog()
        if add_server_dialog.exec() == QtWidgets.QDialog.Accepted:
            res, err_msg = self.servers_manager.add_server(UsbipServer(
                name=add_server_dialog.server_name(),
                address=add_server_dialog.server_address(),
                available=False,
                devices=[],
                filters=[]
            ))
            if not res:
                show_error(self, f"Не удалось добавить сервер.\n{err_msg}.")

    def open_common_filters(self):
        self.open_filters(None)

    def open_server_filters(self):
        server_name = ""
        self.open_filters(server_name)

    def open_filters(self, server_name: Optional[str]):
        if server_name is None:
            dialog_title = "общие"
        else:
            dialog_title = f"{server_name}"

        edit_filters_dialog = EditFiltersDialog(dialog_title)
        if edit_filters_dialog.exec() == QtWidgets.QDialog.Accepted:
            filters = edit_filters_dialog.get_filters()
            res, err_msg = self.servers_manager.set_server_filters(server_name, filters)
            if not res:
                show_error(self, f"Не удалось установить фильтры.\n{err_msg}.")

    def remove_selected_server(self):
        server_name = ""
        res, err_msg = self.servers_manager.remove_server(server_name)
        if not res:
            show_error(self, f"Не удалось удалить сервер {server_name}.\n{err_msg}.")

    def get_selected_device(self):
        return "", ""

    def attach_device(self):
        server_name, selected_device = self.get_selected_device()
        res, err_msg = self.servers_manager.attach_device(server_name, selected_device)
        if not res:
            show_error(self, f"Не удалось импортировать устройство {selected_device} с сервера "
                             f"{server_name}.\n{err_msg}.")

    def detach_device(self):
        server_name, selected_device = self.get_selected_device()
        res, err_msg = self.servers_manager.detach_device(server_name, selected_device)
        if not res:
            show_error(self, f"Не удалось отменить импорт устройства {selected_device} с сервера "
                             f"{server_name}.\n{err_msg}.")

    def open_about(self):
        AboutDialog().exec()

    def closeEvent(self, a_event: QtGui.QCloseEvent):
        self.settings.save_qwidget_state(self.ui.splitter)
        self.settings.save_qwidget_state(self)
        a_event.accept()
