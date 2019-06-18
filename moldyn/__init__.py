from .utils import *
from .processing import *
from . import simulation


__all__ = ["processing", "simulation", "utils"]
__version = "0.0.1"

def gui():
    import sys
    from PyQt5.QtWidgets import QApplication
    from moldyn.ui.mainwindow import MoldynMainWindow

    app = QApplication(sys.argv)

    window = MoldynMainWindow()
    window.show()

    app.exec_()