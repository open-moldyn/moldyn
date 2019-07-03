from PyQt5.QtWidgets import QWidget, QMessageBox

from .qt.define_external_forces import Ui_ExternalForces
from multiprocessing import Process, Queue
from . import draggableLine

from ._conv import _float


class define_exernal_forces(QWidget):

    def __init__(self, *args, simulation=None, until=0):
        super().__init__(*args)
        self.ui = Ui_ExternalForces()
        self.ui.setupUi(self)

        self.up_x_component = [[],[]]
        self.up_y_component = [[],[]]

        self.until = until

        if simulation:
            self.set_simulation(simulation)

        #self.ui.applyExternalForceCheckBox.stateChanged.connect(self.ui.up_components.setEnabled)
        self.ui.applyXUp.stateChanged.connect(self.ui.xUpBtn.setEnabled)
        self.ui.applyYUp.stateChanged.connect(self.ui.yUpBtn.setEnabled)

        self.ui.xUpBtn.clicked.connect(self.design_x_component)
        self.ui.yUpBtn.clicked.connect(self.design_y_component)

        self.ui.upFractionOfSpaceDoubleSpinBox.valueChanged.connect(self.up_spinbox_changed)
        self.ui.lowFractionOfSpaceDoubleSpinBox.valueChanged.connect(self.low_spinbox_changed)

        self.ui.lowerLimitMLineEdit.editingFinished.connect(self.up_edited)
        self.ui.upperLimitMLineEdit.editingFinished.connect(self.low_edited)

        self.show()

    def set_simulation(self, simulation):
        self.simulation = simulation
        self.model = simulation.model

        self.up_apply_x = self.model.up_apply_force_x
        self.up_apply_y = self.model.up_apply_force_y
        self.low_block = self.model.low_block

        self.up_lower_limit = self.model.up_zone_lower_limit
        self.low_upper_limit = self.model.low_zone_upper_limit

        self.up_x_component = self.simulation.state_fct["Fx_ramps"]
        self.up_y_component = self.simulation.state_fct["Fy_ramps"]

        self.up_edited()
        self.low_edited()

    def design_force(self, axis_name, default):
        queue = Queue(1)
        decent_force = self.model.epsilon_ab / self.model.sigma_ab
        axis = (0, (self.until+self.simulation.current_iter)*self.model.dt, -decent_force, decent_force)
        queue.put((axis, *default, "Time (s)", "Force, "+axis_name+" component (N)", None))
        design_thread = Process(target=draggableLine.main, args=(queue,))
        design_thread.start()
        design_thread.join()
        x_data, y_data = queue.get()
        queue.close()
        if len(x_data)<2:
            qmb = QMessageBox()
            qmb.setText("This only works with at least two points.")
            qmb.exec()
            return default
        return [x_data, y_data]

    def design_x_component(self):
        self.up_x_component = self.design_force("x", self.up_x_component)

    def design_y_component(self):
        self.up_y_component = self.design_force("y", self.up_y_component)

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
    def up_apply_x(self):
        return int(self.ui.applyXUp.isChecked())

    @up_apply_x.setter
    def up_apply_x(self, b):
        self.ui.applyXUp.setChecked(b)
        self.ui.xUpBtn.setEnabled(b)

    @property
    def up_apply_y(self):
        return int(self.ui.applyYUp.isChecked())

    @up_apply_y.setter
    def up_apply_y(self, b):
        self.ui.applyYUp.setChecked(b)
        self.ui.yUpBtn.setEnabled(b)

    @property
    def low_upper_limit(self):
        return _float(self.ui.upperLimitMLineEdit, self.c_low_upper_limit)

    @low_upper_limit.setter
    def low_upper_limit(self, v):
        self.ui.upperLimitMLineEdit.setText(str(v))

    @property
    def low_block(self):
        return int(self.ui.blockCheckBox.isChecked())

    @low_block.setter
    def low_block(self, b):
        self.ui.blockCheckBox.setChecked(b)
