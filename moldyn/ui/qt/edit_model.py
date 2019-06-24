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
        EditModel.resize(435, 457)
        self.gridLayout = QtWidgets.QGridLayout(EditModel)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(EditModel)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.enableXPeriodicBoudariesLabel = QtWidgets.QLabel(EditModel)
        self.enableXPeriodicBoudariesLabel.setObjectName("enableXPeriodicBoudariesLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.enableXPeriodicBoudariesLabel)
        self.enableXPeriodicBoudariesCheckBox = QtWidgets.QCheckBox(EditModel)
        self.enableXPeriodicBoudariesCheckBox.setObjectName("enableXPeriodicBoudariesCheckBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.enableXPeriodicBoudariesCheckBox)
        self.enableYPeriodicBoudariesLabel = QtWidgets.QLabel(EditModel)
        self.enableYPeriodicBoudariesLabel.setObjectName("enableYPeriodicBoudariesLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.enableYPeriodicBoudariesLabel)
        self.enableYPeriodicBoudariesCheckBox = QtWidgets.QCheckBox(EditModel)
        self.enableYPeriodicBoudariesCheckBox.setObjectName("enableYPeriodicBoudariesCheckBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.enableYPeriodicBoudariesCheckBox)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)

        self.retranslateUi(EditModel)
        QtCore.QMetaObject.connectSlotsByName(EditModel)

    def retranslateUi(self, EditModel):
        _translate = QtCore.QCoreApplication.translate
        EditModel.setWindowTitle(_translate("EditModel", "Edit Model"))
        self.enableXPeriodicBoudariesLabel.setText(_translate("EditModel", "Enable X periodic boudaries"))
        self.enableYPeriodicBoudariesLabel.setText(_translate("EditModel", "Enable Y periodic boudaries"))

