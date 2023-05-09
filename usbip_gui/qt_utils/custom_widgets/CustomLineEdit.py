from PyQt5 import QtWidgets, QtGui, QtCore

import irspy.utils as utils


class QEditDoubleClick(QtWidgets.QLineEdit):
    """
    QLineEdit с добавлением выделения вещественных чисел по дабл клику
    """
    def __init__(self, a_parent=None):
        super().__init__(a_parent)
        self.select_span = None

        self.editingFinished.connect(self.clearFocus)

    def mouseDoubleClickEvent(self, a_event: QtGui.QMouseEvent):
        super().mouseDoubleClickEvent(a_event)
        result = utils.find_number_re.finditer(self.text())
        if result:
            for num_match in result:
                begin, end = num_match.span()
                if begin <= self.cursorPosition() <= end:
                    self.setSelection(begin, end - begin)
                    break
        a_event.accept()

    def keyPressEvent(self, a_event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(a_event)
        if a_event.key() == QtCore.Qt.Key_Enter or a_event.key() == QtCore.Qt.Key_Return:
            self.editingFinished.emit()
            a_event.accept()


class QEditCopyButton(QEditDoubleClick):
    """
    QEditDoubleClick с добавлением кнопки "Копировать" справа в эдите
    """
    def __init__(self, a_parent=None):
        super().__init__(a_parent)

        self.copy_button = QtWidgets.QPushButton(self)
        pixmap = QtGui.QPixmap(":/icons/icons/copy.png")
        self.copy_button.setIcon(QtGui.QIcon(pixmap))
        self.copy_button.setIconSize(pixmap.size())
        self.copy_button.setCursor(QtCore.Qt.ArrowCursor)
        self.copy_button.setStyleSheet("QPushButton { border: none; padding: 0px; }")
        self.copy_button.setFlat(True)
        self.copy_button.clicked.connect(self.copy)

        frame_width = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.style_padding = "padding-right:{0}px;".format(self.copy_button.sizeHint().width() + frame_width + 1)
        self.setStyleSheet("QLineEdit{{{0}}}".format(self.style_padding))
        msh = self.minimumSizeHint()
        self.setMinimumSize(max(msh.width(), self.copy_button.sizeHint().height() + frame_width * 2 + 2),
                            max(msh.height(), self.copy_button.sizeHint().height() + frame_width * 2 + 2))

    def resizeEvent(self, a_event: QtGui.QResizeEvent):
        size_hint = self.copy_button.sizeHint()
        frame_width = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.copy_button.move(self.rect().right() - frame_width - size_hint.width(),
                              (self.rect().bottom() + 1 - size_hint.height()) / 2)

    def setStyleSheet(self, a_style_sheet: str):
        a_style_sheet += self.style_padding
        super().setStyleSheet(a_style_sheet)

    def copy(self):
        QtWidgets.QApplication.clipboard().setText(self.text())
