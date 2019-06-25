# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edit_model.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_EditModel(object):
    def setupUi(self, EditModel):
        EditModel.setObjectName("EditModel")
        EditModel.resize(493, 457)
        self.gridLayout = QtWidgets.QGridLayout(EditModel)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(EditModel)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(EditModel)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.enableXPeriodicBoudariesLabel = QtWidgets.QLabel(self.groupBox)
        self.enableXPeriodicBoudariesLabel.setObjectName("enableXPeriodicBoudariesLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.enableXPeriodicBoudariesLabel)
        self.enableXPeriodicBoudariesCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.enableXPeriodicBoudariesCheckBox.setObjectName("enableXPeriodicBoudariesCheckBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.enableXPeriodicBoudariesCheckBox)
        self.enableYPeriodicBoudariesLabel = QtWidgets.QLabel(self.groupBox)
        self.enableYPeriodicBoudariesLabel.setObjectName("enableYPeriodicBoudariesLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.enableYPeriodicBoudariesLabel)
        self.enableYPeriodicBoudariesCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.enableYPeriodicBoudariesCheckBox.setObjectName("enableYPeriodicBoudariesCheckBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.enableYPeriodicBoudariesCheckBox)
        self.gridLayout_3.addLayout(self.formLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.enableXPeriodicBoudariesLabel.setBuddy(self.enableXPeriodicBoudariesCheckBox)
        self.enableYPeriodicBoudariesLabel.setBuddy(self.enableYPeriodicBoudariesCheckBox)

        self.retranslateUi(EditModel)
        QtCore.QMetaObject.connectSlotsByName(EditModel)

    def retranslateUi(self, EditModel):
        _translate = QtCore.QCoreApplication.translate
        EditModel.setWindowTitle(_translate("EditModel", "Edit Model"))
        self.groupBox.setTitle(_translate("EditModel", "Spatial configuration"))
        self.enableXPeriodicBoudariesLabel.setText(_translate("EditModel", "Enable X periodic boudaries"))
        self.enableYPeriodicBoudariesLabel.setText(_translate("EditModel", "Enable Y periodic boudaries"))

