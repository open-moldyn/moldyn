from PyQt5.QtWidgets import QErrorMessage, QApplication, QWizard, QMessageBox
from PyQt5.QtCore import pyqtSignal
from .qt.create_model import Ui_CreateModel
from .species_params import species_params

from ..simulation.builder import Model
from .model_viewer import ModelView

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

class CreateModelDialog(QWizard):

    def __init__(self, parent_window=None):
        super().__init__()
        self.ui = Ui_CreateModel()
        self.ui.setupUi(self)

        self.parent_window = parent_window

        # Premier panneau (espèces)
        self.species_a_params = species_params()
        self.species_b_params = species_params()
        self.ui.layout_a.addWidget(self.species_a_params)
        self.ui.layout_b.addWidget(self.species_b_params)

        self.species_a_params.editingFinished.connect(self.check_species)
        self.species_b_params.editingFinished.connect(self.check_species)

        self.model = Model()

        # Second panneau (conf spatiale)
        self.ui.wizardPage1.validatePage =  self.to_spatial_conf

        self.ui.keepRatioCheckBox.stateChanged.connect(self.keep_ratio)

        self.ui.gridWidth.valueChanged.connect(self.grid_w_changed)
        self.ui.gridHeight.valueChanged.connect(self.grid_h_changed)

        self.ui.distanceBetweenAtoms.editingFinished.connect(self.checked_distance)
        self.ui.boxWidthLineEdit.editingFinished.connect(self.box_w_changed)

        self.ui.xPeriodicBoundariesCheckBox.stateChanged.connect(self.model.set_x_periodic)
        self.ui.yPeriodicBoudariesCheckBox.stateChanged.connect(self.model.set_y_periodic)

        self.ui.firstSpeciesMoleFraction.valueChanged.connect(self.model.set_x_a)

        self.ui.previewButton.clicked.connect(self.preview)

        # Troisième panneau (paramètres divers)
        self.ui.wizardPage2.validatePage = self.set_parameters

        self.ui.reset_ia_LJ.clicked.connect(self.reset_es_ab)

        self.ui.resetTimestep.clicked.connect(self.set_decent_timestep)

        self.ui.temperatureKDoubleSpinBox.valueChanged.connect(self.model.set_T)

        self.ui.timestepLineEdit.editingFinished.connect(self.checked_timestep)
        self.ui.epsilonJLineEdit.editingFinished.connect(self.check_es_ab)
        self.ui.sigmaMLineEdit.editingFinished.connect(self.check_es_ab)

        self.show()

    # Premier panneau

    def check_species(self):
        t = (self.species_a_params, self.species_b_params)
        a, b = (s.check_values() for s in t)
        if a ^ b:
            t[a].set_values(t[b].get_values(), False)
        return a or b

    # Second panneau

    def to_spatial_conf(self):
        if not self.check_species():
            qmb = QMessageBox()
            qmb.setText("Please define a species.")
            qmb.exec()
            return False

        self.model.params["display_name"] = " ".join([
            self.species_a_params.ui.nameLineEdit.text(),
            "and",
            self.species_b_params.ui.nameLineEdit.text(),
        ])
        self.model.set_ab(
            self.species_a_params.get_values(),
            self.species_b_params.get_values()
        )
        #self.ui.distanceBetweenAtoms.setText(str(self.model.re_ab))
        self.checked_distance()
        return True

    def keep_ratio(self, b):
        b = bool(b)
        self.ui.gridHeight.setReadOnly(b)
        self.ui.gridHeight.setValue(self.ui.gridWidth.value())

    def grid_w_changed(self, v):
        if self.ui.gridHeight.isReadOnly():
            self.ui.gridHeight.setValue(v)
        self.ui.label_atom_number.setText(str(v * self.ui.gridHeight.value()))
        self.checked_distance()

    def grid_h_changed(self, v):
        self.ui.label_atom_number.setText(str(v * self.ui.gridWidth.value()))

    def box_w_changed(self):
        try:
            l = float(self.ui.boxWidthLineEdit.text())
        except:
            l = float(self.ui.distanceBetweenAtoms.text()) * (self.ui.gridWidth.value())
        self.ui.boxWidthLineEdit.setText(str(l))
        self.ui.distanceBetweenAtoms.setText(str(l / (self.ui.gridWidth.value())))

    def checked_distance(self):
        try:
            d = float(self.ui.distanceBetweenAtoms.text())
        except:
            d = self.model.re_ab
        self.ui.distanceBetweenAtoms.setText(str(d))

        self.ui.boxWidthLineEdit.setText(str(d * (self.ui.gridWidth.value())))

        return d

    def preview(self, b):
        self.model.atom_grid(self.ui.gridWidth.value(), self.ui.gridHeight.value(), self.checked_distance())
        self.model.shuffle_atoms()

        self.mv = ModelView(self.model)
        self.mv.show()

    # Troisième panneau

    def reset_es_ab(self):
        self.model.calc_ab()
        self.ui.epsilonJLineEdit.setText(str(self.model.epsilon_ab))
        self.ui.sigmaMLineEdit.setText(str(self.model.sigma_ab))
        self.checked_timestep()

    def check_es_ab(self):
        try:
            epsilon_ab = float(self.ui.epsilonJLineEdit.text())
        except:
            epsilon_ab = self.model.epsilon_ab
        try:
            sigma_ab = float(self.ui.sigmaMLineEdit.text())
        except:
            sigma_ab = self.model.sigma_ab
        self.ui.epsilonJLineEdit.setText(str(epsilon_ab))
        self.ui.sigmaMLineEdit.setText(str(sigma_ab))
        self.model.params["epsilon_ab"] = epsilon_ab
        self.model.params["sigma_ab"] = sigma_ab
        self.checked_timestep()

    def reset_rcut(self):
        rcut_a = self.model.rcut_a * self.model.rcut_fact
        self.ui.r_cut_aLineEdit.setText(str(rcut_a))
        rcut_b = self.model.rcut_b * self.model.rcut_fact
        self.ui.r_cut_bLineEdit.setText(str(rcut_b))
        rcut_ab = self.model.rcut_ab * self.model.rcut_fact
        self.ui.r_cut_abLineEdit.setText(str(rcut_ab))

    def check_rcut(self):
        try:
            rcut_a = float(self.ui.r_cut_aLineEdit.text())
        except:
            rcut_a = self.model.rcut_a
        self.ui.r_cut_abLineEdit.setText(str(rcut_a))

        try:
            rcut_b = float(self.ui.r_cut_bLineEdit.text())
        except:
            rcut_b = self.model.rcut_ab
        self.ui.r_cut_bLineEdit.setText(str(rcut_b))

        try:
            rcut_ab = float(self.ui.r_cut_abLineEdit.text())
        except:
            rcut_ab = self.model.rcut_ab
        self.ui.r_cut_abLineEdit.setText(str(rcut_ab))

    def set_parameters(self):
        self.model.atom_grid(self.ui.gridWidth.value(), self.ui.gridHeight.value(), self.checked_distance())
        self.model.shuffle_atoms()
        self.model.set_dt()

        self.model.T = 1.0
        self.ui.temperatureKDoubleSpinBox.setValue(1.0)

        self.reset_es_ab()

        self.ui.timestepLineEdit.setText(str(self.model.dt))

        self.reset_rcut()

        return True

    def set_decent_timestep(self):
        self.ui.timestepLineEdit.setText(str(self.model.decent_dt()))
        self.checked_timestep()

    def checked_timestep(self):
        try:
            dt = float(self.ui.timestepLineEdit.text())
        except:
            dt = self.model.dt
        self.ui.timestepLineEdit.setText(str(dt))
        self.model.dt = dt

        decent = self.model.decent_dt()
        if dt > decent:
            qmb = QMessageBox()
            qmb.setText("The time-step may be too high. Simulation may then not be accurate enough.")
            qmb.exec()

        return dt

    def accept(self):
        self.model.params["epsilon_ab"] = float(self.ui.epsilonJLineEdit.text())
        self.model.params["sigma_ab"] = float(self.ui.sigmaMLineEdit.text())
        if self.parent_window:
            self.parent_window.set_model(self.model)
        super().accept()