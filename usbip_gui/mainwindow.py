from logging.handlers import RotatingFileHandler
import logging

from PyQt5 import QtWidgets, QtGui

from usbip_gui.qt_utils.helpers import exception_decorator
from usbip_gui.qt_utils.settings_ini_parser import BadIniException
from usbip_gui.qt_utils.helpers import QTextEditLogger
from usbip_gui.about_dialog import AboutDialog
from usbip_gui.edit_filters_dialog import EditFiltersDialog
from usbip_gui.add_server_dialog import AddServerDialog

from usbip_gui.ui.py.mainwindow import Ui_MainWindow as MainForm
from usbip_gui import app_info
from usbip_gui import settings


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

            self.ui.add_server_action.triggered.connect(self.open_add_server_dialog)
            self.ui.remove_server_action.triggered.connect(self.remove_selected_server)
            self.ui.filters_action.triggered.connect(self.open_common_filters)
            self.ui.about_action.triggered.connect(self.open_about)

            self.show()

    def set_up_logger(self):
        log = QTextEditLogger(self.ui.log_text_edit)
        log.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))

        file_log = RotatingFileHandler(
            f"{app_info.NAME}.log", maxBytes=30*1024*1024, backupCount=3, encoding='utf8')
        file_log.setLevel(logging.DEBUG)
        file_log.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))

        logging.getLogger().addHandler(file_log)
        logging.getLogger().addHandler(log)
        logging.getLogger().setLevel(logging.INFO)

    def open_add_server_dialog(self):
        AddServerDialog().exec()

    def remove_selected_server(self):
        pass

    def open_common_filters(self):
        EditFiltersDialog("Общие фильтры").exec()

    def open_about(self):
        AboutDialog().exec()

    def closeEvent(self, a_event: QtGui.QCloseEvent):
        self.settings.save_qwidget_state(self.ui.splitter)
        self.settings.save_qwidget_state(self)
        a_event.accept()
