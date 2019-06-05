from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal

from .qt.mainwindow import Ui_MainWindow

from .create_model import CreateModelDialog
from .model_viewer import ModelView

from ..simulation.builder import Model
from ..simulation.runner import Simulation


class MoldynMainWindow(QMainWindow):
    updated_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Panneau modèle
        self.ui.newModelBtn.clicked.connect(self.create_model)

        self.ui.gotoSimuBtn.clicked.connect(self.goto_simu)

        # Panneau simu

        self.ui.iterationsSpinBox.valueChanged.connect(self.update_simu_time)
        self.ui.simulationTimeLineEdit.editingFinished.connect(self.update_iters)

        self.ui.simuBtn.clicked.connect(self.simulate)

        self.ui.gotoProcessBtn.clicked.connect(self.goto_process)

        self.show()

    def update_iters(self):
        try:
            t = float(self.ui.simulationTimeLineEdit.text())
        except:
            self.update_simu_time()
        else:
            self.ui.iterationsSpinBox.setValue(int(t/self.simulation.model.dt))

    def update_simu_time(self, v=None):
        self.ui.simulationTimeLineEdit.setText(str(self.model.dt*self.ui.iterationsSpinBox.value()))
        self.ui.simuProgressBar.setMaximum(self.ui.iterationsSpinBox.value())

    def set_model(self, model):
        self.model = model
        self.ui.gotoSimuBtn.setEnabled(True)
        self.ui.tab_simu.setEnabled(True)
        self.simulation = Simulation(self.model)
        self.model_view = ModelView(self.simulation.model)

        self.update_simu_time()

        self.ui.RTViewBtn.clicked.connect(self.show_model)

    def show_model(self):
        self.model_view.show() # bidon mais nécessaire pour que ça marche

    def create_model(self):
        self.cmd = CreateModelDialog(self)
        self.cmd.show()

    def goto_simu(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_simu)

    def simulate(self):
        self.ui.simuBtn.setEnabled(False)
        self.enable_process_tab(False)
        self.updated_signal.connect(self.ui.simuProgressBar.setValue)
        self.ui.simuProgressBar.setValue(0)
        def run():
            self.simulation = Simulation(self.model)
            self.model_view = ModelView(self.simulation.model)
            def up(s):
                self.updated_signal.emit(s.current_iter+1)
            self.simulation.iter(self.ui.iterationsSpinBox.value(), up)
            self.ui.simuBtn.setEnabled(True)
            self.enable_process_tab(True)
        self.simu_thr = QThread()
        self.simu_thr.run = run
        self.simu_thr.start()

    def enable_process_tab(self, b):
        self.ui.tab_processing.setEnabled(b)
        self.ui.gotoProcessBtn.setEnabled(b)

    def goto_process(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_processing)