from qt_utils import ui_to_py
ui_to_py.convert_resources("./qt_utils/resources", ".")
ui_to_py.convert_ui("./ui", "./ui/py")


def main():
    # Импорты здесь, чтобы ловить исключения в собранной версии программы, если они возникнут при импорте
    import sys

    from PyQt5.QtWidgets import QApplication

    from mainwindow import MainWindow

    app = QApplication(sys.argv)

    w = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        import traceback
        main()
    except Exception as err:
        print(traceback.format_exc())
