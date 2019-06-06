from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import QThread, pyqtSignal
from pyqtgraph import PlotWidget
import time

from collections import deque

from .qt.mainwindow import Ui_MainWindow

from .create_model import CreateModelDialog
from .model_viewer import ModelView

from ..simulation.builder import Model
from ..simulation.runner import Simulation


class MoldynMainWindow(QMainWindow):
    updated_signal = pyqtSignal(int, float)
    displayed_properties = dict()

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Panneau modèle
        self.ui.newModelBtn.clicked.connect(self.create_model)

        self.ui.gotoSimuBtn.clicked.connect(self.goto_simu)

        self.displayed_properties_list = {
            "display_name" : ["Name"],
            "T" : ["Temperature", "K"],
            "Lennard-Jones and mass" : {
                "First species" : {
                    "sigma_a" : ["Sigma", "m"],
                    "epsilon_a" : ["Epsilon", "J"],
                    "m_a" : ["Atomic mass", "kg"],
                },
                "Second species" : {
                    "sigma_b" : ["Sigma", "m"],
                    "epsilon_b" : ["Epsilon", "J"],
                    "m_b" : ["Atomic mass", "kg"],
                },
                "Inter-species" : {
                    "sigma_ab" : ["Sigma", "m"],
                    "epsilon_ab" : ["Epsilon", "J"],
                },
            },
            "npart" : ["Atom number"],
            "x_a" : ["First species mole fraction"],
            "dt" : ["Timestep", "s"],
            "Spatial configuration" : {
                "length_x" : ["Width", "m"],
                "length_y" : ["Height", "m"],
                "x_periodic" : ["Periodic condition on x"],
                "y_periodic" : ["Periodic condition on y"],
            }
        }

        def subItems(item, parent):
            for k in item:
                if type(item[k]) == list:
                    if len(item[k])>1:
                        item[k][1:] = ["", item[k][-1]]
                    currentItem = QTreeWidgetItem(item[k])
                    self.displayed_properties[k] = currentItem
                else:
                    currentItem = QTreeWidgetItem([k])
                    subItems(item[k], currentItem)
                parent.addChild(currentItem)

        self.ui.paramsTreeWidget.addChild = self.ui.paramsTreeWidget.addTopLevelItem
        self.ui.paramsTreeWidget.header().setResizeMode(QHeaderView.ResizeToContents)

        subItems(self.displayed_properties_list, self.ui.paramsTreeWidget)


        # Panneau simu

        self.ui.iterationsSpinBox.valueChanged.connect(self.update_simu_time)
        self.ui.simulationTimeLineEdit.editingFinished.connect(self.update_iters)

        self.ui.simuBtn.clicked.connect(self.simulate)

        self.updated_signal.connect(self.update_progress)

        self.progress_plt = PlotWidget(self.ui.progress_groupBox)
        self.ui.progress_groupBox.layout().addWidget(self.progress_plt, 1, 0, 1, 2)
        self.progress_plt.setXRange(0,1)
        self.progress_plt.setLabel('bottom',text='Iteration')
        self.progress_plt.setLabel('left',text='Speed', units='Iteration/s')
        self.progress_gr = self.progress_plt.plot(pen='y')

        self.t_deque = deque()

        self.ui.gotoProcessBtn.clicked.connect(self.goto_process)

        self.ui.RTViewBtn.clicked.connect(self.show_model)

        # Misc

        self.ui.statusbar.showMessage("Please choose a model.")

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
        self.progress_plt.setXRange(0, self.ui.iterationsSpinBox.value())

    def set_model(self, model):
        self.model = model

        self.ui.gotoSimuBtn.setEnabled(True)
        self.ui.tab_simu.setEnabled(True)

        self.simulation = Simulation(self.model)
        self.model_view = ModelView(self.simulation.model)

        for dp in self.displayed_properties:
            self.displayed_properties[dp].setText(1, str(self.model.__getattr__(dp)))

        self.update_simu_time()

        self.ui.statusbar.showMessage("Model loaded, simulation can begin.")

    def show_model(self):
        self.model_view.show() # bidon mais nécessaire pour que ça marche : on risque de redéfinir model donc model_view

    def create_model(self):
        self.cmd = CreateModelDialog(self)
        self.cmd.show()

    def goto_simu(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_simu)

    def update_progress(self, v, new_t):
        self.ui.simuProgressBar.setValue(v+1)
        self.t_deque.append(1/(new_t - self.last_t))
        self.last_t = new_t
        self.progress_gr.setData(self.t_deque)

    def simulate(self):
        self.ui.simuBtn.setEnabled(False)
        self.enable_process_tab(False)
        self.ui.simuProgressBar.setValue(0)
        self.last_t = time.perf_counter()
        self.t_deque.clear()
        self.t_deque.append(0)
        self.ui.statusbar.showMessage("Simulation is running...")

        def run():
            # Pour continuer la simu précedente. On est obligés d'en créer une nouvelle pour des questions de scope.
            # On pourrait créer et conserver le thread une bonne fois pour toutes, pour que ce bricolage cesse.
            c_i = self.simulation.current_iter
            self.simulation = Simulation(self.simulation.model)
            self.simulation.current_iter = c_i # pour savoir où on en est
            self.model_view = ModelView(self.simulation.model)
            def up(s):
                self.updated_signal.emit(s.current_iter, time.perf_counter())
            self.simulation.iter(self.ui.iterationsSpinBox.value(), up)
            self.simu_thr.exit()

        def end():
            self.ui.simuBtn.setEnabled(True)
            self.enable_process_tab(True)
            self.ui.statusbar.showMessage("Simulation complete.")

        self.simu_thr = QThread()
        self.simu_thr.run = run
        self.simu_thr.finished.connect(end)
        self.simu_thr.start()

    def enable_process_tab(self, b):
        self.ui.tab_processing.setEnabled(b)
        self.ui.gotoProcessBtn.setEnabled(b)

    def goto_process(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_processing)