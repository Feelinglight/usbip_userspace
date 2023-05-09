from usbip_gui.qt_utils.qt_settings_ini_parser import QtSettings


def get_ini_settings():
    return QtSettings("./settings.ini", [
        QtSettings.VariableInfo(a_name="some_int", a_section="PARAMETERS", a_type=QtSettings.ValueType.INT),
        QtSettings.VariableInfo(a_name="some_string", a_section="PARAMETERS", a_type=QtSettings.ValueType.STRING),
        QtSettings.VariableInfo(a_name="some_float", a_section="PARAMETERS", a_type=QtSettings.ValueType.FLOAT,
                                a_default=56.931246),
    ])
