from PyQt5.QtWidgets import QWidget

from .qt.edit_model import Ui_EditModel

class EditModelDialog(QWidget):

    def __init__(self, parent_window=None):
        super().__init__()
        self.ui = Ui_EditModel()
        self.ui.setupUi(self)

        self.parent_window = parent_window