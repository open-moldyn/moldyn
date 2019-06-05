# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(499, 445)
        MainWindow.setWindowTitle("OpenMoldyn")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_model = QtWidgets.QWidget()
        self.tab_model.setObjectName("tab_model")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_model)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.newModelBtn = QtWidgets.QToolButton(self.tab_model)
        self.newModelBtn.setObjectName("newModelBtn")
        self.gridLayout_2.addWidget(self.newModelBtn, 1, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(self.tab_model)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2.addWidget(self.groupBox, 3, 0, 1, 4)
        self.loadModelBtn = QtWidgets.QToolButton(self.tab_model)
        self.loadModelBtn.setObjectName("loadModelBtn")
        self.gridLayout_2.addWidget(self.loadModelBtn, 1, 1, 1, 1)
        self.gotoSimuBtn = QtWidgets.QCommandLinkButton(self.tab_model)
        self.gotoSimuBtn.setEnabled(False)
        self.gotoSimuBtn.setObjectName("gotoSimuBtn")
        self.gridLayout_2.addWidget(self.gotoSimuBtn, 4, 0, 1, 4)
        self.tabWidget.addTab(self.tab_model, "")
        self.tab_simu = QtWidgets.QWidget()
        self.tab_simu.setEnabled(False)
        self.tab_simu.setObjectName("tab_simu")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_simu)
        self.gridLayout_3.setObjectName("gridLayout_3")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem, 4, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_simu)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.simuProgressBar = QtWidgets.QProgressBar(self.groupBox_2)
        self.simuProgressBar.setMaximum(1)
        self.simuProgressBar.setProperty("value", 0)
        self.simuProgressBar.setObjectName("simuProgressBar")
        self.gridLayout_4.addWidget(self.simuProgressBar, 0, 0, 1, 1)
        self.RTViewBtn = QtWidgets.QToolButton(self.groupBox_2)
        self.RTViewBtn.setObjectName("RTViewBtn")
        self.gridLayout_4.addWidget(self.RTViewBtn, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 3, 0, 1, 2)
        self.simuBtn = QtWidgets.QCommandLinkButton(self.tab_simu)
        self.simuBtn.setObjectName("simuBtn")
        self.gridLayout_3.addWidget(self.simuBtn, 1, 1, 1, 1)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.iterationsLabel = QtWidgets.QLabel(self.tab_simu)
        self.iterationsLabel.setObjectName("iterationsLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.iterationsLabel)
        self.iterationsSpinBox = QtWidgets.QSpinBox(self.tab_simu)
        self.iterationsSpinBox.setMaximum(210000766)
        self.iterationsSpinBox.setSingleStep(100)
        self.iterationsSpinBox.setProperty("value", 1000)
        self.iterationsSpinBox.setObjectName("iterationsSpinBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.iterationsSpinBox)
        self.simulationTimeLabel = QtWidgets.QLabel(self.tab_simu)
        self.simulationTimeLabel.setObjectName("simulationTimeLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.simulationTimeLabel)
        self.simulationTimeLineEdit = QtWidgets.QLineEdit(self.tab_simu)
        self.simulationTimeLineEdit.setObjectName("simulationTimeLineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.simulationTimeLineEdit)
        self.gridLayout_3.addLayout(self.formLayout, 1, 0, 1, 1)
        self.gotoProcessBtn = QtWidgets.QCommandLinkButton(self.tab_simu)
        self.gotoProcessBtn.setEnabled(False)
        self.gotoProcessBtn.setObjectName("gotoProcessBtn")
        self.gridLayout_3.addWidget(self.gotoProcessBtn, 5, 0, 1, 2)
        self.tabWidget.addTab(self.tab_simu, "")
        self.tab_processing = QtWidgets.QWidget()
        self.tab_processing.setEnabled(False)
        self.tab_processing.setObjectName("tab_processing")
        self.tabWidget.addTab(self.tab_processing, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 499, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen_model = QtWidgets.QAction(MainWindow)
        self.actionOpen_model.setObjectName("actionOpen_model")
        self.actionNew_simulation = QtWidgets.QAction(MainWindow)
        self.actionNew_simulation.setObjectName("actionNew_simulation")

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.newModelBtn.setText(_translate("MainWindow", "New"))
        self.groupBox.setTitle(_translate("MainWindow", "Current model"))
        self.loadModelBtn.setText(_translate("MainWindow", "Load"))
        self.gotoSimuBtn.setText(_translate("MainWindow", "Simulation"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_model), _translate("MainWindow", "Model"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Progress"))
        self.simuProgressBar.setFormat(_translate("MainWindow", "%v/%m"))
        self.RTViewBtn.setText(_translate("MainWindow", "View current state"))
        self.simuBtn.setText(_translate("MainWindow", "Launch simulation"))
        self.iterationsLabel.setText(_translate("MainWindow", "Iterations"))
        self.simulationTimeLabel.setText(_translate("MainWindow", "Simulation time (s)"))
        self.gotoProcessBtn.setText(_translate("MainWindow", "Process data"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_simu), _translate("MainWindow", "Simulation"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_processing), _translate("MainWindow", "Processing"))
        self.actionNew.setText(_translate("MainWindow", "New model"))
        self.actionOpen_model.setText(_translate("MainWindow", "Open model"))
        self.actionNew_simulation.setText(_translate("MainWindow", "New simulation"))

