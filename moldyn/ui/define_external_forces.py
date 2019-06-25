from PyQt5.QtWidgets import QWidget

from .qt.define_external_forces import Ui_ExternalForces

from ._conv import _float


class EditModelDialog(QWidget):

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = Ui_ExternalForces()
        self.ui.setupUi(self)

        self.show()

    def set_up_lower_limit(self, v):
        self.ui.lowerLimitMLineEdit.setText(str(v))

    @property(set_up_lower_limit)
    def up_lower_limit(self):
        return _float(self.ui.lowerLimitMLineEdit, 0)

    def set_up_apply(self, b):
        self.ui.applyExternalForceCheckBox.setChecked(b)
        self.ui.up_components.setEnabled(b)

    @property(set_up_apply)
    def up_apply(self):
        return self.ui.applyExternalForceCheckBox.isChecked()

    def set_up_x_component(self, v):
        self.ui.xForceComponentPerAtomNLineEdit.setText(str(v))

    @property(set_up_x_component)
    def up_x_component(self):
        return _float(self.ui.xForceComponentPerAtomNLineEdit, 0)

    def set_up_y_component(self, v):
        self.ui.yForceComponentPerAtomNLineEdit.setText(str(v))

    @property(set_up_y_component)
    def up_y_component(self):
        return _float(self.ui.yForceComponentPerAtomNLineEdit, 0)

    def set_low_upper_limit(self, v):
        self.ui.upperLimitMLineEdit.setText(str(v))

    @property(set_low_upper_limit)
    def low_upper_limit(self):
        return _float(self.ui.upperLimitMLineEdit, 0)

    def set_low_block(self, b):
        self.ui.blockCheckBox.setChecked(b)

    @property(set_low_block)
    def low_block(self):
        return self.ui.blockCheckBox.isChecked()
