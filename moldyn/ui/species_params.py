from PyQt5.QtWidgets import QWidget
from qt.species_params import Ui_species_params

class species_params(QWidget):
    def __init__(self,*args):
        super().__init__(*args)
        self.ui = Ui_species_params()
        self.ui.setupUi(self)
        self.show()