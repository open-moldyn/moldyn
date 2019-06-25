from PyQt5.QtWidgets import QWidget

from .qt.define_external_forces import Ui_ExternalForces


class EditModelDialog(QWidget):

    def __init__(self,*args):
        super().__init__(*args)
        self.ui = Ui_ExternalForces()
        self.ui.setupUi(self)


        self.show()