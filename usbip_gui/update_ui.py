from qt_utils import ui_to_py

if __name__ == "__main__":
    ui_to_py.convert_resources("./qt_utils/resources", ".")
    ui_to_py.convert_ui("./ui", "./ui/py")
