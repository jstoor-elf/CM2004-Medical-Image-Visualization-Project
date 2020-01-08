import Utilities.datareader as dr
from Utilities import Settings

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFrame, QLabel, QCheckBox, QMenu, QAction, QPushButton
from PyQt5.QtWidgets import QWidget, QPushButton, QButtonGroup, QScrollArea
from PyQt5.QtWidgets import QFormLayout, QGroupBox, QListWidgetItem, QListWidget
from PyQt5.QtWidgets import QStyleOptionViewItem, QStyledItemDelegate
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QSize

from transferfunction_window import ApplicationWindow

import os

class MainBox(QFrame):

    def __init__(self, parent):
        super(MainBox, self).__init__(parent)

        # Vertical view is used to store the different tool windows
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)

        # Set the setLayout, and the min width and height of this QFrame instance
        self.setLayout(self.layout)
        self.setFixedWidth(Settings.menu_window_width)
        self.setObjectName("Menu frame")


        # Add the tool window for a new image
        toolbox_label = QLabel('Vis-DNN Toolbox')
        toolbox_label.setAlignment(Qt.AlignCenter)
        toolbox_label.setStyleSheet(Settings.header_font)
        self.layout.addWidget(toolbox_label)

        # Add the widget where the image is chosen
        self.layout.addWidget(ImageButton(self))
        self.layout.addWidget(SegmentationMenu(self))
        self.layout.addWidget(PointMenu(self))
        self.activateButtons(enable=False)

        # Set the color of the menu box
        self.setStyleSheet(Settings.vis_style_menu)


    def get_visualization_widget(self):
        return self.parentWidget().findChild(QFrame, "visualization Frame")


    def activateButtons(self, enable=True):
        segm_menu = self.findChild(QFrame, "Segmentation Menu Window")
        segm_menu.findChild(QWidget, "Key Press Button").setEnabled(enable)
        segm_menu.findChild(QtWidgets.QComboBox, "Label Choosing").setEnabled(enable)
        segm_menu.findChild(QPushButton, "Slice View").setEnabled(enable)
        segm_menu.findChild(QPushButton, "Active Masks").setEnabled(enable)
        segm_menu.findChild(QPushButton, "3D View").setEnabled(enable)

        point_menu = self.findChild(QFrame, 'Point Menu')
        point_menu.listWidget.setEnabled(enable)
        point_menu.presstype.setEnabled(enable)


class ImageButton(QFrame):
    def __init__(self, parent):
        super(ImageButton, self).__init__(parent)

        self.previous_text = "None"

        label = QLabel('Input Image')
        label.setStyleSheet(Settings.menu_font)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Type dropdown list, training or test images
        self.type_combobox = QtWidgets.QComboBox()
        self.type_combobox.addItem('Train')
        self.type_combobox.addItem('Test')
        self.type_combobox.setCurrentText('Train')
        self.type_combobox.currentIndexChanged.connect(self.type_selectionchange)


        # Create the dropdown list of items to select from
        self.combobox = QtWidgets.QComboBox()
        self.update_im_combobox()
        self.combobox.currentIndexChanged.connect(self.image_selectionchange)


        # Put the the label and the combo box in the vbox
        self.layout.addWidget(label)
        self.layout.addWidget(self.type_combobox)
        self.layout.addWidget(self.combobox)

        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("Image tool window frame")


    def type_selectionchange(self):

        if self.type_combobox.currentText() == 'Train':
            Settings.current_path = Settings.im_train_path
        else:
            Settings.current_path = Settings.im_test_path

        # Clear vis. window
        visualization_window = self.parentWidget().get_visualization_widget()
        visualization_window.reset_vtk_renderer()

        self.combobox.clear()
        self.update_im_combobox()


    def update_im_combobox(self):

        self.previous_text = 'None'
        self.combobox.addItem(self.previous_text)

        # Fetch the visualization window

        if self.type_combobox.currentText() == 'Train':
            path = Settings.im_train_path
        else:
            path = Settings.im_test_path

        for im_names in dr.stripped_im_names(dr.get_im_names(path)):
            self.combobox.addItem(im_names)

        self.combobox.setCurrentText(self.previous_text)


    def image_selectionchange(self):

        # Fetch the visualization window
        visualization_window = self.parentWidget().get_visualization_widget()

        # Set the new text
        new_text = self.combobox.currentText()

        # Update visulizaiton window
        if self.combobox.currentText() == '':
            return
        elif self.combobox.currentText() == 'None' and new_text is not 'None':
            visualization_window.reset_vtk_renderer()
        else:
            if new_text == 'None':
                return

            visualization_window.set_source(new_text, \
                self.type_combobox.currentText(), im_type='image')
            if self.type_combobox.currentText() == 'Train':
                visualization_window.set_source(new_text, \
                    self.type_combobox.currentText(), im_type='gt')
            visualization_window.setup_vtk_renderer()

        self.previous_text = new_text


class SegmentationMenu(QFrame):

    def __init__(self, parent):
        super(SegmentationMenu, self).__init__(parent)

        # QWidget Label at the top
        label = QLabel('View Toolbox')
        label.setStyleSheet(Settings.menu_font)

        # Menus for segmentation activation and representation in slice view
        slice_btn = PushButton(self, "Slice View", ["Show Slices", "Boundary overlay", "Mask Overlay"])
        segm_btn = PushButton(self, "Active Masks", ["Ground Truth", "DNN-Segmentation"])
        rend_btn = PushButton(self, "3D View", ["Volumetric", "Surface", "Coordinates", "All Organs", "Stereo"])

        self.combobox = QtWidgets.QComboBox()
        self.combobox.setObjectName("Label Choosing")
        pix_map = QPixmap(12, 12)
        pix_map.fill(QColor(0,0,0))
        self.combobox.addItem(QIcon(pix_map), 'No active label')
        for organ in Settings.organs:
            pix_map = QPixmap(12, 12)
            pix_map.fill(QColor(*[255*c for c in Settings.labels[organ]['rgb']]))
            self.combobox.addItem(QIcon(pix_map), organ)
        self.combobox.currentIndexChanged.connect(self.label_selectionchange)


        titles = ['M', 'Z', 'C', 'P', 'D']
        presstype = QWidget()
        presstype.setObjectName("Key Press Button")
        l = QtWidgets.QHBoxLayout(presstype)
        l.setContentsMargins(0, 0, 0, 0)

        buttons = []
        path = Settings.view_icons['path']
        for tit, button_icon in enumerate(Settings.view_icons['menu_buttons']):
            icon = QIcon(path + Settings.view_icons['menu_buttons'][button_icon]['png'])
            button = QPushButton()
            button.setIcon(icon)
            button.setObjectName(titles[tit])
            buttons.append(button)

        self.button_group = QButtonGroup(l)
        self.button_group.setExclusive(True)
        for i, button in enumerate(buttons):
            l.addWidget(button)
            if i < len(buttons) - 1:
                self.button_group.addButton(button)
                self.button_group.setId(button, i+1)
                button.setCheckable(True)
            else:
                button.clicked.connect(self.histogram_button_signal)

        buttons[0].setChecked(True)
        self.button_group.buttonToggled.connect(self.on_button_signal)


        # Set layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(label)
        self.layout.addWidget(presstype)
        self.layout.addWidget(segm_btn)
        self.layout.addWidget(slice_btn)
        self.layout.addWidget(rend_btn)
        self.layout.addWidget(self.combobox)


        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("Segmentation Menu Window")

        # Turn off the segmentation functionality
        segm_btn.slice_menu.findChild(QAction, "DNN-Segmentation").setEnabled(False)
        segm_btn.slice_menu.findChild(QAction, "Ground Truth").setChecked(True)
        segm_btn.slice_menu.findChild(QAction, "Ground Truth").setEnabled(False)


    def on_button_signal(self):

        button = self.button_group.button(self.button_group.checkedId())
        visualization_window = self.parentWidget().get_visualization_widget()

        if button.objectName() == 'M':
            visualization_window.change_slice_event_type(0)
        elif button.objectName() == 'Z':
            visualization_window.change_slice_event_type(1)
        elif button.objectName() == 'C':
            visualization_window.change_slice_event_type(2)
        elif button.objectName() == 'P':
            visualization_window.change_slice_event_type(3)


    def histogram_button_signal(self):
        visualization_window = self.parentWidget().get_visualization_widget()
        values, counts = visualization_window.current_data.get_histogram()
        op_pts = visualization_window.render_list[-1].vis_object.get_opacity_pts()
        cmap_name = visualization_window.render_list[-1].vis_object.get_cmap()

        parent = self.parentWidget().parentWidget()
        hist = ApplicationWindow(parent, op_pts, values, counts, cmap_name)
        #hist.setFixedSize(hist.size())
        hist.show()

        # Set the volume slider range
        volume_range = visualization_window.get_volume_lookup()
        #hist.set_volume_sliders(volume_range)

        # Set the Slice sliders range
        slice_range, slice_value_range = visualization_window.get_slices_lookup()
        hist.set_slice_sliders(slice_range, slice_value_range)


    def label_selectionchange(self):

        view_3D = self.findChild(QPushButton, "3D View")
        all_organs = view_3D.slice_menu.findChild(QAction, "All Organs")

        if not all_organs.isChecked():
            organ = self.combobox.currentText()
            visualization_window = self.parentWidget().get_visualization_widget()
            visualization_window.handle_surface_rendition(False, organ)



class PushButton(QPushButton):
    def __init__(self, parent, button_name, action_names):
        super(PushButton, self).__init__(button_name, parent=parent)

        self.setObjectName(button_name)

        # Menu for segmentation representation in slice view
        self.slice_menu = QMenu()
        for action_name in action_names:
            action = QAction(action_name, self.slice_menu)
            action.setObjectName(action_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, a=action_name: self.check_state(checked, a))
            action.setChecked(False)
            self.slice_menu.addAction(action)

        self.setMenu(self.slice_menu)


    def check_state(self, is_checked, action_name):
        # Fetch the visualization window
        visualization_window = self.parentWidget().parentWidget().get_visualization_widget()


        if action_name == "Show Slices":
            visualization_window.change_visualization_view(is_checked)
        elif action_name == "Mask Overlay":
            visualization_window.change_masks_for_renderer(is_checked, 'mask')
        elif action_name == "Boundary overlay":
            visualization_window.change_masks_for_renderer(is_checked, 'boundary')
        elif action_name == "Ground Truth":
            print(action_name, is_checked)
        elif action_name == "DNN-Segmentation":
            print(action_name, is_checked)
        elif action_name == "Coordinates":
            visualization_window.change_volume_renderer(is_checked, 'coordinates')
        elif action_name == "Volumetric":
            visualization_window.change_volume_renderer(is_checked, 'volumetric')
        elif action_name == "Surface":
            visualization_window.change_volume_renderer(is_checked, 'surface')
        elif action_name == "All Organs":
            organ = self.parentWidget().combobox.currentText()
            visualization_window.handle_surface_rendition(is_checked, organ)
        elif action_name == "Stereo":
            visualization_window.set_stereo(is_checked)



class PointMenu(QFrame):

    def __init__(self, parent):
        super(PointMenu, self).__init__(parent)

        # QWidget Label at the top
        label = QLabel('Point Tablett')
        label.setStyleSheet(Settings.menu_font)

        # Set the name of the point menu
        self.setObjectName('Point Menu')

        # List to store points
        self.listWidget = QListWidget()
        self.delegate = ItemDelegate()
        self.listWidget.setItemDelegate(self.delegate)
        self.init_point_buttons()

        # Set point layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(label)
        self.layout.addWidget(self.listWidget)
        self.layout.addWidget(self.presstype)


        # Set shape of this QWidget
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)


    def init_point_buttons(self):

        # Init QWidget
        self.presstype = QWidget()
        self.presstype.setObjectName("Point buttons")

        # Initialize the buttons
        left = self.init_button_collection(True, ['Remove', 'Remove all'])
        right = self.init_button_collection(False, ['Improve', 'Improve all'])

        l = QtWidgets.QHBoxLayout(self.presstype)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(left)
        l.addWidget(right)


    def init_button_collection(self, flag, names):

        presstype = QWidget()
        presstype.setObjectName("Remove buttons") if flag else presstype.setObjectName("Improve buttons")

        l = QtWidgets.QHBoxLayout(presstype)
        l.setContentsMargins(0, 0, 0, 0)
        l.setAlignment(Qt.AlignLeft) if flag else l.setAlignment(Qt.AlignRight)

        path = Settings.view_icons['path']
        action = 'delete' if flag else 'improve'
        for i, icon in enumerate(Settings.view_icons['point_buttons'][action]):
            icon = QIcon(path + Settings.view_icons['point_buttons'][action][icon])
            button = QPushButton()
            button.setIcon(icon)
            button.setMaximumSize(QSize(28, 28))
            button.clicked.connect(lambda state, id=names[i]: self.button_pressed(id))
            l.addWidget(button)

        return presstype


    def add_point(self, id, label, pos):
        self.listWidget.addItem(ListWidgetWithId(id, label, pos))


    def button_pressed(self, id):

        # Put points of relevance in list
        remove_points = []
        if id in ['Remove', 'Improve']:
            for index in range(self.listWidget.count()):
                if self.listWidget.item(index).checkState() == Qt.Checked:
                    remove_points.append(self.listWidget.item(index))
        elif id in ['Remove all', 'Improve all']:
            for index in range(self.listWidget.count()):
                remove_points.append(self.listWidget.item(index))


        if remove_points:

            visualization_window = self.parentWidget().get_visualization_widget()

            if id in ['Remove', 'Remove all']:
                for item in remove_points:
                    self.listWidget.takeItem(self.listWidget.row(item))
                visualization_window.remove_points(remove_points)
            elif id in ['Improve', 'Improve all']:
                print('Improve Points, nmbr: {}'.format(len(remove_points)))
                visualization_window.improve_segmentation(remove_points)



class ListWidgetWithId(QListWidgetItem):

    def __init__(self, id, label, pos):
        super(ListWidgetWithId, self).__init__()

        self.id = id
        self.label = label
        self.pos = pos

        pix_map = QPixmap(8, 8)
        pix_map.fill(QColor(*[255*c for c in Settings.labels[label]['rgb']]))
        qicon = QIcon(pix_map)

        self.setText("(X,Y,Z) = ({},{},{})".format(*pos))
        self.setCheckState(Qt.Unchecked)
        self.setFont(QFont("Segoe UI", 8))
        self.setIcon(qicon)



class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Right
        super(ItemDelegate, self).paint(painter, option, index)
