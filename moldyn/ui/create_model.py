import sys
from PyQt5.QtWidgets import QDialog, QApplication, QWizard, QMessageBox
from PyQt5.QtCore import pyqtSignal
from .qt.create_model import Ui_CreateModel
from .species_params import species_params

import  matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

from ..simulation.builder import Model

class CreateModelDialog(QWizard):
    def __init__(self):
        super().__init__()
        self.ui = Ui_CreateModel()
        self.ui.setupUi(self)
        species_a_params = species_params()
        species_b_params = species_params()
        self.ui.layout_a.addWidget(species_a_params)
        self.ui.layout_b.addWidget(species_b_params)

        self.model = Model()

        self.ui.keepRatioCheckBox.stateChanged.connect(self.keepRatio)

        self.ui.gridWidth.valueChanged.connect(self.gridWChanged)
        self.ui.gridHeight.valueChanged.connect(self.gridHChanged)

        self.ui.previewButton.clicked.connect(self.preview)

        self.ui.distanceBetweenAtoms.editingFinished.connect(self.checkDistance)

        self.ui.firstSpeciesMoleFraction.valueChanged.connect(self.model.set_x_a)

        self.show()

    def keepRatio(self, b):
        b = bool(b)
        self.ui.gridHeight.setReadOnly(b)
        self.ui.gridHeight.setValue(self.ui.gridWidth.value())

    def gridWChanged(self, v):
        if self.ui.gridHeight.isReadOnly():
            self.ui.gridHeight.setValue(v)
        self.ui.label_atom_number.setText(str(v * self.ui.gridHeight.value()))

    def gridHChanged(self, v):
        self.ui.label_atom_number.setText(str(v * self.ui.gridWidth.value()))

    def checkDistance(self):
        try:
            self.ui.distanceBetweenAtoms.setText(str(float(self.ui.distanceBetweenAtoms.text())))
        except:
            QMessageBox.warning(self, "Distance error", "Distance must be a number", QMessageBox.Ok)
            self.ui.distanceBetweenAtoms.setFocus()


    def preview(self, b):
        try:
            d = float(self.ui.distanceBetweenAtoms.text())
        except:
            self.checkDistance()
        else:
            self.model.atom_grid(self.ui.gridWidth.value(), self.ui.gridHeight.value(), d)
            self.model.shuffle_atoms()
            plt.axis("equal")
            plt.ylim(self.model.y_lim_inf, self.model.y_lim_sup)
            plt.xlim(self.model.x_lim_inf, self.model.x_lim_sup)
            plt.plot(*self.model.pos[:self.model.n_a,:].T, "ro", markersize=1)
            plt.plot(*self.model.pos[self.model.n_a:,:].T, "bo", markersize=1)
            plt.show()