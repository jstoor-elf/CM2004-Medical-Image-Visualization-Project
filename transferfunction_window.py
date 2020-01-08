import sys
import time

import numpy as np

import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 6})

from matplotlib.figure import Figure
from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvas

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from Utilities import Settings

from slider import QRangeSlider
import pyqtgraph as pg
import bisect

from Utilities import Settings

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, parent, op_pts, X, Y, cmap_name):
        super().__init__(parent)

        self.setObjectName('Main Histogram window')

        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        fig = Figure(dpi=100)
        static_canvas = FigureCanvas(fig)
        layout.addWidget(AdjustingWidget(self, cmap_name))
        layout.addWidget(static_canvas)

        g = Graph(self)
        pos = np.column_stack((op_pts[0], op_pts[1]))
        g.setData(pos=pos, size=10, pxMode=True)

        plot_item = pg.PlotWidget()
        layout.addWidget(plot_item)
        plot_item.addItem(g)

        self.addPoints = False
        self.range = (X[0], X[-1])
        self._static_ax = static_canvas.figure.subplots()
        self._static_ax.plot(X[100:], Y[100:], "-")
        self._static_ax.set_title('Histogram (HU)', fontdict={'fontsize': 9})
        self._static_ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        self._static_ax.tick_params(axis="x", labelsize=6)
        self._static_ax.tick_params(axis="y", labelsize=6)

    def set_volume_sliders(self, volume_range):

        grey_scale_widget = self.findChild(QtWidgets.QFrame, 'Slider Widget')

        grey_scale_widget.slid_1.slider.setMin(int(self.range[0]))
        grey_scale_widget.slid_1.slider.setMax(int(self.range[1]))
        grey_scale_widget.slid_1.slider.setStart(int(volume_range[0]))
        grey_scale_widget.slid_1.slider.setEnd(int(volume_range[1]))


    def set_slice_sliders(self, slice_range, slice_value_range):

        grey_scale_widget = self.findChild(QtWidgets.QFrame, 'Slider Widget')

        grey_scale_widget.slid_2.slider.setMin(int(self.range[0]))
        grey_scale_widget.slid_2.slider.setMax(int(self.range[1]))
        grey_scale_widget.slid_2.slider.setStart(int(slice_range[0]))
        grey_scale_widget.slid_2.slider.setEnd(int(slice_range[1]))

        grey_scale_widget.slid_3.slider.setMin(0)
        grey_scale_widget.slid_3.slider.setMax(100)
        grey_scale_widget.slid_3.slider.setStart(int(100 * slice_value_range[0]))
        grey_scale_widget.slid_3.slider.setEnd(int(100 * slice_value_range[1]))


        self.setMinimumSize(400, 600)
        self.setMaximumSize(400, 600)


class AdjustingWidget(QtWidgets.QFrame):

    def __init__(self, parent, cmap):
        super().__init__(parent)

        self.setObjectName('Slider Widget')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.settigs3D = Settings3DWindow('3D_Int', '3D: Visualization Window', cmap, parent=self)
        self.slid_2 = MyRangeSlider('2D_Int', '2D: Image Intensity Range', parent=self)
        self.slid_3 = MyRangeSlider('2D_Val', '2D: Image Value Range', parent=self)

        self.layout.addWidget(self.slid_2)
        self.layout.addWidget(self.slid_3)
        self.layout.addWidget(self.settigs3D)

        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)



class MyRangeSlider(QtWidgets.QFrame):

    def __init__(self, name, label, parent=None):
        super().__init__(parent)

        self.setObjectName(name)

        if self.objectName() == '3D_Int':
             self.b = QtWidgets.QCheckBox("Add opacity point?", self)
             self.b.stateChanged.connect(self.clickBox)


        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(label)
        self.label.setStyleSheet("QLabel { font-size: 10px; }")
        self.slider = QRangeSlider(self)
        self.slider.setCallback(self.get_range)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.slider)

        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)

    def getVisualizationWindow(self):
        mCW = self.parentWidget().parentWidget().parentWidget().parentWidget()
        return mCW.findChild(QtWidgets.QFrame, "visualization Frame")


    def get_range(self, interval):
        vis_win = self.getVisualizationWindow()

        if self.objectName() == '3D_Int':
            vis_win.set_volume_lookup(interval)
        else:
            vis_win.set_slice_look_up(self.objectName(), interval)


    def clickBox(self, state):
        mCW = self.parentWidget().parentWidget().parentWidget()
        mCW.addPoints = state == QtCore.Qt.Checked


class Settings3DWindow(QtWidgets.QFrame):

    def __init__(self, name, label, cmap, parent=None):
        super().__init__(parent)

        self.setObjectName(name)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignLeft)
        self.label = QtWidgets.QLabel(label)
        self.label.setStyleSheet("QLabel { font-size: 10px; }")

        self.b = QtWidgets.QCheckBox("Add opacity point: ", self)
        self.b.stateChanged.connect(self.clickBox)
        self.b.setLayoutDirection(Qt.RightToLeft)

        nF = QtWidgets.QFrame()
        layout1 = QtWidgets.QHBoxLayout(nF)
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.setAlignment(Qt.AlignLeft)
        layout1.addWidget(self.b)
        layout1.addWidget(self.setup_cmap_frame(cmap))

        self.layout.addWidget(self.label)
        self.layout.addWidget(nF)

        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)


    def getVisualizationWindow(self):
        mCW = self.parentWidget().parentWidget().parentWidget().parentWidget()
        return mCW.findChild(QtWidgets.QFrame, "visualization Frame")


    def clickBox(self, state):
        mCW = self.parentWidget().parentWidget().parentWidget()
        mCW.addPoints = state == QtCore.Qt.Checked


    def cmap_selectionchange(self):
        mCW = self.getVisualizationWindow()
        mCW.change_cmap(self.type_combobox.currentText())


    def setup_cmap_frame(self, cmap):
        nF = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout(nF)
        layout.setContentsMargins(5, 0, 5, 0)

        label = QtWidgets.QLabel('cmap: ')
        layout.addWidget(label)

        # Type dropdown list, training or test images
        self.type_combobox = QtWidgets.QComboBox()
        for colormap in sorted(Settings.colormaps):
            self.type_combobox.addItem(colormap)
        self.type_combobox.currentIndexChanged.connect(self.cmap_selectionchange)
        self.type_combobox.setCurrentText(cmap)
        layout.addWidget(self.type_combobox)

        return nF



class Graph(pg.GraphItem):
    def __init__(self, parent):
        self.parent = parent
        self.dragPoint = None
        self.dragOffset = None
        pg.GraphItem.__init__(self)


    def setData(self, **kwds):
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['adj'] = np.column_stack((np.arange(0, npts-1), np.arange(1, npts)))
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)

        self.updateGraph()


    def addData(self, lX, lY):

        self.data['pos'] = np.asarray([lX, lY]).T

        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['adj'] = np.column_stack((np.arange(0, npts-1), np.arange(1, npts)))
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)

        self.updateGraph()


    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)


    def mouseClickEvent(self, ev):

        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return

        if self.parent.addPoints:
            position = ev.pos()

            # Find the position where to insert the new element
            newX = int(position.x())
            posX = bisect.bisect(self.data['pos'][:,0], newX)
            lX = list(self.data['pos'][:,0])
            lY = list(self.data['pos'][:,1])
            dy = lY[posX-1] + (((lY[posX] - lY[posX-1]) * (newX - lX[posX-1])) / (lX[posX] - lX[posX-1]))
            lX.insert(posX, newX)
            lY.insert(posX, dy)
            self.addData(lX, lY)

            ev.accept() # Accept event


    def mouseDragEvent(self, ev):

        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return

        if ev.isStart():
            pos = ev.buttonDownPos()
            pts = self.scatter.pointsAt(pos)
            if len(pts) == 0:
                ev.ignore()
                return
            self.dragPoint = pts[0]
            ind = pts[0].data()[0]
            self.dragOffset = self.data['pos'][ind][1] - pos[1]
        elif ev.isFinish():
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                ev.ignore()
                return

        ind = self.dragPoint.data()[0]
        self.data['pos'][ind][1] = ev.pos()[1] + self.dragOffset
        self.updateGraph()
        ev.accept()

        # Sedn range to update the volumetric rendition
        self.send_range(self.data['pos'])


    def send_range(self, pos):

        mCW = self.parent.parentWidget().parentWidget()
        vis_win = mCW.findChild(QtWidgets.QFrame, "visualization Frame")
        vis_win.set_volume_opacity(list(pos[:,0]), list(pos[:,1]))

        #vis_win = self.getVisualizationWindow()

        #if self.objectName() == '3D_Int':
        #    vis_win.set_volume_lookup(interval)
        #else:
        #    vis_win.set_slice_look_up(self.objectName(), interval)
