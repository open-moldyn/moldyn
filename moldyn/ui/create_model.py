import sys
from PyQt5.QtWidgets import QDialog, QApplication, QWizard
from qt.create_model import Ui_CreateModel
from species_params import species_params

class CreateModelDialog(QWizard):
    def __init__(self):
        super().__init__()
        self.ui = Ui_CreateModel()
        self.ui.setupUi(self)
        species_a_params = species_params()
        species_b_params = species_params()
        self.ui.layout_a.addWidget(species_a_params)
        self.ui.layout_b.addWidget(species_b_params)
        self.show()

app = QApplication(sys.argv)
w = CreateModelDialog()
w.show()
sys.exit(app.exec_())