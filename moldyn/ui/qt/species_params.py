# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'species_params.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_species_params(object):
    def setupUi(self, species_params):
        species_params.setObjectName("species_params")
        species_params.resize(254, 187)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(species_params.sizePolicy().hasHeightForWidth())
        species_params.setSizePolicy(sizePolicy)
        species_params.setWindowTitle("species_params")
        self.formLayout_2 = QtWidgets.QFormLayout(species_params)
        self.formLayout_2.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.formLayout_2.setObjectName("formLayout_2")
        self.nameLabel = QtWidgets.QLabel(species_params)
        self.nameLabel.setObjectName("nameLabel")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.nameLabel)
        self.presetLabel = QtWidgets.QLabel(species_params)
        self.presetLabel.setObjectName("presetLabel")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.presetLabel)
        self.presetComboBox = QtWidgets.QComboBox(species_params)
        self.presetComboBox.setObjectName("presetComboBox")
        self.presetComboBox.addItem("")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.presetComboBox)
        self.massKgLabel = QtWidgets.QLabel(species_params)
        self.massKgLabel.setObjectName("massKgLabel")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.massKgLabel)
        self.epsilonJLabel = QtWidgets.QLabel(species_params)
        self.epsilonJLabel.setObjectName("epsilonJLabel")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.epsilonJLabel)
        self.sigmaMLineEdit = QtWidgets.QLineEdit(species_params)
        self.sigmaMLineEdit.setText("")
        self.sigmaMLineEdit.setObjectName("sigmaMLineEdit")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.sigmaMLineEdit)
        self.sigmaMLabel = QtWidgets.QLabel(species_params)
        self.sigmaMLabel.setObjectName("sigmaMLabel")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.sigmaMLabel)
        self.nameLineEdit = QtWidgets.QLineEdit(species_params)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.nameLineEdit)
        self.massKgLineEdit = QtWidgets.QLineEdit(species_params)
        self.massKgLineEdit.setText("")
        self.massKgLineEdit.setObjectName("massKgLineEdit")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.massKgLineEdit)
        self.epsilonJLineEdit = QtWidgets.QLineEdit(species_params)
        self.epsilonJLineEdit.setText("")
        self.epsilonJLineEdit.setObjectName("epsilonJLineEdit")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.epsilonJLineEdit)
        self.nameLabel.setBuddy(self.nameLineEdit)
        self.presetLabel.setBuddy(self.presetComboBox)
        self.massKgLabel.setBuddy(self.massKgLineEdit)
        self.epsilonJLabel.setBuddy(self.epsilonJLineEdit)
        self.sigmaMLabel.setBuddy(self.sigmaMLineEdit)

        self.retranslateUi(species_params)
        QtCore.QMetaObject.connectSlotsByName(species_params)
        species_params.setTabOrder(self.presetComboBox, self.nameLineEdit)
        species_params.setTabOrder(self.nameLineEdit, self.massKgLineEdit)
        species_params.setTabOrder(self.massKgLineEdit, self.sigmaMLineEdit)
        species_params.setTabOrder(self.sigmaMLineEdit, self.epsilonJLineEdit)

    def retranslateUi(self, species_params):
        _translate = QtCore.QCoreApplication.translate
        self.nameLabel.setText(_translate("species_params", "Name"))
        self.presetLabel.setText(_translate("species_params", "Preset"))
        self.presetComboBox.setItemText(0, _translate("species_params", "Choose..."))
        self.massKgLabel.setText(_translate("species_params", "Mass (kg)"))
        self.epsilonJLabel.setText(_translate("species_params", "Epsilon (J)"))
        self.sigmaMLabel.setText(_translate("species_params", "Sigma (m)"))

