import os
import shutil

from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QHeaderView, QListWidgetItem, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from mpl_toolkits.axisartist.parasite_axes import HostAxes, ParasiteAxes
from pyqtgraph import PlotWidget
import time
import csv
import multiprocessing as mp
from datetime import timedelta

from moldyn.utils.data_mng import DynState, tmp1_path, tmp_path

MODEL_FILE_FILTER = "Model file (*.mdl);;Legacy Model file (*.zip)"

SIMULATION_FILE_FILTER_ = "Simulation file (*.mds);;\
                                                                                Legacy Simulation file (*.zip)"

try:
    mp.set_start_method('spawn')
except RuntimeError:
    pass

from multiprocessing import Process, Queue

from collections import deque

from .qt.mainwindow import Ui_MainWindow

from .create_model import CreateModelDialog
from .edit_model import EditModelDialog
from .model_viewer import ModelView

from ._conv import _float

from ..simulation.builder import Model
from ..simulation.runner import Simulation

from ..processing import visualisation as visu
from ..processing.data_proc import PDF
from . import draggableLine


class MoldynMainWindow(QMainWindow):
    updated_signal = pyqtSignal(int, float)
    movie_progress_signal = pyqtSignal(int)
    displayed_properties = dict()

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Panneau modèle
        self.ui.newModelBtn.clicked.connect(self.create_model)
        self.ui.loadModelBtn.clicked.connect(self.load_model)
        self.ui.saveModelBtn.clicked.connect(self.save_model)
        self.ui.loadSimuBtn.clicked.connect(self.load_simulation)
        self.ui.gotoSimuBtn.clicked.connect(self.goto_simu)
        self.ui.newSimuBtn.clicked.connect(self.reset_model)
        self.ui.editModelBtn.clicked.connect(self.edit_model)

        self.displayed_properties_list = {
            "display_name" : ["Name"],
            "T" : ["Temperature", "K"],
            "Lennard-Jones and mass" : {
                "First species" : {
                    "sigma_a" : ["Sigma", "m"],
                    "epsilon_a" : ["Epsilon", "J"],
                    "m_a" : ["Atomic mass", "kg"],
                    "rcut_a" : ["rcut_a", "m"],
                },
                "Second species" : {
                    "sigma_b" : ["Sigma", "m"],
                    "epsilon_b" : ["Epsilon", "J"],
                    "m_b" : ["Atomic mass", "kg"],
                    "rcut_b" : ["rcut_b", "m"],
                },
                "Inter-species" : {
                    "sigma_ab" : ["Sigma", "m"],
                    "epsilon_ab" : ["Epsilon", "J"],
                    "rcut_ab" : ["rcut_ab", "m"],
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
            },
        }

        def sub_items(item, parent):
            for k in item:
                if type(item[k]) == list:
                    if len(item[k])>1:
                        item[k][1:] = ["", item[k][1]]
                    current_item = QTreeWidgetItem(item[k])
                    self.displayed_properties[k] = current_item
                else:
                    current_item = QTreeWidgetItem([k])
                    sub_items(item[k], current_item)
                parent.addChild(current_item)
                current_item.setExpanded(True)

        self.ui.paramsTreeWidget.addChild = self.ui.paramsTreeWidget.addTopLevelItem
        self.ui.paramsTreeWidget.header().setResizeMode(QHeaderView.ResizeToContents)

        sub_items(self.displayed_properties_list, self.ui.paramsTreeWidget)

        # Panneau simu

        self.ui.iterationsSpinBox.valueChanged.connect(self.update_simu_time)
        self.ui.simulationTimeLineEdit.editingFinished.connect(self.update_iters)

        self.ui.simuBtn.clicked.connect(self.simulate)

        self.updated_signal.connect(self.update_progress)

        self.ui.designTemperatureBtn.clicked.connect(self.design_temperature_profile)

        self.progress_plt = PlotWidget(self.ui.progress_groupBox)
        self.ui.progress_groupBox.layout().addWidget(self.progress_plt, 2, 0, 1, 3)
        self.progress_plt.setXRange(0,1)
        self.progress_plt.setLabel('bottom',text='Iteration')
        self.progress_plt.setLabel('left',text='Speed', units='Iteration/s')
        self.progress_gr = self.progress_plt.plot(pen='y')

        self.t_deque = deque()

        self.ui.gotoProcessBtn.clicked.connect(self.goto_process)

        self.ui.RTViewBtn.clicked.connect(self.show_model)

        # Panneau processing

        self.ui.saveRModelBtn.clicked.connect(self.save_final_model)
        self.ui.saveSimuBtn.clicked.connect(self.save_simu_history)
        self.ui.reuseModelBtn.clicked.connect(self.reuse_model)

        self.ui.exportBtn.clicked.connect(self.export_to_csv)

        self.ui.PDFButton.clicked.connect(self.PDF)

        self.temporal_variables = {
            "Time":["time","s"],
            "Temperature":["T","K"],
            "Temperature control":["T_ctrl","K"],
            "Microscopic kinetic energy":["EC","J"],
            "Inter-atomic potential energy":["EP","J"],
            "Total energy":["ET","J"],
            "Number of bonds per atom":["bonds"],
            "Iteration":["iters"],
        }

        self.temp_variables_w = []

        for v in self.temporal_variables:
            self.ui.lineComboW.addItem(v)
            i = QListWidgetItem(v)
            i.setCheckState(False)
            self.temp_variables_w.append(i)
            self.ui.lineListW.addItem(i)

        self._1d_options = {
            "log x":None,
            "log y":None,
            "grid":None,
        }
        for i_n in self._1d_options:
            i = QListWidgetItem(i_n)
            i.setCheckState(False)
            self.ui.list1DOptions.addItem(i)
            self._1d_options[i_n] = i

        self.ui.plotB.clicked.connect(self.line_graph)

        self._2d_options = {
            "density map": None,
            "deformation (compression)":None,
            "deformation (shear)":None,
            "particles": None,
        }
        for i_n in self._2d_options:
            i = QListWidgetItem(i_n)
            i.setCheckState(False)
            self.ui.surfListW.addItem(i)
            self._2d_options[i_n] = i

        self.ui.drawSurfButton.clicked.connect(self.draw_surf)

        self.ui.makeMovieBtn.clicked.connect(self.make_movie)
        self.movie_progress_signal.connect(self.ui.movieProgressBar.setValue)

        # Misc
        try:
            self._load_model(tmp_path)
        except:
            self.ui.statusbar.showMessage("Please choose a model.")
        else:
            self.ui.statusbar.showMessage("Using cached model.")

        self.show()

    # Panneau modèle

    def set_model(self, model):
        self.model = model

        self.ui.saveAllAtomsPositionCheckBox.setEnabled(True)
        self.ui.saveModelBtn.setEnabled(True)

        self.ui.gotoSimuBtn.setEnabled(True)
        self.ui.tab_simu.setEnabled(True)

        self.simulation = Simulation(self.model, prefer_gpu=self.ui.tryToUseGPUCheckBox.checkState())
        self.model_view = ModelView(self.simulation.model)

        for dp in self.displayed_properties:
            self.displayed_properties[dp].setText(1, str(self.model.__getattr__(dp)))

        self.update_simu_time()

        self.model_to_cache()

        self.ui.tab_processing.setEnabled(False)
        self.ui.currentTime.setText("0")
        self.ui.currentIteration.setText("0")
        self.ui.editModelBtn.setEnabled(True)
        self.ui.newSimuBtn.setEnabled(True)

        self.ui.statusbar.showMessage("Model loaded, simulation can begin.")

    def reset_model(self):
        self.set_model(self.model)

    def edit_model(self):
        self.emd = EditModelDialog(self)
        self.emd.show()

    def load_simulation(self):
        path, filter = QFileDialog.getOpenFileName(caption="Load model", filter=SIMULATION_FILE_FILTER_,
                                                   options=QFileDialog.DontUseNativeDialog)
        if path:
            ds = self._load_model(path)
            with ds.open(ds.STATE_FCT, 'r') as IO:
                for key, item in IO.items():
                    self.simulation.state_fct[key] = item
            c_i = len(self.simulation.state_fct["T"])
            self.simulation.current_iter = c_i
            self.ui.currentIteration.setText(str(c_i))
            self.ui.currentTime.setText(str((c_i)*self.model.dt))
            self.enable_process_tab(True)
            t, T = self.simulation.state_fct["T_ramps"]
            if len(t)>1:
                self.simulation.set_T_ramps(t, T)
            t, Fx = self.simulation.state_fct["Fx_ramps"]
            if len(t)>1:
                self.simulation.set_Fx_ramps(t, Fx)
            t, Fy = self.simulation.state_fct["Fy_ramps"]
            if len(t)>1:
                self.simulation.set_Fy_ramps(t, Fy)
            sp = self.simulation.model.params["save_pos_history"]
            self.ui.groupBoxMovie.setEnabled(sp)
            self.ui.saveAllAtomsPositionCheckBox.setCheckState(sp)
            self.ui.saveAllAtomsPositionCheckBox.setEnabled(False)
            self.ui.statusbar.showMessage("Simulation history loaded.")

    def show_model(self):
        self.model_view.show() # bidon mais nécessaire pour que ça marche : on risque de redéfinir model donc model_view

    def create_model(self):
        self.cmd = CreateModelDialog(self)
        self.cmd.show()

    def load_model(self):
        path, filter = QFileDialog.getOpenFileName(caption="Load model", filter=MODEL_FILE_FILTER,
                                                   options=QFileDialog.DontUseNativeDialog)
        if path:
            self._load_model(path)

    def _load_model(self, path):
        ds = DynState(path)
        model = Model()
        # position of particles
        with ds.open(ds.POS, 'r') as IO:
            model.pos = IO.load()
        # parameters
        with ds.open(ds.PAR) as IO:
            for key, item in IO.items():
                model.params[key] = item
        # velocity
        with ds.open(ds.VEL, 'r') as IO:
            model.v = IO.load()

        model._m()

        self.set_model(model)
        return ds

    def _save_model(self, m):
        path, filter = QFileDialog.getSaveFileName(caption="Save model", filter=MODEL_FILE_FILTER,
                                                   options=QFileDialog.DontUseNativeDialog)
        print(filter)
        if path:
            path = self._correct_path(path, filter, [".zip", ".mdl"])
            try:
                shutil.rmtree(tmp1_path)
            except FileNotFoundError:
                pass
            ds = DynState(tmp1_path)
            ds.save_model(m)
            ds.to_zip(path)

    def _correct_path(self, path, filter, expected):
        for ext in expected:
            if not path.endswith(ext) and ext in filter:
                path += ext
                return path
        return path

    def save_model(self):
        self._save_model(self.model)

    def save_final_model(self):
        self._save_model(self.simulation.model)

    # Panneau simu

    def _model_to_cache(self, index):
        if (self.ui.tabWidget.currentWidget() is self.ui.tab_simu):
            self.model_to_cache()

    def model_to_cache(self):
        if self.model:
            self.ds = DynState(tmp_path)
            self.ds.save_model(self.model)

    def update_iters(self):
        try:
            t = _float(self.ui.simulationTimeLineEdit)
        except:
            self.update_simu_time()
        else:
            self.ui.iterationsSpinBox.setValue(int(t/self.simulation.model.dt))

    def update_simu_time(self, v=None):
        self.ui.simulationTimeLineEdit.setText(str(self.model.dt*self.ui.iterationsSpinBox.value()))
        self.ui.simuProgressBar.setMaximum(self.ui.iterationsSpinBox.value())
        self.progress_plt.setXRange(0, self.ui.iterationsSpinBox.value())

    def goto_simu(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_simu)

    def design_temperature_profile(self):
        queue = Queue(1)
        axis = (0, (self.ui.iterationsSpinBox.value()+self.simulation.current_iter)*self.model.dt, 0, 100)
        queue.put((axis, *self.simulation.T_ramps, "Time (s)", "Temperature (K)", 0))
        design_thread = Process(target=draggableLine.main, args=(queue,))
        design_thread.start()
        design_thread.join()
        x_data, y_data = queue.get()
        queue.close()
        if len(x_data)<2:
            qmb = QMessageBox()
            qmb.setText("This only works with at least two points.")
            qmb.exec()
            return
        self.simulation.set_T_ramps(x_data, y_data)

    def update_progress(self, v, new_t):
        c_i = v+1 - self.c_i
        self.t_deque.append(1/(new_t - self.last_t))
        self.last_t = new_t
        self.ui.simuProgressBar.setValue(c_i)
        if c_i==self.ui.iterationsSpinBox.value() or not c_i%10:
            self.progress_gr.setData(self.t_deque)
            self.ui.currentIteration.setText(str(v+1))
            self.ui.currentTime.setText(str((v+1)*self.model.dt))
            self.ui.ETA.setText(str(timedelta(seconds=int( (self.ui.iterationsSpinBox.value()/c_i - 1)*(new_t-self.simu_starttime)))))

        if self.save_pos:
            self.pos_IO.save(self.simulation.model.pos)

    def simulate(self):
        self.ui.simuBtn.setEnabled(False)
        self.ui.iterationsSpinBox.setEnabled(False)
        self.ui.simulationTimeLineEdit.setEnabled(False)
        self.ui.tryToUseGPUCheckBox.setEnabled(False)
        self.ui.temperature_groupBox.setEnabled(False)
        self.ui.saveAllAtomsPositionCheckBox.setEnabled(False)
        self.enable_process_tab(False)
        self.ui.simuProgressBar.setValue(0)
        self.last_t = time.perf_counter()
        self.t_deque.clear()
        self.t_deque.append(0)
        self.ui.statusbar.showMessage("Simulation is running...")

        self.save_pos = self.ui.saveAllAtomsPositionCheckBox.checkState()
        self.simulation.model.params["save_pos_history"] = self.save_pos
        if self.save_pos:
            mode = "a" if self.simulation.current_iter else "w"

            self.pos_IO = DynState(tmp_path).open(DynState.POS_H, mode=mode)
            self.pos_IO.__enter__()

        if len(self.simulation.T_ramps[0]):
            final_t = (self.simulation.current_iter + self.ui.iterationsSpinBox.value())*self.model.dt
            t, T = map(list,self.simulation.T_ramps)
            t.append(final_t)
            T.append(self.simulation.T_f(final_t))
            self.simulation.set_T_ramps(t, T)

        def run():
            # Pour continuer la simu précedente. On est obligés d'en créer une nouvelle pour des questions de scope.
            # On pourrait créer et conserver le thread une bonne fois pour toutes, pour que ce bricolage cesse.
            del(self.simulation._compute) # le module de calcul risque de continuer à exister sinon
            self.c_i = self.simulation.current_iter
            self.simulation = Simulation(simulation=self.simulation, prefer_gpu=self.ui.tryToUseGPUCheckBox.checkState())
            self.model_view = ModelView(self.simulation.model)
            self.simu_starttime = time.perf_counter()
            def up(s):
                self.updated_signal.emit(s.current_iter, time.perf_counter())
            self.simulation.iter(self.ui.iterationsSpinBox.value(), up)
            self.simu_thr.exit()

        def end():
            if self.save_pos:
                self.pos_IO.file.close()

            with DynState(tmp_path).open(DynState.STATE_FCT, mode="w") as ds:
                ds.from_dict(self.simulation.state_fct)

            self.enable_process_tab(True)
            self.ui.simuBtn.setEnabled(True)
            self.ui.iterationsSpinBox.setEnabled(True)
            self.ui.tryToUseGPUCheckBox.setEnabled(True)
            self.ui.simulationTimeLineEdit.setEnabled(True)
            self.ui.temperature_groupBox.setEnabled(True)
            self.ui.groupBoxMovie.setEnabled(self.save_pos)
            self.ui.statusbar.showMessage("Simulation complete. (Iterations : " + str(self.simulation.current_iter) + ")")

        self.simu_thr = QThread()
        self.simu_thr.run = run
        self.simu_thr.finished.connect(end)
        self.simu_thr.start()

    def enable_process_tab(self, b):
        self.ui.tab_processing.setEnabled(b)
        self.ui.gotoProcessBtn.setEnabled(b)

    def goto_process(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_processing)

    # Panneau process

    def reuse_model(self):
        self.set_model(self.simulation.model)
        self.ui.tabWidget.setCurrentWidget(self.ui.tab_model)

    def save_simu_history(self):
        path, filter = QFileDialog.getSaveFileName(caption="Save simulation history", filter=SIMULATION_FILE_FILTER_,
                                                   options=QFileDialog.DontUseNativeDialog)
        if path:
            path = self._correct_path(path, filter, [".zip", ".mds"])
            #shutil.rmtree('./data/tmp1')
            ds = DynState(tmp_path)
            if not self.ui.saveAllAtomsPositionCheckBox.checkState():
                try:
                    os.remove(tmp_path+'/'+DynState.POS_H)
                except:
                    pass
            ds.save_model(self.simulation.model)
            ds.to_zip(path)

    def export_to_csv(self):
        path, filter = QFileDialog.getSaveFileName(caption="Export to CSV", filter="CSV file (*.csv)",
                                                   options=QFileDialog.DontUseNativeDialog)
        if path:
            path = self._correct_path(path, filter, [".csv"])
            with open(path, "w", newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(self.temporal_variables.keys())
                csvwriter.writerows(zip(*(self.simulation.state_fct[s[0]] for s in self.temporal_variables.values())))

    def line_graph(self):
        ords = [i.text() for i in self.temp_variables_w if i.checkState()]
        if not len(ords):
            return

        absc = self.ui.lineComboW.currentText()

        def values(s):
            return self.simulation.state_fct[self.temporal_variables[s][0]]

        def label(s):
            if len(self.temporal_variables[s])>1:
                return s + " (" + self.temporal_variables[s][1] + ")"
            return s

        def dimension(s):
            if "energy" in s:
                return "Energy (J)"
            elif "Temperature" in s:
                return "Temperature (K)"
            else:
                return label(s)

        dimensions = list(set(dimension(s) for s in ords))
        axis = dict()

        visu.plt.ioff()
        fig = visu.plt.figure()

        gr_opts = dict()
        for o in self._1d_options:
            gr_opts[o] = self._1d_options[o].checkState()

        host = HostAxes(fig, [0.15, 0.1, 0.75-(0.04*len(dimensions)), 0.8])
        host.set_xlabel(label(absc))
        host.set_ylabel(dimensions[0])
        if gr_opts["log x"]:
            host.semilogx()
        if gr_opts["log y"]:
            host.semilogy()
        if gr_opts["grid"]:
            host.grid(True, which="minor", linestyle="--")
            host.grid(True, which="major")

        if len(dimensions)>1:
            host.axis["right"].set_visible(False)

        axis[dimensions[0]] = host

        for i, dim in enumerate(dimensions[1:]):
            par = ParasiteAxes(host, sharex=host)
            host.parasites.append(par)
            par.axis["right"] = par.get_grid_helper().new_fixed_axis(loc="right", axes=par, offset=(55*i, 0))
            par.axis["right"].set_visible(True)
            par.set_ylabel(dim)
            par.axis["right"].major_ticklabels.set_visible(True)
            par.axis["right"].label.set_visible(True)
            axis[dim] = par
            if gr_opts["log x"]:
                par.semilogx()
            if gr_opts["log y"]:
                par.semilogy()

        for i in ords:
            axis[dimension(i)].plot(values(absc), values(i), label=label(i))

        fig.add_axes(host)
        host.legend()
        visu.plt.show()

    def PDF(self):
        """Pair Distribution Function"""
        self.old_status = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage("Computing Pair Distribution Function...")

        visu.plt.ioff()
        d = PDF(self.simulation.model.pos, self.ui.PDFNSpinBox.value(), self.ui.PDFDistSpinBox.value()*max(self.model.rcut_a, self.model.rcut_b, self.model.rcut_ab), 100)
        visu.plt.figure()
        visu.plt.plot(*d)
        visu.plt.xlabel("Distance (m)")
        visu.plt.show()

        self.ui.statusbar.showMessage(self.old_status)

    def draw_surf(self):
        self.old_status = self.ui.statusbar.currentMessage()

        gr_opts = dict()
        for o in self._2d_options:
            gr_opts[o] = self._2d_options[o].checkState()

        visu.plt.figure()

        if gr_opts["density map"]:
            self.ui.statusbar.showMessage("Computing density map...")
            visu.plot_densityf(self.simulation.model, 50)

        if gr_opts["deformation (compression)"]:
            self.ui.statusbar.showMessage("Computing deformation...")
            visu.deformation_volume(self.model, self.simulation.model, self.ui.deformationDistSpinBox.value()*max(self.model.rcut_a, self.model.rcut_b, self.model.rcut_ab))

        if gr_opts["deformation (shear)"]:
            self.ui.statusbar.showMessage("Computing deformation...")
            visu.deformation_dev(self.model, self.simulation.model, self.ui.deformationDistSpinBox.value()*max(self.model.rcut_a, self.model.rcut_b, self.model.rcut_ab))

        if gr_opts["particles"]:
            visu.plot_particles(self.simulation.model)

        visu.plt.ylim(self.model.y_lim_inf, self.model.y_lim_sup)
        visu.plt.xlim(self.model.x_lim_inf, self.model.x_lim_sup)

        visu.plt.show()

        self.ui.statusbar.showMessage(self.old_status)

    def make_movie(self):
        path, filter = QFileDialog.getSaveFileName(caption="Make movie", filter="Video file (*.mp4)",
                                                   options=QFileDialog.DontUseNativeDialog)
        if path:
            path = self._correct_path(path, filter, [".mp4"])
            self.ui.tab_model.setEnabled(False)
            self.ui.tab_simu.setEnabled(False)
            self.ui.groupBoxMovie.setEnabled(False)
            self.ui.movieProgressBar.setMaximum(self.simulation.current_iter)

            def run():
                def up(k):
                    self.movie_progress_signal.emit(k)

                visu.make_movie(self.simulation, DynState(tmp_path), path, self.ui.stepsByFrameSpinBox.value(),
                                self.ui.FPSSpinBox.value(), callback=up)

            def end():
                self.ui.tab_model.setEnabled(True)
                self.ui.tab_simu.setEnabled(True)
                self.ui.groupBoxMovie.setEnabled(True)
                self.ui.movieProgressBar.setValue(self.simulation.current_iter)

            self.render_thr = QThread()
            self.render_thr.run = run
            self.render_thr.finished.connect(end)
            self.render_thr.start()
