
def main():
    # Импорты здесь, чтобы ловить исключения в собранной версии программы,
    # если они возникнут при импорте
    import sys
    from PyQt5.QtWidgets import QApplication
    from usbip_gui.mainwindow import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        import traceback
        main()
    except Exception as err:
        print(traceback.format_exc())
