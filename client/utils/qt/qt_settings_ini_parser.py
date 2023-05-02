from PyQt5 import QtCore, QtWidgets

from irspy.settings_ini_parser import Settings
from irspy import utils


class QtSettings(Settings):
    """
    Добавляет к Settings методы для сохранения состояния и размера некоторых виджетов qt
    """
    GEOMETRY_SECTION = "GEOMETRY"

    def save_bytes(self, a_name: str, a_bytes: bytes):
        self.add_ini_section(QtSettings.GEOMETRY_SECTION)
        self.settings[QtSettings.GEOMETRY_SECTION][a_name] = utils.bytes_to_base64(a_bytes)
        self.save()

    def read_bytes(self, a_name: str) -> QtCore.QByteArray:
        try:
            geometry_string = self.settings[QtSettings.GEOMETRY_SECTION][a_name]
            return QtCore.QByteArray(utils.base64_to_bytes(geometry_string))
        except (KeyError, ValueError):
            return QtCore.QByteArray()

    def save_qwidget_state(self, a_widget: QtWidgets.QWidget):
        widget_name = a_widget.objectName()
        assert bool(widget_name), "Виджет должен иметь objectName! (Уникальный)"

        if isinstance(a_widget, QtWidgets.QMainWindow) or isinstance(a_widget, QtWidgets.QDialog):
            widget_state = a_widget.saveGeometry()
        elif isinstance(a_widget, QtWidgets.QTableWidget) or isinstance(a_widget, QtWidgets.QTableView):
            widget_state = a_widget.horizontalHeader().saveState()
        elif isinstance(a_widget, QtWidgets.QTreeWidget):
            widget_state = a_widget.header().saveState()
        elif hasattr(a_widget, "restoreGeometry") and not isinstance(a_widget, QtWidgets.QSplitter):
            widget_state = a_widget.saveGeometry()
        elif hasattr(a_widget, "saveState"):
            widget_state = a_widget.saveState()
        else:
            assert True, 'No way to save widget state'

        self.save_bytes(widget_name, bytes(widget_state))

    def restore_qwidget_state(self, a_widget: QtWidgets.QWidget):
        widget_name = a_widget.objectName()
        geometry_bytes = self.read_bytes(widget_name)

        if isinstance(a_widget, QtWidgets.QMainWindow) or isinstance(a_widget, QtWidgets.QDialog):
            a_widget.restoreGeometry(geometry_bytes)
        elif isinstance(a_widget, QtWidgets.QTableWidget) or isinstance(a_widget, QtWidgets.QTableView):
            a_widget.horizontalHeader().restoreState(geometry_bytes)
        elif isinstance(a_widget, QtWidgets.QTreeWidget):
            a_widget.header().restoreState(geometry_bytes)
        elif hasattr(a_widget, "restoreGeometry") and not isinstance(a_widget, QtWidgets.QSplitter):
            a_widget.restoreGeometry(geometry_bytes)
        elif hasattr(a_widget, "restoreState"):
            a_widget.restoreState(geometry_bytes)
        else:
            assert True, 'No way to restore widget state'

    def save_dialog_size(self, a_widget: QtWidgets.QWidget):
        """
        В отличии от save_qwidget_state сохраняет не все состояние диалога, а только его размеры
        """
        widget_name = a_widget.objectName()
        assert bool(widget_name), "Виджет должен иметь objectName! (Уникальный)"

        size = "{};{}".format(a_widget.size().width(), a_widget.size().height())
        widget_state = bytes(size, encoding='cp1251')

        self.save_bytes(widget_name, widget_state)

    def restore_dialog_size(self, a_widget):
        widget_name = a_widget.objectName()
        geometry_bytes = self.read_bytes(widget_name)

        try:
            size = geometry_bytes.split(";")
            a_widget.resize(int(size[0]), int(size[1]))
        except ValueError:
            pass


if __name__ == "__main__":
    # Пример использования
    import sys
    from PyQt5 import QtWidgets

    a = QtSettings("./test_settings.ini", [
        Settings.VariableInfo(a_name="list_float", a_section="PARAMETERS", a_type=Settings.ValueType.LIST_FLOAT),
        Settings.VariableInfo(a_name="list_int", a_section="PARAMETERS", a_type=Settings.ValueType.LIST_INT),
        Settings.VariableInfo(a_name="float1", a_section="PARAMETERS", a_type=Settings.ValueType.FLOAT, a_default=123.),
        Settings.VariableInfo(a_name="int1", a_section="PARAMETERS", a_type=Settings.ValueType.INT, a_default=222),
        Settings.VariableInfo(a_name="str1", a_section="PARAMETERS", a_type=Settings.ValueType.STRING, a_default="haha")
    ])

    print(a.list_float, a.list_int, a.float1, a.int1, a.str1)

    a.list_float = [31., 33., 333.]
    a.list_int = [11, 2, 3]
    a.float1 = 11.
    a.int1 = 331
    a.str1 = "he1he"

    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QDialog()
    w.setObjectName("test")
    a.restore_dialog_size(w)
    w.show()
    app.exec()

    a.save_dialog_size(w)

    print(a.list_float, a.list_int, a.float1, a.int1, a.str1)
