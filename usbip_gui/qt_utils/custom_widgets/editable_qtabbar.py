from PyQt5 import QtGui, QtWidgets, QtCore


class EditableQTabBar(QtCore.QObject):
    tab_changed = QtCore.pyqtSignal(int)

    tab_added = QtCore.pyqtSignal(int)
    tab_deleted = QtCore.pyqtSignal(int)

    def __init__(self, a_parent: QtWidgets.QWidget = None):
        super().__init__(a_parent)

        self.tab_bar = QtWidgets.QTabBar(a_parent)

        # Этот styleSheet проверен на PyQt5 v5.14.1. На v5.15.2 работает неверно
        self.tab_bar.setStyleSheet(
            "QTabWidget::tab-bar { border: 0px }\n"
            "QTabBar::tab { height: 25px; }\n"
            "QTabBar::tab::last { width: 15px; padding-left: 12px; margin-left: 1px; border: 0px }"
        )
        self.tab_bar.setExpanding(False)

        plus_button = QtWidgets.QPushButton()
        plus_button.setIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/icons/plus.png")))
        plus_button.setFlat(True)
        plus_button.setFixedSize(20, 20)
        plus_button.clicked.connect(self.add_tab_button_clicked)

        self.tab_bar.addTab("")
        self.tab_bar.setTabEnabled(self.tab_bar.count() - 1, False)
        self.tab_bar.setTabButton(self.tab_bar.count() - 1, QtWidgets.QTabBar.RightSide, plus_button)

        self.tab_bar.currentChanged.connect(self.tab_changed.emit)

    def widget(self) -> QtWidgets.QTabBar:
        return self.tab_bar

    def add_tab_with_name(self, a_name):
        close_button = TabCloseButton(self.tab_bar)
        close_button.close_clicked.connect(self.delete_tab)

        new_tab_index = self.tab_bar.count() - 1
        self.tab_bar.insertTab(new_tab_index, a_name)
        self.tab_bar.setTabButton(new_tab_index, QtWidgets.QTabBar.RightSide, close_button)

        self.tab_added.emit(new_tab_index)

        self.tab_bar.setCurrentIndex(new_tab_index)

    def add_tab_button_clicked(self):
        tab_name, ok = QtWidgets.QInputDialog.getText(self.tab_bar, "Ввод имени вкладки", "Имя вкладки",
                                                      QtWidgets.QLineEdit.Normal)
        if ok and tab_name:
            self.add_tab_with_name(tab_name)

    def delete_tab(self):
        sender = self.sender()

        tab_name = self.tab_bar.tabText(self.tab_bar.currentIndex())
        res = QtWidgets.QMessageBox.question(self.tab_bar, f'Подтвердите действие',
                                             f'Вы действительно хотите удалить "{tab_name}"?',
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                             QtWidgets.QMessageBox.No)
        if res == QtWidgets.QMessageBox.Yes:
            tab_idx = self.get_tab_idx(sender)

            if tab_idx == self.tab_bar.count() - 2 and tab_idx == self.tab_bar.currentIndex():
                # Если удаляется последняя вкладка и она активна, меняем активную на предыдущую (иначе выберется "+")
                self.tab_bar.setCurrentIndex(max(0, self.tab_bar.count() - 3))

            self.tab_deleted.emit(tab_idx)
            self.tab_bar.removeTab(tab_idx)

            # if self.tab_bar.currentIndex() == tab_idx:
                # В этих случаях self.tab_bar.currentChanged не эмитится
                # self.tab_bar.currentChanged.emit(tab_idx)

    def get_tab_idx(self, a_widget):
        for tab_idx in range(self.tab_bar.count() - 1):
            if a_widget is self.tab_bar.tabButton(tab_idx, QtWidgets.QTabBar.RightSide):
                return tab_idx
        assert True, "Cant find tab idx by widget!!!"


class TabCloseButton(QtWidgets.QWidget):
    close_clicked = QtCore.pyqtSignal()

    def __init__(self, a_parent=None):
        super().__init__(a_parent)

        self.close_button = QtWidgets.QPushButton(self)
        self.close_button.setIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/icons/close.png")))
        self.close_button.setIconSize(QtCore.QSize(15, 15))
        self.close_button.setFlat(True)
        self.close_button.setFixedSize(15, 15)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.close_button)
        self.layout.setContentsMargins(5, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)

        self.close_button.clicked.connect(self.close_clicked.emit)
