from logging.handlers import RotatingFileHandler
from typing import List, Optional
import logging

from PyQt5 import QtWidgets, QtGui, QtCore

from usbip_gui.qt_utils.settings_ini_parser import BadIniException
from usbip_gui.qt_utils.helpers import QTextEditLogger, show_error
from usbip_gui.about_dialog import AboutDialog
from usbip_gui.edit_filters_dialog import EditFiltersDialog
from usbip_gui.add_server_dialog import AddServerDialog

from usbip_gui.ui.py.mainwindow import Ui_MainWindow as MainForm
from usbip_gui import app_info
from usbip_gui import settings
import common.usb as usb
from servers_manager import ServersManager, UsbipServer


class MainWindow(QtWidgets.QMainWindow):

    CLASS_TO_ICON = {
        usb.UsbClass.AUDIO: ":/icons/icons/audio_gray.png",
        usb.UsbClass.HID: ":/icons/icons/hid_gray.png",
        usb.UsbClass.VIDEO: ":/icons/icons/camera_gray.png",
        usb.UsbClass.AUDIO_VIDEO: ":/icons/icons/camera_gray.png",
        usb.UsbClass.WIRELESS: ":/icons/icons/bluetooth_gray.png",
        usb.UsbClass.MSC: ":/icons/icons/flashdrive_gray.png",
    }

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

            self.ui.usb_tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.ui.usb_tree_widget.customContextMenuRequested.connect(self.show_context_menu)

            self.ui.add_server_action.triggered.connect(self.open_add_server_dialog)
            self.ui.remove_server_action.triggered.connect(self.remove_selected_server)
            self.ui.filters_action.triggered.connect(self.open_common_filters)
            self.ui.about_action.triggered.connect(self.open_about)

            self.tick_timer = QtCore.QTimer(self)
            self.tick_timer.timeout.connect(self.tick)
            self.tick_timer.start(100)

            self.show()
            self.open_filters(None)

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

    def show_context_menu(self, pos):
        item = self.ui.usb_tree_widget.itemAt(pos)

        menu = QtWidgets.QMenu(self)
        # TODO: Сделать в зависимости от сервер/устройство подключено/устройство отключено
        menu.addAction(QtWidgets.QAction('Отключить устройство', menu))

        menu.popup(QtGui.QCursor.pos())

    def usb_icon(self, usb_dev: usb.UsbipDevice, attached):
        try:
            icon = self.CLASS_TO_ICON[usb_dev.classes[0]]
        except (KeyError, IndexError):
            icon = ":/icons/icons/usb.png"

        base = QtGui.QPixmap(icon).scaled(100, 100)
        attached_icon = ":/icons/icons/ok.png" if attached else ":/icons/icons/close.png"
        overlay = QtGui.QPixmap(attached_icon).scaled(80, 80)
        result = QtGui.QPixmap(base.width(), base.height())
        result.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(result)
        painter.drawPixmap(0, 0, base)
        painter.drawPixmap(30, 30, overlay)
        painter.end()

        return QtGui.QIcon(result)

    def make_server_text(self, server: UsbipServer):
        return f'<html><head/><body>' \
               f'<span style=" font-size:11pt;"><b>{server.name}</b></span> ' \
               f'<span style=" font-size:9pt;">({server.address})</span>' \
               f'</body></html>'

    def make_device_text(self, device: usb.UsbipDevice):
        return f'<html><head/><body>' \
               f'<span style=" font-size:11pt;">{device.name}</span><br>' \
               f'<span style=" font-size:9pt;">ID: {device.busid}</span>' \
               f'<span style=" font-size:9pt;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;VID: {device.vid}</span>' \
               f'<span style=" font-size:9pt;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PID: {device.pid}</span>' \
               f'</body></html>'

    def update_table(self):
        expanded = {}
        for i in range(self.ui.usb_tree_widget.topLevelItemCount()):
            item = self.ui.usb_tree_widget.topLevelItem(i)
            expanded[item.text(0)] = item.isExpanded()

        self.ui.usb_tree_widget.clear()

        for server in self.usbip_servers:
            server_tree_widget = QtWidgets.QTreeWidgetItem()
            self.ui.usb_tree_widget.addTopLevelItem(server_tree_widget)

            server_text = QtWidgets.QLabel(self.make_server_text(server))
            server_icon = ":/icons/icons/server_online.png" if server.available else \
                ":/icons/icons/server_offline.png"
            server_tree_widget.setIcon(0, QtGui.QIcon(server_icon))
            self.ui.usb_tree_widget.setItemWidget(server_tree_widget, 0, server_text)

            for dev, attached in server.devices:
                dev_tree_widget = QtWidgets.QTreeWidgetItem()
                server_tree_widget.addChild(dev_tree_widget)

                text_widget = QtWidgets.QLabel(self.make_device_text(dev))
                dev_tree_widget.setIcon(0, self.usb_icon(dev, attached))

                self.ui.usb_tree_widget.setItemWidget(dev_tree_widget, 0, text_widget)

            try:
                server_tree_widget.setExpanded(expanded[server.name])
            except KeyError:
                server_tree_widget.setExpanded(True)

    def tick(self):
        usbip_servers = self.servers_manager.get_servers_list()
        if self.usbip_servers != usbip_servers:
            self.usbip_servers = usbip_servers

            logging.debug("Данные о серверах изменились:")
            for server in self.usbip_servers:
                logging.debug(f"{server}")

            self.update_table()

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

        edit_filters_dialog = EditFiltersDialog(
            dialog_title, self.servers_manager.get_server_filters(server_name))
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
