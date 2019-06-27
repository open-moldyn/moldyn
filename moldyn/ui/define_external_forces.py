from PyQt5.QtWidgets import QWidget

from .qt.define_external_forces import Ui_ExternalForces

from ._conv import _float


class define_exernal_forces(QWidget):

    def __init__(self, model, *args):
        super().__init__(*args)
        self.ui = Ui_ExternalForces()
        self.ui.setupUi(self)

        self.model = model

        self.ui.applyExternalForceCheckBox.stateChanged.connect(self.ui.up_components.setEnabled)

        self.ui.upFractionOfSpaceDoubleSpinBox.valueChanged.connect(self.up_spinbox_changed)
        self.ui.lowFractionOfSpaceDoubleSpinBox.valueChanged.connect(self.low_spinbox_changed)

        self.ui.lowerLimitMLineEdit.editingFinished.connect(self.up_edited)
        self.ui.upperLimitMLineEdit.editingFinished.connect(self.low_edited)

        self.up_apply = self.model.up_apply_force
        self.low_block = self.model.low_block

        self.up_lower_limit = self.model.up_zone_lower_limit
        self.low_upper_limit = self.model.low_zone_upper_limit

        self.ui.applyExternalForceCheckBox.stateChanged.connect(self.checkbox_state_changed)
        self.ui.blockCheckBox.stateChanged.connect(self.checkbox_state_changed)

        self.up_x_component = self.model.up_x_component
        self.up_y_component = self.model.up_y_component

        self.up_edited()
        self.low_edited()

        self.show()

    def checkbox_state_changed(self):
        self.model.params["up_apply_force"] = self.up_apply
        self.model.params["low_block"] = self.low_block

    def up_spinbox_changed(self):
        self.ui.lowerLimitMLineEdit.setText(str(self.c_up_lower_limit))
        self.set_up()

    def low_spinbox_changed(self):
        self.ui.upperLimitMLineEdit.setText(str(self.c_low_upper_limit))
        self.set_low()

    def up_edited(self):
        self.ui.upFractionOfSpaceDoubleSpinBox.setValue(1 - self.up_lower_limit / self.model.length_y)
        self.set_up()

    def low_edited(self):
        self.ui.lowFractionOfSpaceDoubleSpinBox.setValue(self.low_upper_limit / self.model.length_y)
        self.set_low()

    def set_up(self):
        self.model.params["up_zone_lower_limit"] = self.up_lower_limit

    def set_low(self):
        self.model.params["low_zone_upper_limit"] = self.low_upper_limit

    @property
    def c_up_lower_limit(self):
        return self.model.length_y*(1-self.ui.upFractionOfSpaceDoubleSpinBox.value())

    @property
    def c_low_upper_limit(self):
        return self.model.length_y*self.ui.lowFractionOfSpaceDoubleSpinBox.value()

    @property
    def up_lower_limit(self):
        return _float(self.ui.lowerLimitMLineEdit, self.c_up_lower_limit)

    @up_lower_limit.setter
    def up_lower_limit(self, v):
        self.ui.lowerLimitMLineEdit.setText(str(v))

    @property
    def up_apply(self):
        return self.ui.applyExternalForceCheckBox.isChecked()

    @up_apply.setter
    def up_apply(self, b):
        self.ui.applyExternalForceCheckBox.setChecked(b)
        self.ui.up_components.setEnabled(b)

    @property
    def up_x_component(self):
        return _float(self.ui.xForceComponentPerAtomNLineEdit, self.model.up_x_component)

    @up_x_component.setter
    def up_x_component(self, v):
        self.ui.xForceComponentPerAtomNLineEdit.setText(str(v))

    @property
    def up_y_component(self):
        return _float(self.ui.yForceComponentPerAtomNLineEdit, self.model.up_y_component)

    @up_y_component.setter
    def up_y_component(self, v):
        self.ui.yForceComponentPerAtomNLineEdit.setText(str(v))

    @property
    def low_upper_limit(self):
        return _float(self.ui.upperLimitMLineEdit, self.c_low_upper_limit)

    @low_upper_limit.setter
    def low_upper_limit(self, v):
        self.ui.upperLimitMLineEdit.setText(str(v))

    @property
    def low_block(self):
        return self.ui.blockCheckBox.isChecked()

    @low_block.setter
    def low_block(self, b):
        self.ui.blockCheckBox.setChecked(b)
