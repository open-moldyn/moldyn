# -*-encoding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from moldyn.ui.mainwindow import MoldynMainWindow


def main():
    app = QApplication(sys.argv)

    window = MoldynMainWindow()
    window.show()

    app.exec_()


if __name__ == "__main__":
    main()
