import vtk

from PyQt5 import QtWidgets

from operator import itemgetter
import os, sys
sys.path.append(os.path.abspath(os.path.join('..', 'Utilities')))
from Utilities import Settings


class WindowCommunicator:

    def __init__(self, list_visualizers, input_manager):

        self.axial    = list_visualizers[0]
        self.sagittal = list_visualizers[1]
        self.coronal  = list_visualizers[2]
        self.volume   = list_visualizers[3]

        self.input_manager = input_manager


    def update_view(self, inter, orie, actions, action_type):

        # zoom factor, a function of the window size and the visualization window
        zoom = self.zoom_factor(orie)

        # Get deltas for horizontal and vertical movement
        dx, dy = self.get_delta(inter, zoom)

        if action_type == 'Slicing':

            # Perform the view update
            if orie == 'Axial':
                func = self.axial_view
            elif orie == 'Sagittal':
                func = self.sagittal_view
            elif orie == 'Coronal':
                func = self.coronal_view
            func(dx, dy, actions)

        elif action_type == 'Move':

            # Perform the view update
            vis = self.get_visualizer(orie)

            # Move visualization object
            pos = vis.vis_object.PositionMove(inter, dx, dy, orie)

            if actions['Move'] == 1:
                self.input_manager.translate_points(dx, dy, orie)


        elif action_type == 'Reset':

            # Reset all the views irrespective of the view, also the 3D coordinate system
            self.input_manager.restore_planes() # Restore the positions of the dots
            self.axial.vis_object.reset_origin(self.axial.get_interactor())
            self.sagittal.vis_object.reset_origin(self.sagittal.get_interactor())
            self.coronal.vis_object.reset_origin(self.coronal.get_interactor())
            self.volume.vis_object.coordinate_system.reset_lines()
            self.volume.get_interactor().Render()


        elif action_type == 'Color':

            # Get color label
            menu_window = self.axial.vis_object.vis_widget.parentWidget().findChild(QtWidgets.QFrame, "Menu frame")
            segm_menu_window = menu_window.findChild(QtWidgets.QFrame, "Segmentation Menu Window")
            label_win = segm_menu_window.findChild(QtWidgets.QComboBox, "Label Choosing")
            label = label_win.currentText()

            if not label == 'No active label':
                # Get visualizer type
                coordinates= self.check_and_create_sphere_position(inter, orie)

                if coordinates:
                    pos = self.get_all_coordinates(coordinates, orie)
                    self.add_sphere(pos, label, orie)



    def check_and_create_sphere_position(self, inter, orie):

        # Get zoom factor for window
        zoom = self.zoom_factor(orie)

        # Get the visualizer
        vis = self.get_visualizer(orie)

        # Get window size to move the center of the click position
        window_size = vis.vtkWidget.GetRenderWindow().GetSize()
        winFacX, winFacY = window_size[0] / 4, (window_size[1] / 4) + 2.5

        # Get global mouse click position
        clickPos = inter.GetEventPosition()

        # Create a picker to get the relative position of the click, i.e. rel. to the renderer
        picker = vtk.vtkPropPicker()
        moveX, moveY = clickPos[0] + winFacX, clickPos[1] + winFacY
        picker.PickProp(moveX, moveY, vis.vis_object.renderer)
        local_pos = picker.GetPickPosition()

        # Multiply picker by 2, i.e. the view is over the whole screen, not the plane view
        local_posX = 2 * local_pos[0] # Local position for x
        local_posY = 2 * local_pos[1]  # Local position for y


        if picker.GetPath():
            minX, maxX, minY, maxY, _, _ = picker.GetViewProp().GetBounds()
            b1, b2 = (maxX - minX) / 2, (maxY - minY) / 2
            if (-b1 <= local_posX <= b1) and (-b2 <= local_posY <= b2):
                # Here call a method that fetches the coordinate axis value of interest
                # i.e. the one that isn't used, set the correct values for local_posX,
                # local_posY, local_posZ: and use it to create a sphere

                # Current center of the image slice in 3D coordinates
                current_center  = vis.vis_object.image_actor.reslice.GetResliceAxesOrigin()

                # Return the offset of the visualizer, to translate the point
                original_center = vis.vis_object.image_actor.center

                centX =  original_center[0] - current_center[0]
                centY = -original_center[1] + current_center[1]
                centZ =  original_center[2] - current_center[2]

                if orie == 'Axial':
                    posX = centX - local_posX
                    posY = centY - local_posY
                    posZ = centZ
                elif orie == 'Sagittal':
                    posX = centX
                    posY = centY + local_posX
                    posZ = centZ + local_posY
                elif orie == 'Coronal':
                    posX = centX - local_posX
                    posY = centY
                    posZ = centZ + local_posY

                return (posX, posY, posZ)

        return None



    def get_all_coordinates(self, local, orie):

        bounds = self.volume.vis_object.volume_rendition.actor.GetBounds()

        volLocaX = ((bounds[0] + bounds[1]) / 2) - local[0]
        volLocaY = ((bounds[2] + bounds[3]) / 2) + local[1]
        volLocaZ = ((bounds[4] + bounds[5]) / 2) - local[2]


        return [(-local[0], -local[1],  local[2]),
                ( local[1],  local[2],  local[0]),
                (-local[0],  local[2],  local[1]),
                (volLocaX, volLocaY, volLocaZ)]


    def add_sphere(self, coordinates, label, orie):

        input_manager = self.input_manager

        plane_positions, translations = list(), list()
        signs = [-1, 1, -1]
        for i, vis in zip([2, 0, 1], [self.axial, self.sagittal, self.coronal]):
            current = vis.vis_object.image_actor.reslice.GetResliceAxesOrigin()
            initial = vis.vis_object.image_actor.center
            plane_positions.append(signs[i]*(current[i] - initial[i]))
            translations.append(vis.vis_object.image_actor.translation)

        pixel_pos = self.axial.vis_object.image_actor.get_pixel_coordinates(coordinates[3])
        points = input_manager.add_point(label, coordinates, plane_positions, translations, pixel_pos)

        #print("Id: {}\nLabel: {}".format(points.id, points.label))

        #for point in points.pos:
        #    print("\tX: {} Y: {} Z:{}".format(*point))

        self.axial.vis_object.renderer.AddActor(points.points2D[0].actor)
        self.sagittal.vis_object.renderer.AddActor(points.points2D[1].actor)
        self.coronal.vis_object.renderer.AddActor(points.points2D[2].actor)
        self.volume.vis_object.renderer.AddActor(points.point3D.actor)

        self.axial.vtkWidget.GetRenderWindow().Render()
        self.sagittal.vtkWidget.GetRenderWindow().Render()
        self.coronal.vtkWidget.GetRenderWindow().Render()
        self.volume.vtkWidget.GetRenderWindow().Render()

        # Add the point to the menu
        self.axial.vis_object.vis_widget.add_point_to_menu(points.id, \
                points.label, points.pixel_coordinates)



    def get_delta(self, inter, zoom):
        (lastX, lastY) = inter.GetLastEventPosition()
        (mouseX, mouseY) = inter.GetEventPosition()
        return zoom*(mouseX - lastX), zoom*(mouseY - lastY)


    def get_visualizer(self, orie):
        if orie == 'Axial':
            return self.axial
        elif orie == 'Sagittal':
            return self.sagittal
        elif orie == 'Coronal':
            return self.coronal


    def zoom_factor(self, orie):

        # Get correct visualizer
        vis = self.get_visualizer(orie)

        zoom = vis.vis_object.renderer.GetActiveCamera().GetParallelScale()
        window_size = vis.vtkWidget.GetRenderWindow().GetSize()
        index = window_size[1] < window_size[0]
        return zoom / (window_size[index] / 4)


    def  axial_view(self, dx, dy, actions):

        ''' AXIAL VIEW '''

        orie = 'Axial'

        if actions["Slicing"] == 1:
            dy *= -1 # Rotate around the z axis

            # Translate the line of for the picked intear
            self.axial.vis_object.coordinate_system.translate_line(dx, -dy, orie, False)
            self.axial.get_interactor().Render()

            # Translate coordinate axis of other slice views
            self.sagittal.vis_object.coordinate_system.lines[1].translate_line(0, dy)
            self.coronal.vis_object.coordinate_system.lines[1].translate_line(0, dx)

            # Slice through slice views
            self.sagittal.vis_object.SliceMove(-dx, self.sagittal.get_interactor())
            self.coronal.vis_object.SliceMove(dy, self.coronal.get_interactor())

            # Move point planes
            input_manager = self.input_manager
            input_manager.move_plane('Sagittal', dx)
            input_manager.move_plane('Coronal', -dy)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line(dx, dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view
        elif actions["Slicing"] == 2:

            self.sagittal.vis_object.coordinate_system.translate_line(0, dy, orie, False)
            self.coronal.vis_object.coordinate_system.translate_line(0, dy, orie, False)
            self.sagittal.get_interactor().Render()
            self.coronal.get_interactor().Render()

            self.axial.vis_object.SliceMove(-dy, self.axial.get_interactor())

            self.input_manager.move_plane('Axial', -dy)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line_depth(dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view



    def  sagittal_view(self, dx, dy, actions):

        ''' SAGITTAL VIEW '''

        orie = 'Sagittal'

        if actions["Slicing"] == 1:

            # Translate the line of for the picked intear
            self.sagittal.vis_object.coordinate_system.translate_line(dx, dy, orie, False)
            self.sagittal.get_interactor().Render()

            # Translate coordinate axis of other slice views
            self.axial.vis_object.coordinate_system.lines[0].translate_line(1, -dx)
            self.coronal.vis_object.coordinate_system.lines[0].translate_line(1, dy)

            # Slice through slice views
            self.axial.vis_object.SliceMove(-dy, self.axial.get_interactor())
            self.coronal.vis_object.SliceMove(dx, self.coronal.get_interactor())

            # Move point planes
            input_manager = self.input_manager
            input_manager.move_plane('Axial', -dy)
            input_manager.move_plane('Coronal', -dx)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line(dx, dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view

        elif actions["Slicing"] == 2:
            self.axial.vis_object.coordinate_system.translate_line(-dy, 0, orie, False)
            self.coronal.vis_object.coordinate_system.translate_line(-dy, 0, orie, False)
            self.axial.get_interactor().Render()
            self.coronal.get_interactor().Render()

            self.sagittal.vis_object.SliceMove(dy, self.sagittal.get_interactor())

            self.input_manager.move_plane('Sagittal', -dy)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line_depth(dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view



    def  coronal_view(self, dx, dy, actions):

        ''' CORONAL VIEW '''

        orie = 'Coronal'

        if actions["Slicing"] == 1:

            # Translate the line of for the picked intear
            self.coronal.vis_object.coordinate_system.translate_line(dx, dy, orie, False)
            self.coronal.get_interactor().Render()

            # Translate coordinate axis of other slice views
            self.axial.vis_object.coordinate_system.lines[1].translate_line(0, dx)
            self.sagittal.vis_object.coordinate_system.lines[0].translate_line(1, dy)

            # Slice through slice views
            self.axial.vis_object.SliceMove(-dy, self.axial.get_interactor())
            self.sagittal.vis_object.SliceMove(-dx, self.sagittal.get_interactor())

            # Move point planes
            input_manager = self.input_manager
            input_manager.move_plane('Axial', -dy)
            input_manager.move_plane('Sagittal', dx)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line(dx, dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view

        elif actions["Slicing"] == 2:

            self.axial.vis_object.coordinate_system.translate_line(0, -dy, orie, False)
            self.sagittal.vis_object.coordinate_system.translate_line(dy, 0, orie, False)
            self.axial.get_interactor().Render()
            self.sagittal.get_interactor().Render()

            self.coronal.vis_object.SliceMove(dy, self.coronal.get_interactor())

            self.input_manager.move_plane('Coronal', -dy)

            # Update 3D coordinate system
            self.volume.vis_object.coordinate_system.translate_line_depth(dy, orie)
            self.volume.get_interactor().Render() # Render the 3D view
