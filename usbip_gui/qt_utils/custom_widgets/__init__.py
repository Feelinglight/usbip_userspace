

if __name__ == "__main__":
    from irspy.qt import ui_to_py
    ui_to_py.convert_resources('../resources', '../resources', )
    ui_to_py.convert_ui('./ui_forms', './ui_py', 'irspy.qt.resources')
