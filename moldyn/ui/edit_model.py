from PyQt5.QtWidgets import QDialog

from .qt.edit_model import Ui_EditModel

from .define_external_forces import define_exernal_forces

class EditModelDialog(QDialog):

    def __init__(self, parent_window=None):
        super().__init__()
        self.ui = Ui_EditModel()
        self.ui.setupUi(self)

        self.parent_window = parent_window

        self.model = parent_window.model.copy() # indispensable pour ne garder que les modifs validées

        self.ui.enableXPeriodicBoudariesCheckBox.setChecked(self.model.x_periodic)
        self.ui.enableYPeriodicBoudariesCheckBox.setChecked(self.model.y_periodic)

        self.external_forces = define_exernal_forces(self.model)
        self.ui.verticalLayout.addWidget(self.external_forces)

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)


    def accept(self):
        self.model.x_periodic = self.ui.enableXPeriodicBoudariesCheckBox.isChecked()
        self.model.y_periodic = self.ui.enableYPeriodicBoudariesCheckBox.isChecked()
        self.parent_window.set_model(self.model)
        super().accept()