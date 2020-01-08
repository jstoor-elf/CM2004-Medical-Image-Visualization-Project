import Utilities.datareader as dr
from Utilities import Settings
from Utilities.mask_improver import improve_segmentation
from Renderers.slice_renderer import SliceRenderer
from Renderers.volume_renderer import VolumeRenderer
from Renderers.window_communicator import WindowCommunicator
from Renderers.input_manager import InputManager
from data_object import ImageObject, MaskObject

import vtk

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFrame, QLabel, QAction
from PyQt5 import Qt

from vtk.util.numpy_support import vtk_to_numpy


class VisualizationWindow(QFrame):

    def __init__(self, parent):
        super(VisualizationWindow, self).__init__(parent)

        # Vertical view is used to store the different tool windows
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("visualization Frame")

        # Set Background color
        self.setStyleSheet(Settings.vis_style_single )

        # Set the source that the visualization is taken from
        self.current_data, self.current_gt, self.current_mask = None, None, None
        self.window_communicator, self.input_manager = None, None
        self.activated = False


    def set_source(self, im_name, class_type, im_type='image', init_border=True):
        # Im_type has to be activated first
        # Get path to source and change the attribute
        if im_type == 'image':
            self.current_data = ImageObject(im_name, class_type)
        elif im_type == 'gt':
            self.current_gt = MaskObject(im_name, init_border=init_border)
        elif im_type == 'as':
            self.current_mask = MaskObject(im_name, init_border=init_border)
        else:
            raise Exception("Incorrect image type: 'image', 'gt', \
                or 'mask' sould be given")


    def reset_vtk_renderer(self):

        if self.activated:
            # Reset the data
            self.current_data = None
            self.current_gt   = None
            self.current_mask = None
            self.window_communicator = None
            self.input_manager = None

            for ren in self.render_list:
                ren.vis_object.renderer.RemoveAllViewProps()
                ren.vis_object.renderer.ResetCamera()
                ren.vtkWidget.GetRenderWindow().Render()

            self.render_list = []
            self.setStyleSheet(Settings.vis_style_single )

            for i in reversed(range(self.grid_layout.count())):
                self.grid_layout.itemAt(i).widget().setParent(None)



    def setup_vtk_renderer(self):
        # Rendering interactor

        # Visualizations of type VisualizationWidget, see below
        self.render_list = list()
        self.render_list.append(VisualizationWidget(self, SliceRenderer(self, self.current_data, self.current_gt, orie='Axial')))
        self.render_list.append(VisualizationWidget(self, SliceRenderer(self, self.current_data, self.current_gt, orie='Sagittal')))
        self.render_list.append(VisualizationWidget(self, SliceRenderer(self, self.current_data, self.current_gt, orie='Coronal')))
        self.render_list.append(VisualizationWidget(self, VolumeRenderer(self, self.current_data, self.current_gt)))

        # Requesting a StereoCapableWindowOn for volume
        self.render_list[-1].prep_stereo()


        verts = self.render_list[-1].vis_object.surface_rendition.get_vertecies()

        # Setup the communicator to synchronize windows
        self.window_communicator = WindowCommunicator(self.render_list, InputManager())


        # Grid layout and add window interactors
        if not self.activated:
            self.grid_layout = Qt.QGridLayout()

        pos = [(0,0), (0,1), (1,0), (1,1)]
        for inter, p in zip(self.render_list, pos):
            self.grid_layout.addWidget(inter.vtkWidget, *p)

        if not self.activated:
            self.setLayout(self.grid_layout)


        for inter in self.render_list:
            # Change the AddObserver
            iren = inter.get_interactor()
            iren.RemoveObservers('MouseMoveEvent')
            iren.AddObserver('MouseMoveEvent', StyleCallback(inter.vis_object, iren), 1.)

            inter.vtkWidget.GetRenderWindow().Render()
            iren.Initialize()
            iren.Start()

        self.setStyleSheet(Settings.vis_style_multiple)


        ### FIX THE MENU WINDOW ###

        # Set the push button in the menu bar to "Show slices - checked"
        menu_window = self.parentWidget().findChild(QFrame, "Menu frame")
        menu_window.activateButtons(enable=True) # Activate segmentation menu

        # Set show slices to true
        segm_menu_window = menu_window.findChild(QFrame, "Segmentation Menu Window")
        push_button = segm_menu_window.findChild(QtWidgets.QPushButton, "Slice View")
        push_button.slice_menu.findChild(QAction, "Show Slices").setChecked(True)

        push_button = segm_menu_window.findChild(QtWidgets.QPushButton, "3D View")
        #push_button.slice_menu.findChild(QAction, "Volumetric").setChecked(True)
        push_button.slice_menu.findChild(QAction, "Surface").setChecked(True)
        push_button.slice_menu.findChild(QAction, "Coordinates").setChecked(True)
        push_button.slice_menu.findChild(QAction, "All Organs").setChecked(True)

        # Activated slices
        self.activated = True


    def change_masks_for_renderer(self, is_checked, overlay_type):

        if len(self.render_list) == 4:
            for i in range(len(self.render_list)-1):
                self.render_list[i].change_masks(is_checked, overlay_type)
                self.render_list[i].vtkWidget.GetRenderWindow().Render()


    def change_visualization_view(self, is_checked):

        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        pos = [(0,0), (0,1), (1,0), (1,1)]
        if is_checked:
            self.setStyleSheet(Settings.vis_style_multiple)
            for inter, p in zip(self.render_list, pos):
                self.grid_layout.addWidget(inter.vtkWidget, *p)
        else:
            self.setStyleSheet(Settings.vis_style_single)
            self.grid_layout.addWidget(self.render_list[-1].vtkWidget, *pos[0])


    def change_slice_event_type(self, bool):
        if len(self.render_list) == 4:
            for i in range(len(self.render_list)-1):
                self.render_list[i].set_slice_setting(bool)


    def change_volume_renderer(self, is_checked, actor_type):
        self.render_list[len(self.render_list) - 1].vis_object.change_actor(\
                is_checked, actor_type)
        self.render_list[len(self.render_list) - 1].get_interactor().Render()


    def add_point_to_menu(self, id, label, pos):
        # Set the push button in the menu bar to "Show slices - checked"
        menu_window = self.parentWidget().findChild(QFrame, "Menu frame")

        # Set show slices to true
        point_window = menu_window.findChild(QFrame, 'Point Menu')
        point_window.add_point(id, label, pos)


    def remove_points(self, remove_points):
        if self.window_communicator:
            self.window_communicator.input_manager.remove_points(remove_points, self.render_list)

            for ren in self.render_list:
                ren.vtkWidget.GetRenderWindow().Render()


    def improve_segmentation(self, points):
        border, mask = improve_segmentation(self.current_gt, points)
        self.current_gt.renew_border_mask(border) # Update border
        self.current_gt.improved = self.current_gt.numpy_to_vtkimg(mask)

        for i, ren in enumerate(self.render_list[:-1]):
            ren.vis_object.update_masks(self.current_gt)
            ren.vtkWidget.GetRenderWindow().Render()

        self.render_list[-1].vis_object.update_masks(self.current_gt.improved)
        self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def handle_surface_rendition(self, is_checked, organ):
        if is_checked or organ == 'No active label':
            self.reset_organs()
        else:
            self.single_out_organ(organ)


    def single_out_organ(self, organ):
        surface_rend = self.render_list[-1].vis_object.surface_rendition

        if surface_rend:
            surface_rend.single_out_organ(organ)
            self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def reset_organs(self):
        surface_rend = self.render_list[-1].vis_object.surface_rendition

        if surface_rend:
            surface_rend.reset_organs()
            self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def get_slices_lookup(self):
        return self.render_list[0].vis_object.image_actor.get_look_up()


    def get_volume_lookup(self):
        return self.render_list[-1].vis_object.get_look_up()


    def set_slice_look_up(self, r_type, interval):

        if r_type == '2D_Int':
            for render in self.render_list[:-1]:
                render.vis_object.image_actor.set_intensity_range(interval)
                render.vtkWidget.GetRenderWindow().Render()
        elif r_type == '2D_Val':
            interval = (interval[0] / 100, interval[1] / 100)
            for render in self.render_list[:-1]:
                render.vis_object.image_actor.set_value_range(interval)
                render.vtkWidget.GetRenderWindow().Render()


    def set_volume_lookup(self, interval):
        self.render_list[-1].vis_object.set_volume_lookup(interval)
        self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def set_volume_opacity(self, x, y):
        self.render_list[-1].vis_object.set_opacity_pts(x, y)
        self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def change_cmap(self, name):
        self.render_list[-1].vis_object.change_cmap(name)
        self.render_list[-1].vtkWidget.GetRenderWindow().Render()


    def set_stereo(self, flag):
        self.render_list[-1].set_stereo(flag)


class VisualizationWidget(QFrame):

    def __init__(self, parent, vis_object):
        super(VisualizationWidget, self).__init__(parent)

        self.vis_object = vis_object
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.vis_object.renderer)


    def get_interactor(self):
        return self.vtkWidget.GetRenderWindow().GetInteractor()


    def change_masks(self, is_checked, overlay_type):
        self.vis_object.change_mask_layer(is_checked, overlay_type)


    def set_slice_setting(self, index):
        self.vis_object.set_action_type(index)


    def prep_stereo(self):
        ren_win = self.vtkWidget.GetRenderWindow()
        ren_win.GetStereoCapableWindow()
        ren_win.StereoCapableWindowOn()


    def set_stereo(self, flag):

        ren_win = self.vtkWidget.GetRenderWindow()
        if flag:
            ren_win.SetStereoRender(1)
            ren_win.SetStereoTypeToAnaglyph()
        else:
            ren_win.SetStereoRender(0)
        ren_win.GetInteractor().Render()





class StyleCallback:
    def __init__(self, ren, interactor):
        self.interactor = interactor
        self.rendition = ren

    def __call__(self, obj, ev):
        # _x, _y = obj.GetEventPosition()
        # render_ref = obj.FindPokedRenderer(_x, _y)
        self.interactor.SetInteractorStyle(self.rendition.inter_style)
