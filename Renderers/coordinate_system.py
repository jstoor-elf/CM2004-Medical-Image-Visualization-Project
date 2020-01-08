import vtk

import os, sys
import copy
sys.path.append(os.path.abspath(os.path.join('..', 'Utilities')))
from Utilities import Settings

class CoordinateSystem3D:

    def __init__(self, im_source):

        sizes = im_source.GetExecutive().GetWholeExtent(im_source.GetOutputInformation(0))
        spacing = im_source.GetOutput().GetSpacing()
        origin = im_source.GetOutput().GetOrigin()

        revert = [spacing[0] * (sizes[0] + sizes[1]),
                  spacing[1] * (sizes[2] + sizes[3]),
                  spacing[2] * (sizes[4] + sizes[5])]


        self.center = [origin[0] + spacing[0] * 0.5 * (sizes[0] + sizes[1]),
                       origin[1] + spacing[1] * 0.5 * (sizes[2] + sizes[3]),
                       origin[2] + spacing[2] * 0.5 * (sizes[4] + sizes[5])]

        self.origin = [0, 0, 0]


         ## DEFINITION OF LINES TO DEFINE COORDINATE SYSTEM
        self.lines = list()
        color = Settings.coordinate_system['color']
        for a, coord in enumerate(['z', 'y', 'x']):
            self.lines.append(SliceLine(self.center, a, revert[a], coord, color))


        ## DEFINITION OF PLANES TO USE WITH LINES
        self.planes = list()
        planes = [(0, 1), (1, 2), (0, 2)]
        for plane in planes:
            dicter = {a: revert[a] for a in plane}
            # Append the plane to the list
            self.planes.append(SlicePlane(self.center, dicter))


    def translate_line(self, dx, dy, orie):

        if orie == 'Axial':
            # Axial Lines
            self.origin[0] -= dx
            self.origin[1] += dy
            self.lines[1].translate_line(0, dx)
            self.lines[0].translate_line(1, dy)
            self.lines[2].translate_line(0, dx)
            self.lines[2].translate_line(1, dy)
            self.planes[1].move_plane(dx)
            self.planes[2].move_plane(-dy)

        elif orie == 'Sagittal':
            # Sagittal Lines
            self.origin[1] += dx
            self.origin[2] += dy
            self.lines[0].translate_line(2, -dy)
            self.lines[2].translate_line(1, dx)
            self.lines[0].translate_line(1, dx)
            self.lines[1].translate_line(2, -dy)
            self.planes[0].move_plane(-dy)
            self.planes[2].move_plane(-dx)

        elif orie == 'Coronal':
            # Coronal Lines
            self.origin[0] += dx
            self.origin[2] += dy
            self.lines[1].translate_line(2, -dy)
            self.lines[2].translate_line(0, dx)
            self.lines[1].translate_line(0, dx)
            self.lines[0].translate_line(2, -dy)
            self.planes[0].move_plane(-dy)
            self.planes[1].move_plane(dx)


    def translate_line_depth(self, dx, orie):

        if orie == 'Axial':
            # Axial Lines
            self.origin[2] += dx
            self.lines[0].translate_line(2, -dx)
            self.lines[1].translate_line(2, -dx)
            self.planes[0].move_plane(-dx)

        elif orie == 'Sagittal':
            # Sagittal Lines
            self.origin[0] += dx
            self.lines[1].translate_line(0, -dx)
            self.lines[2].translate_line(0, -dx)
            self.planes[1].move_plane(-dx)

        elif orie == 'Coronal':
            # Coronal Lines
            self.origin[1] += dx
            self.lines[0].translate_line(1, dx)
            self.lines[2].translate_line(1, dx)
            self.planes[2].move_plane(-dx)


    def reset_lines(self):
        self.origin = [0, 0, 0]
        for line in self.lines:
            line.reset_line()

        for plane in self.planes:
            plane.reset_plane()


class CoordinateSystem2D:

    def __init__(self, im_source, orie):

        sizes = im_source.GetExecutive().GetWholeExtent(im_source.GetOutputInformation(0))
        spacing = im_source.GetOutput().GetSpacing()

        self.revert = [spacing[0] * (sizes[0] + sizes[1]),
                       spacing[1] * (sizes[2] + sizes[3]),
                       spacing[2] * (sizes[4] + sizes[5])]


        self.lines = list() # Store lines in list
        color = Settings.coordinate_system['color']
        if orie == 'Axial':
            # Axial Lines
            self.lines.append(SliceLine([0., 0., 1], 0, self.revert[0], 'x', color))
            self.lines.append(SliceLine([0., 0., 1], 1, self.revert[1], 'y', color))
        elif orie == 'Sagittal':
            # Sagittal Lines
            self.lines.append(SliceLine([0., 0., 1], 0, self.revert[0], 'z', color))
            self.lines.append(SliceLine([0., 0., 1], 1, self.revert[2], 'y', color))
        elif orie == 'Coronal':
            # Coronal Lines
            self.lines.append(SliceLine([0., 0., 1], 0, self.revert[0], 'z', color))
            self.lines.append(SliceLine([0., 0., 1], 1, self.revert[2], 'x', color))



    def translate_line(self, dx, dy, orie, move=True):

        self.lines[0].translate_line(1, dy)
        self.lines[1].translate_line(0, dx)
        if move:
            self.lines[0].move_line(dx)
            self.lines[1].move_line(dy)


    def reset_lines(self):
        for line in self.lines:
            line.reset_line()


class SliceLine:

    def __init__(self, center, index, deviation, coord_axis, color):

        self.coord_axis = coord_axis
        self.index = index
        self.end_points = []
        self.reset_points = []

        # Define the enpoints of the line
        midpoints = center.copy()
        for mult in [-.5, 1.]:
            midpoints[self.index] += mult * deviation
            self.end_points.append(midpoints.copy())

        # Store copy of inital points for resets
        self.reset_points = copy.deepcopy(self.end_points)

        # Create the line source
        self.lineSource = vtk.vtkLineSource()
        self.lineSource.SetPoint1(*self.end_points[0])
        self.lineSource.SetPoint2(*self.end_points[1])


        # Create the mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.lineSource.GetOutputPort())

        # Create the mapper
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(*color)
        self.actor.GetProperty().SetOpacity(1.)


    def reset_line(self):
        self.end_points = copy.deepcopy(self.reset_points)
        self.lineSource.SetPoint1(*self.end_points[0])
        self.lineSource.SetPoint2(*self.end_points[1])


    def move_line(self, delta):
        self.end_points[0][self.index] += delta
        self.end_points[1][self.index] += delta

        self.lineSource.SetPoint1(*self.end_points[0])
        self.lineSource.SetPoint2(*self.end_points[1])


    def slate_line(self, index, delta):
        current = self.end_points.copy()
        current[0][index] += delta
        current[1][index] += delta

        self.end_points = current
        self.lineSource.SetPoint1(*self.end_points[0])
        self.lineSource.SetPoint2(*self.end_points[1])


    def translate_line(self, index, delta):

        current = self.end_points.copy()
        current[0][index] += delta
        current[1][index] += delta

        self.end_points = current
        self.lineSource.SetPoint1(*self.end_points[0])
        self.lineSource.SetPoint2(*self.end_points[1])



class SlicePlane:

    def __init__(self, center, deviations):

        self.center = copy.deepcopy(center)
        self.deviations = deviations
        for dev in self.deviations:
            self.center[dev] -= self.deviations[dev]/2

        # Set the points of the plane
        self.kickstart()

        self.outline = vtk.vtkOutlineFilter()
        self.outline.SetInputData(self.planeSource.GetOutput())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.outline.GetOutputPort())

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(*Settings.coordinate_system['plane_color'])
        self.actor.GetProperty().SetOpacity(1.)

    def move_plane(self, delta):
        self.planeSource.Update()
        self.planeSource.Push(delta)


    def kickstart(self):
        self.planeSource = vtk.vtkPlaneSource()
        self.planeSource.SetCenter(*self.center)
        for i, dev in enumerate(self.deviations):
            center = self.center.copy()
            center[dev] += self.deviations[dev]
            self.planeSource.SetPoint1(*center) if i == 0 else self.planeSource.SetPoint2(*center)
        self.planeSource.Update()


    def reset_plane(self):
        self.kickstart()
        self.outline.SetInputData(self.planeSource.GetOutput())
