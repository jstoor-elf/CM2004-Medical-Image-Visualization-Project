
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from .coordinate_system import CoordinateSystem3D
import numpy as np

import os, sys
sys.path.append(os.path.abspath(os.path.join('..', 'Utilities')))
from Utilities import Settings

from matplotlib import cm

from vtk.util.numpy_support import vtk_to_numpy

class VolumeRenderer:

    def __init__(self, parent_vis, current_data, current_gt=None):

        # Reference to vislization
        self.vis_widget = parent_vis

        # Define volume and surface rendition
        self.volume_rendition  = VolumeActor(current_data.im_src)
        self.surface_rendition = SurfaceActor(current_gt.mask_src) if current_gt else None

        # Text actor
        self.textActor = vtk.vtkTextActor()
        self.textActor.SetPosition(*Settings.vis_text_info['position'])
        self.textActor.SetInput("3D Rendition")
        self.textActor.GetTextProperty().SetFontSize(Settings.vis_text_info['size'])
        self.textActor.GetTextProperty().SetColor(*Settings.vis_text_info['color'])


        # include (xSpacing, ySpacing, zSpacing) to get the correct slices

        self.coordinate_system = CoordinateSystem3D(current_data.im_src)

        camera = vtk.vtkCamera()
        camera.SetViewUp(0., 0., -1.)
        camera.SetPosition(-100, 700, -200)
        camera.SetFocalPoint(100, 100, 100)
        camera.Zoom(0.80)


        # Add the actors
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetActiveCamera(camera)
        #self.renderer.AddActor(self.volume_rendition.actor)
        if current_gt:
            self.change_actor(True, 'surface')
        self.change_actor(True, 'coordinates')
        self.renderer.AddActor(self.textActor)

        # Interaction style
        self.inter_style = vtk.vtkInteractorStyleTrackballCamera()


    # Set the communicator so that other windows can be reached
    def setWindowCommunicator(self, window_communicator):
        self.window_communicator = window_communicator


    def setInputManager(self, input_manager):
        self.input_manager = input_manager


    def change_actor(self, is_checked, actor_type):

        # Fetch function:
        func = self.renderer.RemoveActor if not is_checked else self.renderer.AddActor

        # Perform function step on actor_type
        if actor_type == 'coordinates':
            for line in self.coordinate_system.lines:
                func(line.actor)
            for plane in self.coordinate_system.planes:
                func(plane.actor)
        elif actor_type == 'volumetric':
            func(self.volume_rendition.actor)
        elif actor_type == 'surface':
            func(self.surface_rendition.actor)


    def get_look_up(self):
        below = self.volume_rendition.opacity_pts[0][0]
        above = self.volume_rendition.opacity_pts[0][-1]
        return below, above

    def set_volume_lookup(self, interval):
        self.volume_rendition.set_color_range(interval)


    def get_opacity_pts(self):
        return self.volume_rendition.opacity_pts


    def set_opacity_pts(self, x, y):
        return self.volume_rendition.set_opacity_points(x, y)


    def change_cmap(self, name):
        self.volume_rendition.set_cmap(name)


    def get_cmap(self):
        return self.volume_rendition.c_map_name


    def update_masks(self, improved):
        self.surface_rendition.update_mask(improved)


class VolumeActor:
    def __init__(self, source):

        # 3 set up the volume mapper
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputConnection(source.GetOutputPort())

        # 4 transfer functions for color and opacity
        self.color_transfer = vtk.vtkColorTransferFunction()
        self.alpha_transfer = vtk.vtkPiecewiseFunction()
        self.c_map_name = 'copper'
        self.c_map = cm.get_cmap(self.c_map_name)
        self.init_opacity_points()
        self.set_color_transfer() # Fill color transfer function


        # 6 set up the volume properties
        self.volume_properties = vtk.vtkVolumeProperty()
        self.volume_properties.SetColor(0, self.color_transfer)
        self.volume_properties.SetScalarOpacity(0, self.alpha_transfer)
        self.volume_properties.SetInterpolationTypeToLinear()

        self.volume_properties.ShadeOn()
        self.volume_properties.SetAmbient(1.0)
        self.volume_properties.SetDiffuse(0.7)
        self.volume_properties.SetSpecular(0.5)


        # 7 set up the actor
        self.actor = vtk.vtkVolume()
        self.actor.SetMapper(volume_mapper)
        self.actor.SetProperty(self.volume_properties)


    def set_cmap(self, name):
        self.c_map_name = name
        self.c_map = cm.get_cmap(self.c_map_name)
        self.set_color_transfer()


    def set_color_range(self, interval):
        min, max = interval
        self.width, self.level = int(max - min), int(min + (max - min) / 2)
        self.color_transfer.RemoveAllPoints()
        self.alpha_transfer.RemoveAllPoints()
        self.set_color_transfer()


    def init_opacity_points(self):
        self.opacity_pts = [[], []]
        pts = [(-2000, 0.), (1200, 0.), (1600, .4), (2000, 0.), (3000, 0.)]
        for x, y in pts:
            self.opacity_pts[0].append(x)
            self.opacity_pts[1].append(y)


    def set_opacity_points(self, xs, ys):
        self.opacity_pts = [[], []]
        for x, y in zip(xs, ys):
            self.opacity_pts[0].append(int(x))
            self.opacity_pts[1].append(y)

        self.set_color_transfer()


    def set_color_transfer(self):

        pos_ind = np.where(np.asarray(self.opacity_pts[1]) > 0.0001)[0]
        print(pos_ind)
        min, max = self.opacity_pts[0][np.min(pos_ind)-1], self.opacity_pts[0][np.max(pos_ind)+1]
        for i in range(min, max, 10):
            color = self.c_map((i - min) / (max - min))
            self.color_transfer.AddRGBPoint(i, *color[:-1])

        for x, y in zip(*self.opacity_pts):
            self.alpha_transfer.AddPoint(x, y)


class SurfaceActor:

    def __init__(self, source):

        # Get list with string-representations of the organs to be used
        organs = Settings.organs

        source.Update()

        # Filter
        cast_filter = vtk.vtkImageCast()
        cast_filter.SetOutputScalarTypeToUnsignedInt()
        cast_filter.SetInputConnection(source.GetOutputPort())
        cast_filter.Update()

        # Create mesh using marching cube
        march = vtk.vtkDiscreteMarchingCubes()
        march.ComputeNormalsOn()
        march.ComputeGradientsOn()
        for i, organ in enumerate(organs):
            march.SetValue(i, Settings.labels[organ]['value'])
        march.SetInputData(cast_filter.GetOutput())
        march.Update()

        # Filtrate the masks
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetInputConnection(march.GetOutputPort())
        smooth.SetNumberOfIterations(15)
        smooth.BoundarySmoothingOff()
        smooth.FeatureEdgeSmoothingOff()
        smooth.SetFeatureAngle(120.0)
        smooth.SetPassBand(.001)
        smooth.NonManifoldSmoothingOn()
        smooth.NormalizeCoordinatesOn()
        smooth.Update()

        # print(smooth.GetOutput().GetPoints())
        #array->GetTuple(desiredpoint, tuple);
        #delete[] tuple;


        # Set lookup table
        self.color_transfer = vtk.vtkDiscretizableColorTransferFunction()
        self.alpha_transfer = vtk.vtkPiecewiseFunction()
        self.color_transfer.AddRGBPoint(0, 0., 0., 0.) # Background
        self.alpha_transfer.AddPoint(0, 0) # Background
        for i, organ in enumerate(Settings.organs):
            self.color_transfer.AddRGBPoint(Settings.labels[organ]['value'], *Settings.labels[organ]['rgb'])
            self.alpha_transfer.AddPoint(Settings.labels[organ]['value'], 1.)
        self.color_transfer.SetScalarOpacityFunction(self.alpha_transfer)


        # Surface mapper
        self.surface_mapper = vtk.vtkPolyDataMapper()
        self.surface_mapper.SetLookupTable(self.color_transfer)
        self.surface_mapper.SetInputConnection(smooth.GetOutputPort())


        # self.verts = vtk_to_numpy(smooth.GetOutput().GetPoints().GetData())
        modelPolyData = self.surface_mapper.GetInput()
        numPoints = modelPolyData.GetNumberOfPoints()

        locator = vtk.vtkPointLocator()
        locator.SetDataSet(modelPolyData)
        locator.BuildLocator()

        for ptId in range(numPoints): # (ptId=0; ptId<numPoints; ptId++)
            point = modelPolyData.GetPoint(ptId)
            id = locator.FindClosestPoint(point)
            print(point)
            print(modelPolyData.GetPointData().GetScalars().GetTuple(id))



        # Create the actor
        self.actor = vtk.vtkActor()
        self.actor.GetProperty().SetOpacity(1.)
        self.actor.SetMapper(self.surface_mapper)
        self.actor.GetProperty().ShadingOn()
        


    def single_out_organ(self, organ):
        self.alpha_transfer.RemoveAllPoints()
        for i, t_organ in enumerate(Settings.organs):
            if t_organ == organ:
                self.alpha_transfer.AddPoint(Settings.labels[t_organ]['value'], .7)
            else:
                self.alpha_transfer.AddPoint(Settings.labels[t_organ]['value'], 0.)
        self.color_transfer.EnableOpacityMappingOn()
        self.surface_mapper.Update()


    def reset_organs(self):
        # Set lookup table
        self.alpha_transfer.RemoveAllPoints()
        for i, organ in enumerate(Settings.organs):
            self.alpha_transfer.AddPoint(Settings.labels[organ]['value'], 1.)
        self.color_transfer.EnableOpacityMappingOff()
        self.surface_mapper.Update()


    def update_mask(self, src):

        # Filter
        cast_filter = vtk.vtkImageCast()
        cast_filter.SetOutputScalarTypeToUnsignedInt()
        cast_filter.SetInputData(src)
        cast_filter.Update()

        # Create mesh using marching cube
        march = vtk.vtkDiscreteMarchingCubes()
        march.ComputeNormalsOn()
        march.ComputeGradientsOn()
        for i, organ in enumerate(Settings.organs):
            march.SetValue(i, Settings.labels[organ]['value'])
        march.SetInputData(cast_filter.GetOutput())
        march.Update()

        # Filtrate the masks
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetInputConnection(march.GetOutputPort())
        smooth.SetNumberOfIterations(15)
        smooth.BoundarySmoothingOff()
        smooth.FeatureEdgeSmoothingOff()
        smooth.SetFeatureAngle(120.0)
        smooth.SetPassBand(.001)
        smooth.NonManifoldSmoothingOn()
        smooth.NormalizeCoordinatesOn()
        smooth.Update()

        self.surface_mapper.SetInputConnection(smooth.GetOutputPort())


    def get_vertecies(self):
        return None # self.verts
