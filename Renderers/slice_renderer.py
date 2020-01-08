
from Utilities import Settings
from .coordinate_system import CoordinateSystem2D

import vtk


class SliceRenderer:

    def __init__(self, parent_vis, im_data, gt_data=None, orie='Sagittal', border=True, between=True):

        # Reference to vislization
        self.vis_widget = parent_vis

        # orie
        self.orie = orie

        # Store the coordinate system for future reference
        self.coordinate_system = CoordinateSystem2D(im_data.im_src, self.orie)

        # Image actor
        self.image_actor = ImageSliceActor(im_data, self.orie)
        self.mask_actor, self.border_actor = None, None

        # Text actor
        self.text_for_actor = "{}: {}/{}"
        self.textActor = vtk.vtkTextActor()
        self.set_text(self.image_actor.reslice.GetResliceAxes().MultiplyPoint((0, 0, 0, 1)))
        self.textActor.SetPosition(*Settings.vis_text_info['position'])
        self.textActor.GetTextProperty().SetFontSize(Settings.vis_text_info['size'])
        self.textActor.GetTextProperty().SetColor(*Settings.vis_text_info['color'])

        # Renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.image_actor.actor)
        self.renderer.AddActor(self.textActor)
        for line in self.coordinate_system.lines:
            self.renderer.AddActor(line.actor)


        if gt_data:
            self.border_actor = MaskSliceActor(gt_data.border_src,\
                self.image_actor.get_orie_mat(), opacity=1.)
            self.mask_actor = MaskSliceActor(gt_data.mask_src.GetOutput(), \
                self.image_actor.get_orie_mat(), opacity=.1)


        # Create callbacks for slicing the image
        self.actions = {}
        self.actions["Slicing"] = 0
        self.actions["Move"] = 0
        self.actions["Reset"] = 0
        self.actions["Color"] = 0
        self.action_type = 'Slicing'

        # Set up the interaction
        self.inter_style = vtk.vtkInteractorStyleImage()
        self.inter_style.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.inter_style.AddObserver("LeftButtonPressEvent", self.ButtonCallback)
        self.inter_style.AddObserver("LeftButtonReleaseEvent", self.ButtonCallback)
        self.inter_style.AddObserver("RightButtonPressEvent", self.ButtonCallback)
        self.inter_style.AddObserver("RightButtonReleaseEvent", self.ButtonCallback)


        # Zoom objects
        self.renderer.ResetCamera()
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        self.renderer.GetActiveCamera().Zoom(1.40)
        self.init_parallel_scale = self.renderer.GetActiveCamera().GetParallelScale()



    def MouseMoveCallback(self, obj, event):
        if self.action_type in ['Slicing', 'Move']:
            self.vis_widget.window_communicator.update_view(obj.GetInteractor(), self.orie, \
                    self.actions, self.action_type)


    def set_action_type(self, a_type):
        #self.image_actor.coordinate_length(0)
        action_types = ['Slicing', 'Move', 'Reset', 'Color']
        self.action_type = action_types[a_type]


    def ButtonCallback(self, obj, event):
        inter = obj.GetInteractor()

        if self.action_type in ['Slicing', 'Move']:
            if event == "LeftButtonPressEvent":
                self.actions[self.action_type] = 1
            elif event == "RightButtonPressEvent":
                self.actions[self.action_type] = 2
            else:
                self.actions[self.action_type] = 0
        elif self.action_type == 'Reset':
            if event == "LeftButtonPressEvent":
                self.vis_widget.window_communicator.update_view(inter, self.orie, self.actions, \
                    self.action_type)
        elif self.action_type == 'Color':
            if event == "LeftButtonPressEvent":
                self.vis_widget.window_communicator.update_view(inter, self.orie, self.actions, \
                    self.action_type)


    def SliceMove(self, delta, inter):

        self.image_actor.reslice.Update()
        matrix = self.image_actor.reslice.GetResliceAxes()
        center = matrix.MultiplyPoint((0, 0, delta, 1))

        for i, actor in enumerate([True, self.border_actor, self.mask_actor]):
            if actor is not None:
                if i > 0:
                    matrix = actor.reslice.GetResliceAxes()
                matrix.SetElement(0, 3, center[0])
                matrix.SetElement(1, 3, center[1])
                matrix.SetElement(2, 3, center[2])

        self.set_text(center)
        inter.GetRenderWindow().Render() # render window


    def PositionMove(self, inter, deltaX, deltaY, orie):

        center = self.image_actor.center

        if self.actions["Move"] == 1:

            reslice_origin = self.image_actor.reslice.GetResliceAxesOrigin()
            s = 1 if orie == 'Axial' else -1
            pos = self.new_origin(reslice_origin, -deltaX, s * deltaY, 0)

            actors = [self.image_actor, self.border_actor, self.mask_actor]
            for actor in actors:
                if actor is not None:
                    actor.reslice.Update()
                    actor.reslice.SetResliceAxesOrigin(*pos)

            # Update coordinate system
            self.coordinate_system.translate_line(deltaX, deltaY, self.orie)

            # Render window
            inter.GetRenderWindow().Render()

            # Translate origin
            self.image_actor.translate(deltaX, deltaY)

        if self.actions['Move'] == 2:
            current = self.renderer.GetActiveCamera().GetParallelScale()
            self.renderer.GetActiveCamera().SetParallelScale(current+deltaY)
            inter.GetRenderWindow().Render()


    def reset_origin(self, inter):
        # Update translation of image actor
        self.image_actor.reset_translation()

        self.image_actor.reslice.Update()
        center = self.image_actor.center
        self.coordinate_system.reset_lines()

        actors = [self.image_actor, self.border_actor, self.mask_actor]
        for actor in actors:
            if actor is not None:
                actor.reslice.SetResliceAxesOrigin(*center)

        self.renderer.GetActiveCamera().SetParallelScale(self.init_parallel_scale)
        inter.GetRenderWindow().Render()



    def new_origin(self, origin, dx, dy, dz):

        changes = [[dx, dy, dz], [dz, dx, -dy], [dx, dz, -dy]]

        if self.image_actor.orie == 'Axial':
            change = changes[0]
        elif self.image_actor.orie == 'Sagittal':
            change = changes[1]
        elif self.image_actor.orie == 'Coronal':
            change = changes[2]

        return [x + y for x, y in zip(origin, change)]


    def test_new_point_Z(self, obj):

        inter = obj.GetInteractor()
        (lastX, lastY) = inter.GetLastEventPosition()
        (mouseX, mouseY) = inter.GetEventPosition()
        dx, dy = mouseX - lastX, mouseY - lastY

        self.image_actor.reslice.Update()
        sliceSpacing = self.image_actor.reslice.GetOutput().GetSpacing()[2]
        matrix = self.image_actor.reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, 1*delta, 1))


        if self.orie == 'Axial':
            return 0 <= center[2] <= self.image_actor.slices[5]
        elif self.orie == 'Coronal':
            return 0 <= center[1] <= self.image_actor.slices[3]
        elif self.orie == 'Sagittal':
            return 0 <= center[0] <= self.image_actor.slices[1]


    def set_text(self, center):

        fac = self.image_actor.spacing

        if self.orie == 'Axial':
            nominator = round((1./fac[2])*center[2]) # round((1./fac[2])*self.image_actor.slices[5])
            denominator = round((1./fac[2])*self.image_actor.slices[5])
            self.textActor.SetInput(self.text_for_actor.format(self.orie, nominator, denominator))

        elif self.orie == 'Sagittal':
            nominator = round((1./fac[0])*center[0])
            denominator = round((1./fac[0])*self.image_actor.slices[1])
            self.textActor.SetInput(self.text_for_actor.format(self.orie, nominator, denominator))

        elif self.orie == 'Coronal':
            nominator = round((1./fac[1])*center[1])
            denominator = round((1./fac[1])*self.image_actor.slices[3])
            self.textActor.SetInput(self.text_for_actor.format(self.orie, nominator, denominator))


    def change_mask_layer(self, is_checked, overlay_type):

        if not is_checked:
            if overlay_type == 'mask':
                self.renderer.RemoveActor(self.mask_actor.actor)
            elif overlay_type == 'boundary':
                self.renderer.RemoveActor(self.border_actor.actor)
        else:
            if overlay_type == 'mask':
                self.renderer.AddActor(self.mask_actor.actor)
            elif overlay_type == 'boundary':
                self.renderer.AddActor(self.border_actor.actor)


    def update_masks(self, current_mask):
        self.border_actor.update_slice_image(current_mask.border_src)
        self.mask_actor.update_slice_image(current_mask.improved)



class ImageSliceActor():
    def __init__(self, im_data, orie='Sagittal'):

        # orie
        self.orie = orie

        source = im_data.im_src

        self.translation = [0, 0]

        # (xMin, xMax, yMin, yMax, zMin, zMax)
        self.sizes = source.GetExecutive().GetWholeExtent(source.GetOutputInformation(0))
        self.spacing = source.GetOutput().GetSpacing()
        self.origin = source.GetOutput().GetOrigin()

        # include (xSpacing, ySpacing, zSpacing) to get the correct slices

        self.center = [self.origin[0] + self.spacing[0] * 0.5 * (self.sizes[0] + self.sizes[1]),
                       self.origin[1] + self.spacing[1] * 0.5 * (self.sizes[2] + self.sizes[3]),
                       self.origin[2] + self.spacing[2] * 0.5 * (self.sizes[4] + self.sizes[5])]


        self.slices = [self.center[0] - self.spacing[0] * 0.5 * (self.sizes[0] + self.sizes[1]),
                      self.center[0] + self.spacing[0] * 0.5 * (self.sizes[0] + self.sizes[1]),
                      self.center[1] - self.spacing[1] * 0.5 * (self.sizes[2] + self.sizes[3]),
                      self.center[1] + self.spacing[1] * 0.5 * (self.sizes[2] + self.sizes[3]),
                      self.center[2] - self.spacing[2] * 0.5 * (self.sizes[4] + self.sizes[5]),
                      self.center[2] + self.spacing[2] * 0.5 * (self.sizes[4] + self.sizes[5])]


        self.reslice = vtk.vtkImageReslice()
        self.reslice.SetInputConnection(source.GetOutputPort())
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetResliceAxes(self.get_orie_mat())
        self.reslice.SetInterpolationModeToLinear()

        # Create a greyscale lookup table
        self.table = vtk.vtkLookupTable()
        self.table.SetRange(0, 1500) # image intensity range
        self.table.SetValueRange(0.0, 0.7) # from black to white
        self.table.SetSaturationRange(0.0, 0.0) # no color saturation
        self.table.SetRampToLinear()
        self.table.Build()

        # Map the image through the lookup table
        self.color = vtk.vtkImageMapToColors()
        self.color.SetLookupTable(self.table)
        self.color.SetInputConnection(self.reslice.GetOutputPort())

        # Display the image
        self.actor = vtk.vtkImageActor()
        self.actor.GetMapper().SetInputConnection(self.color.GetOutputPort())


    def get_look_up(self):
        return self.table.GetRange(), self.table.GetValueRange()


    def set_intensity_range(self, interval):
        self.table.SetRange(*interval)
        self.table.Build()
        self.color.Update()


    def set_value_range(self, interval):
        self.table.SetValueRange(*interval)
        self.table.Build()
        self.color.Update()


    def get_orie_mat(self):
        trans_mat = vtk.vtkMatrix4x4()
        center = self.center

        if self.orie == 'Axial':
            trans_mat.DeepCopy((1, 0, 0, center[0],
                            0, -1, 0, center[1],
                            0, 0, 1, center[2],
                            0, 0, 0, 1))
        elif self.orie == 'Coronal':
            trans_mat.DeepCopy((1, 0, 0, center[0],
                              0, 0, 1, center[1],
                              0,-1, 0, center[2],
                              0, 0, 0, 1))
        elif self.orie == 'Sagittal':
            trans_mat.DeepCopy((0, 0,-1, center[0],
                               1, 0, 0, center[1],
                               0,-1, 0, center[2],
                               0, 0, 0, 1))
        else:
            print(self.orie)
            raise ValueError

        return trans_mat


    def test_range(self, min, max):
        return min >= 0 and min < max and max < 2000


    def get_max_sizes(self):
        maxX = self.origin[0] + (self.sizes[0] + self.sizes[1])
        maxY = self.origin[1] + (self.sizes[2] + self.sizes[3])
        maxZ = self.origin[2] + (self.sizes[4] + self.sizes[5])
        return (maxX, maxY, maxZ)


    def get_pixel_coordinates(self, coordinates_with_spacing):
        return [(self.origin[i] + coordinates_with_spacing[i] / self.spacing[i]) for i in range(3)]



    def set_range(self, min, max):
        if self.test_range(min, max):
            self.table.SetRange(min, max)
            self.table.Build()

    def translate(self, dx, dy):
        self.translation[0] += dx
        self.translation[1] += dy

    def reset_translation(self):
        self.translation = [0, 0]



class MaskSliceActor():
    def __init__(self, source, orientation, opacity=1.0):

        self.reslice = vtk.vtkImageReslice()
        self.reslice.SetInputData(source)
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetResliceAxes(orientation)
        self.reslice.SetInterpolationModeToNearestNeighbor()

        # Set lookup table
        color_transfer = vtk.vtkDiscretizableColorTransferFunction()
        alpha_transfer = vtk.vtkPiecewiseFunction()
        color_transfer.AddRGBPoint(0, 0., 0., 0.) # Background
        alpha_transfer.AddPoint(0, 0) # Background
        for i, organ in enumerate(Settings.labels):
            color_transfer.AddRGBPoint(Settings.labels[organ]['value'], *Settings.labels[organ]['rgb'])
            if organ in Settings.organs:
                alpha_transfer.AddPoint(Settings.labels[organ]['value'], opacity)
            else:
                alpha_transfer.AddPoint(Settings.labels[organ]['value'], 0.)
        color_transfer.SetScalarOpacityFunction(alpha_transfer)
        color_transfer.EnableOpacityMappingOn()


        # Map the image through the lookup table
        self.color = vtk.vtkImageMapToColors()
        self.color.SetLookupTable(color_transfer)
        self.color.SetInputConnection(self.reslice.GetOutputPort())

        # Display the image
        self.actor = vtk.vtkImageActor()
        self.actor.GetMapper().SetInputConnection(self.color.GetOutputPort())


    def update_slice_image(self, source):
        self.reslice.SetInputData(source)
        self.color.Update()
