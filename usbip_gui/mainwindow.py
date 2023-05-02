from logging.handlers import RotatingFileHandler
import logging

from PyQt5 import QtWidgets, QtGui

from qt_utils.helpers import exception_decorator
from qt_utils.settings_ini_parser import BadIniException
from qt_utils.helpers import QTextEditLogger
from about_dialog import AboutDialog

from ui.py.mainwindow import Ui_MainWindow as MainForm
import app_info
import settings


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
            self.settings.restore_qwidget_state(self.ui.mw_splitter_1)

            self.set_up_logger()

            self.ui.some_spinbox.setValue(self.settings.some_int)

            self.ui.logging_info_button.clicked.connect(self.logging_info_button_clicked)
            self.ui.logging_warning_button.clicked.connect(self.logging_warning_button_clicked)
            self.ui.exception_in_slot_button.clicked.connect(self.exception_in_slot_button_clicked)
            self.ui.some_spinbox.editingFinished.connect(self.some_spinbox_value_changed)
            self.ui.about_action.triggered.connect(self.open_about)

            self.show()

    def set_up_logger(self):
        log = QTextEditLogger(self.ui.log_text_edit)
        log.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))

        file_log = RotatingFileHandler("telegram_scanner.log", maxBytes=30*1024*1024, backupCount=3, encoding='utf8')
        file_log.setLevel(logging.DEBUG)
        file_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))

        logging.getLogger().addHandler(file_log)
        logging.getLogger().addHandler(log)
        logging.getLogger().setLevel(logging.INFO)

    def logging_info_button_clicked(self):
        logging.info("Пример вывода в лог (Уровень INFO)")

    def logging_warning_button_clicked(self):
        logging.warning("Пример вывода в лог (Уровень WARNING)")

    @exception_decorator
    def exception_in_slot_button_clicked(self, _):
        very_important_value = 42 / 0

    def some_spinbox_value_changed(self):
        self.settings.some_int = self.ui.some_spinbox.value()

    def open_about(self):
        AboutDialog().exec()

    def closeEvent(self, a_event: QtGui.QCloseEvent):
        self.settings.save_qwidget_state(self.ui.mw_splitter_1)
        self.settings.save_qwidget_state(self)
        a_event.accept()
