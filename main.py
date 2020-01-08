import vtk
import sys

from Utilities import Settings
import menu_window as mw
import visualization_window as vs

from PyQt5 import QtCore, QtGui, QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog, QPushButton
from PyQt5 import Qt


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Init graphical user interface window
        self.setup_ui()


    def setup_ui(self):
        self.resize(Settings.window_width, Settings.window_height)
        self.setObjectName("MainWindow")

        # central widget
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setObjectName("centralwidget")
        # self.centralwidget.setStyleSheet("QWidget { background-color: rgba(236, 236, 236, 255); }")

        # print(self.centralwidget.palette().color(self.centralwidget.backgroundRole()).getRgb())

        # horizontal layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontal layout")

        # the translate mechanism
        QtCore.QMetaObject.connectSlotsByName(self)
        self.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", \
            Settings.main_window_name))

        # Set up visualization window and menu box
        self.vis_window = vs.VisualizationWindow(self.centralwidget)
        self.menu_window = mw.MainBox(self.centralwidget)

        # Set the menu layout
        self.horizontalLayout.addWidget(self.vis_window)
        self.horizontalLayout.addWidget(self.menu_window)

        # Set minimum size of window
        self.setMinimumSize(Settings.min_window_width, Settings.min_window_height)




if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
