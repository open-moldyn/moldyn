import sys
from PyQt5.QtWidgets import QApplication
from .mainwindow import MoldynMainWindow


def main():
    app = QApplication(sys.argv)

    window = MoldynMainWindow()
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()
