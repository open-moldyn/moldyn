from PyQt5.QtWidgets import QDialog

from .qt.edit_model import Ui_EditModel

from .define_external_forces import define_exernal_forces

class EditModelDialog(QDialog):

    def __init__(self, parent_window=None):
        super().__init__()
        self.ui = Ui_EditModel()
        self.ui.setupUi(self)

        self.parent_window = parent_window

        self.model = parent_window.simulation.model # indispensable pour ne garder que les modifs validées
        self.simulation = parent_window.simulation

        self.ui.enableXPeriodicBoudariesCheckBox.setChecked(self.model.x_periodic)
        self.ui.enableYPeriodicBoudariesCheckBox.setChecked(self.model.y_periodic)

        self.external_forces = define_exernal_forces(simulation=parent_window.simulation, until=parent_window.ui.iterationsSpinBox.value())
        self.ui.verticalLayout.addWidget(self.external_forces)

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)


    def accept(self):
        self.model.x_periodic = self.ui.enableXPeriodicBoudariesCheckBox.isChecked()
        self.model.y_periodic = self.ui.enableYPeriodicBoudariesCheckBox.isChecked()
        self.model.params["up_apply_force_x"] = self.external_forces.up_apply_x
        self.model.params["up_apply_force_y"] = self.external_forces.up_apply_y
        self.model.params["low_block"] = self.external_forces.low_block
        self.simulation.set_Fx_ramps(*self.external_forces.up_x_component)
        self.simulation.set_Fy_ramps(*self.external_forces.up_y_component)
        super().accept()