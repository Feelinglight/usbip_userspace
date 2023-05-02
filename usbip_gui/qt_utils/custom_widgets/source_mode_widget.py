from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QTimer


from irspy.qt.custom_widgets.ui_py.source_mode_widget import Ui_source_mode_widget as SourceModeForm
from irspy.qt.qt_settings_ini_parser import QtSettings
import irspy.clb.calibrator_constants as clb
import irspy.clb.clb_dll as clb_dll
from irspy import utils
from irspy.qt import qt_utils


class SourceModeWidget(QtWidgets.QWidget):
    close_confirmed = pyqtSignal()

    def __init__(self, a_settings: QtSettings, a_calibrator: clb_dll.ClbDrv, a_parent=None):
        super().__init__(a_parent)

        self.ui = SourceModeForm()
        self.ui.setupUi(self)

        self.pause_icon = QtGui.QIcon(QtGui.QPixmap(":/icons/icons/pause.png"))
        self.play_icon = QtGui.QIcon(QtGui.QPixmap(":/icons/icons/play.png"))
        self.ui.enable_button.setIconSize(QtCore.QSize(25, 25))

        self.settings = a_settings

        self.calibrator = a_calibrator
        self.clb_state = clb.State.DISCONNECTED
        self.signal_type = clb.SignalType.ACI
        self.mode = clb.Mode.SOURCE

        self.units = clb.signal_type_to_units[self.signal_type]
        self.value_to_user = utils.value_to_user_with_units(self.units)

        self.connect_signals()

        self.signal_type_to_radio = {
            clb.SignalType.ACI: self.ui.aci_radio,
            clb.SignalType.ACV: self.ui.acv_radio,
            clb.SignalType.DCI: self.ui.dci_radio,
            clb.SignalType.DCV: self.ui.dcv_radio,
        }
        self.mode_to_radio = {
            clb.Mode.SOURCE: self.ui.source_mode_radio,
            clb.Mode.FIXED_RANGE: self.ui.fixed_mode_radio,
            clb.Mode.DETUNING: self.ui.detuning_radio,
        }

        self.update_signal_enable_state(self.calibrator.signal_enable)

        self.clb_check_timer = QTimer()
        self.clb_check_timer.timeout.connect(self.sync_clb_parameters)
        self.clb_check_timer.start(100)

    def __del__(self):
        print("source mode deleted")

    def connect_signals(self):
        self.ui.clb_list_combobox.currentTextChanged.connect(self.connect_to_clb)

        self.ui.enable_button.clicked.connect(self.enable_signal)

        self.ui.aci_radio.clicked.connect(self.aci_radio_checked)
        self.ui.acv_radio.clicked.connect(self.acv_radio_checked)
        self.ui.dci_radio.clicked.connect(self.dci_radio_checked)
        self.ui.dcv_radio.clicked.connect(self.dcv_radio_checked)

        self.ui.detuning_radio.clicked.connect(self.detuning_radio_checked)
        self.ui.fixed_mode_radio.clicked.connect(self.fixed_radio_checked)
        self.ui.source_mode_radio.clicked.connect(self.source_radio_checked)

        self.ui.amplitude_edit.textEdited.connect(self.amplitude_edit_text_changed)
        self.ui.apply_amplitude_button.clicked.connect(self.apply_amplitude_button_clicked)
        self.ui.amplitude_edit.returnPressed.connect(self.apply_amplitude_button_clicked)

        self.ui.frequency_edit.textEdited.connect(self.frequency_edit_text_changed)
        self.ui.apply_frequency_button.clicked.connect(self.apply_frequency_button_clicked)
        self.ui.frequency_edit.returnPressed.connect(self.apply_frequency_button_clicked)

    def update_clb_list(self, a_clb_list: list):
        self.ui.clb_list_combobox.clear()
        for clb_name in a_clb_list:
            self.ui.clb_list_combobox.addItem(clb_name)

    def update_clb_status(self, a_status: clb.State):
        self.clb_state = a_status
        self.ui.clb_state_label.setText(clb.state_to_text[a_status])

    def connect_to_clb(self, a_clb_name):
        self.calibrator.connect(a_clb_name)

    @utils.exception_decorator_print
    def sync_clb_parameters(self):
        if self.calibrator.signal_type_changed():
            self.show_signal_type()

        if self.calibrator.amplitude_changed():
            self.show_amplitude()

        if self.calibrator.frequency_changed():
            self.show_frequency()

        if self.calibrator.mode_changed():
            self.show_mode()

    def enable_signal(self, a_signal_enable):
        self.calibrator.signal_enable = a_signal_enable
        self.update_signal_enable_state(a_signal_enable)

    def signal_enable_changed(self, a_enable: bool):
        self.update_signal_enable_state(a_enable)

    def update_signal_enable_state(self, a_signal_enabled: bool):
        if a_signal_enabled:
            self.ui.enable_button.setText("Стоп")
            self.ui.enable_button.setIcon(self.pause_icon)
        else:
            self.ui.enable_button.setText("Старт")
            self.ui.enable_button.setIcon(self.play_icon)

        self.ui.enable_button.setChecked(a_signal_enabled)

        self.ui.dcv_radio.setDisabled(a_signal_enabled)
        self.ui.dci_radio.setDisabled(a_signal_enabled)
        self.ui.acv_radio.setDisabled(a_signal_enabled)
        self.ui.aci_radio.setDisabled(a_signal_enabled)

        self.ui.fixed_mode_radio.setDisabled(a_signal_enabled)
        self.ui.detuning_radio.setDisabled(a_signal_enabled)
        self.ui.source_mode_radio.setDisabled(a_signal_enabled)

    # noinspection PyTypeChecker
    def wheelEvent(self, event: QtGui.QWheelEvent):
        steps = qt_utils.get_wheel_steps(event)

        keys = event.modifiers()
        if keys & QtCore.Qt.ShiftModifier:
            self.tune_amplitude(self.settings.exact_step * steps)
        elif keys & QtCore.Qt.ControlModifier:
            self.tune_amplitude(self.settings.rough_step * steps)
        else:
            self.tune_amplitude(self.settings.common_step * steps)

        event.accept()

    def set_amplitude(self, a_amplitude: float):
        self.calibrator.amplitude = a_amplitude
        self.show_amplitude()

    def show_amplitude(self):
        self.ui.amplitude_edit.setText(self.value_to_user(self.calibrator.amplitude))
        self.amplitude_edit_text_changed()

    def tune_amplitude(self, a_step):
        self.set_amplitude(utils.relative_step_change(self.calibrator.amplitude, a_step,
                                                      clb.signal_type_to_min_step[self.signal_type],
                                                      a_normalize_value=self.calibrator.amplitude))

    def amplitude_edit_text_changed(self):
        try:
            parsed = utils.parse_input(self.ui.amplitude_edit.text())
        except ValueError:
            parsed = ""
        qt_utils.update_edit_color(self.calibrator.amplitude, parsed, self.ui.amplitude_edit)

    def apply_amplitude_button_clicked(self):
        try:
            new_amplitude = utils.parse_input(self.ui.amplitude_edit.text())
            self.set_amplitude(new_amplitude)
        except ValueError:
            # Отлавливает некорректный ввод
            pass

    def set_frequency(self, a_frequency):
        self.calibrator.frequency = a_frequency
        self.show_frequency()

    def show_frequency(self):
        self.ui.frequency_edit.setText(utils.float_to_string(self.calibrator.frequency))
        self.frequency_edit_text_changed()

    def frequency_edit_text_changed(self):
        qt_utils.update_edit_color(self.calibrator.frequency,
                                   self.ui.frequency_edit.text().replace(",", "."),
                                   self.ui.frequency_edit)

    def apply_frequency_button_clicked(self):
        try:
            new_frequency = utils.parse_input(self.ui.frequency_edit.text())
            self.set_frequency(new_frequency)
        except ValueError:
            # Отлавливает некорректный ввод
            pass

    def aci_radio_checked(self):
        self.update_signal_type(clb.SignalType.ACI)

    def acv_radio_checked(self):
        self.update_signal_type(clb.SignalType.ACV)

    def dci_radio_checked(self):
        self.update_signal_type(clb.SignalType.DCI)

    def dcv_radio_checked(self):
        self.update_signal_type(clb.SignalType.DCV)

    def source_radio_checked(self):
        self.update_mode(clb.Mode.SOURCE)

    def fixed_radio_checked(self):
        self.update_mode(clb.Mode.FIXED_RANGE)

    def detuning_radio_checked(self):
        self.update_mode(clb.Mode.DETUNING)

    def update_signal_type(self, a_signal_type: clb.SignalType):
        if not self.calibrator.signal_enable:
            self.calibrator.signal_type = a_signal_type
            self.show_signal_type()

    def show_signal_type(self):
        self.signal_type = self.calibrator.signal_type
        self.signal_type_to_radio[self.signal_type].setChecked(True)
        self.units = clb.signal_type_to_units[self.signal_type]
        self.value_to_user = utils.value_to_user_with_units(self.units)
        self.show_amplitude()

    def update_mode(self, a_mode: clb.Mode):
        if not self.calibrator.signal_enable:
            self.calibrator.mode = a_mode
            self.mode = a_mode

    def show_mode(self):
        self.mode = self.calibrator.mode
        self.mode_to_radio[self.mode].setChecked(True)

    def closeEvent(self, a_event: QtGui.QCloseEvent) -> None:
        self.calibrator.signal_enable = False
