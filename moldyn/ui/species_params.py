from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from .qt.species_params import Ui_species_params
from ..data.atom_preset import atoms

from ._conv import _float

class species_params(QWidget):
    editingFinished = pyqtSignal()

    def __init__(self,*args):
        super().__init__(*args)
        self.ui = Ui_species_params()
        self.ui.setupUi(self)

        for atom in atoms:
            self.ui.presetComboBox.addItem(atom)

        self.ui.presetComboBox.currentTextChanged.connect(self.set_preset)

        self.ui.sigmaMLineEdit.editingFinished.connect(self._editing_finished)
        self.ui.epsilonJLineEdit.editingFinished.connect(self._editing_finished)
        self.ui.massKgLineEdit.editingFinished.connect(self._editing_finished)

        self.show()

    def set_preset(self, a):
        if a in atoms:
            self.ui.nameLineEdit.setText(a)
            self.set_values(atoms[a])
            self._editing_finished()

    def check_values(self):
        try:
            self.get_values()
        except:
            return False
        return True

    def set_values(self, v, force = True):
        ws = (self.ui.epsilonJLineEdit, self.ui.sigmaMLineEdit, self.ui.massKgLineEdit)
        for w, av in zip(ws, v):
            lf = False
            try:
                float(w.text())
            except:
                lf = True
            if lf or force:
                w.setText(str(av))

    def get_values(self):
        wid = (
            self.ui.epsilonJLineEdit,
            self.ui.sigmaMLineEdit,
            self.ui.massKgLineEdit,
        )
        return tuple(map(_float,wid))

    def _editing_finished(self):
        self.editingFinished.emit()