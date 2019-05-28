import sys
from PyQt5.QtWidgets import QDialog, QApplication, QWizard
from PyQt5.QtCore import pyqtSignal
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

        self.ui.keepRatioCheckBox.stateChanged.connect(self.keepRatio)

        self.ui.gridWidth.valueChanged.connect(self.gridWChanged)

        self.show()

    def keepRatio(self, b):
        b = bool(b)
        self.ui.gridHeight.setReadOnly(b)

    def gridWChanged(self, v):
        if self.ui.gridHeight.isReadOnly():
            self.ui.gridHeight.setValue(v)

# pour test
app = QApplication(sys.argv)
w = CreateModelDialog()
w.show()
sys.exit(app.exec_())