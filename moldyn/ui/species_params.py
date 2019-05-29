from PyQt5.QtWidgets import QWidget
from .qt.species_params import Ui_species_params
from ..data.atom_preset import atoms

class species_params(QWidget):
    def __init__(self,*args):
        super().__init__(*args)
        self.ui = Ui_species_params()
        self.ui.setupUi(self)

        for atom in atoms:
            self.ui.presetComboBox.addItem(atom)

        self.ui.presetComboBox.currentTextChanged.connect(self.set_preset)

        self.show()

    def set_preset(self, a):
        if a in atoms:
            self.ui.nameLineEdit.setText(a)
            self.ui.epsilonJLineEdit.setText(str(atoms[a][0]))
            self.ui.sigmaMLineEdit.setText(str(atoms[a][1]))
            self.ui.massKgLineEdit.setText(str(atoms[a][2]))