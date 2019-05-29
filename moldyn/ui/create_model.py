import sys
from PyQt5.QtWidgets import QDialog, QApplication, QWizard, QMessageBox
from PyQt5.QtCore import pyqtSignal
from .qt.create_model import Ui_CreateModel
from .species_params import species_params

from ..simulation.builder import Model

import  matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt


class CreateModelDialog(QWizard):

    def __init__(self):
        super().__init__()
        self.ui = Ui_CreateModel()
        self.ui.setupUi(self)

        # Premier panneau (espèces)
        self.species_a_params = species_params()
        self.species_b_params = species_params()
        self.ui.layout_a.addWidget(self.species_a_params)
        self.ui.layout_b.addWidget(self.species_b_params)

        self.model = Model()

        # Second panneau (conf spatiale)
        self.ui.wizardPage1.validatePage =  self.to_spatial_conf

        self.ui.keepRatioCheckBox.stateChanged.connect(self.keep_ratio)

        self.ui.gridWidth.valueChanged.connect(self.grid_w_changed)
        self.ui.gridHeight.valueChanged.connect(self.grid_h_changed)

        self.ui.distanceBetweenAtoms.editingFinished.connect(self.checked_distance)

        self.ui.xPeriodicBoundariesCheckBox.stateChanged.connect(self.model.set_x_periodic)
        self.ui.yPeriodicBoudariesCheckBox.stateChanged.connect(self.model.set_y_periodic)

        self.ui.firstSpeciesMoleFraction.valueChanged.connect(self.model.set_x_a)

        self.ui.previewButton.clicked.connect(self.preview)

        # Troisième panneau (paramètres divers)
        self.ui.wizardPage2.validatePage = self.set_parameters

        self.ui.reset_ia_LJ.clicked.connect(self.reset_es_ab)

        self.ui.temperatureKDoubleSpinBox.valueChanged.connect(self.model.set_T)

        self.ui.timestepLineEdit.editingFinished.connect(self.checked_timestep)

        self.show()

    # Second panneau

    def to_spatial_conf(self):
        self.model.set_ab(
            self.species_a_params.get_values(),
            self.species_b_params.get_values()
        )
        self.ui.distanceBetweenAtoms.setText(str(self.model.re_ab))
        return True

    def keep_ratio(self, b):
        b = bool(b)
        self.ui.gridHeight.setReadOnly(b)
        self.ui.gridHeight.setValue(self.ui.gridWidth.value())

    def grid_w_changed(self, v):
        if self.ui.gridHeight.isReadOnly():
            self.ui.gridHeight.setValue(v)
        self.ui.label_atom_number.setText(str(v * self.ui.gridHeight.value()))

    def grid_h_changed(self, v):
        self.ui.label_atom_number.setText(str(v * self.ui.gridWidth.value()))

    def checked_distance(self):
        try:
            d = float(self.ui.distanceBetweenAtoms.text())
        except:
            d = self.model.re_ab
        self.ui.distanceBetweenAtoms.setText(str(d))
        return d

    def preview(self, b):
        self.model.atom_grid(self.ui.gridWidth.value(), self.ui.gridHeight.value(), self.checked_distance())
        self.model.shuffle_atoms()

        plt.axis("equal")
        plt.ylim(self.model.y_lim_inf, self.model.y_lim_sup)
        plt.xlim(self.model.x_lim_inf, self.model.x_lim_sup)
        plt.plot(*self.model.pos[:self.model.n_a,:].T, "ro", markersize=1)
        plt.plot(*self.model.pos[self.model.n_a:,:].T, "bo", markersize=1)
        plt.show()

    # Troisième panneau

    def reset_es_ab(self):
        self.ui.epsilonJLineEdit.setText(str(self.model.epsilon_ab))
        self.ui.sigmaMLineEdit.setText(str(self.model.sigma_ab))

    def set_parameters(self):
        self.model.atom_grid(self.ui.gridWidth.value(), self.ui.gridHeight.value(), self.checked_distance())
        self.model.shuffle_atoms()
        self.model.set_dt()

        self.model.T = 1.0
        self.ui.temperatureKDoubleSpinBox.setValue(1.0)

        self.reset_es_ab()

        self.ui.timestepLineEdit.setText(str(self.model.dt))

        return True

    def checked_timestep(self):
        try:
            dt = float(self.ui.timestepLineEdit.text())
        except:
            dt = self.model.dt
        self.ui.timestepLineEdit.setText(str(dt))
        self.model.dt = dt
        return dt
