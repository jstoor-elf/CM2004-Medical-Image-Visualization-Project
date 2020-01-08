import vtk

import os, sys
sys.path.append(os.path.abspath(os.path.join('..', 'Utilities')))
from Utilities import Settings


class InputManager:

    def __init__(self):

        self.nmb_ids = 0

        # Store all point objects
        self.points = list()

        # Create planes for the axial, sagittal and coronal view
        self.planes = list()
        for x in range(3):
            plane = vtk.vtkPlane()
            plane.SetOrigin(0, 0, 1)
            plane.SetNormal(0, 0, 1)
            self.planes.append(plane)

        self.points = list()


    def move_plane(self, orie, dx):
        index = ['Axial', 'Sagittal', 'Coronal'].index(orie)
        for point in self.points:
            point = point.points2D[index]
            coords = point.point.GetCenter()
            point.point.SetCenter(coords[0], coords[1], coords[2] + dx)
            point.sphereMapper.Update()


    def restore_planes(self):
        for i in range(3):
            for point in self.points:
                point = point.points2D[i]
                point.point.SetCenter(*point.start_position)
                point.sphereMapper.Update()


    def add_point(self, label, pos, planes_dx, translations, pixel_pos):
        point = SlicePoint(self.nmb_ids, label, pos, self.planes, planes_dx, translations, pixel_pos)
        self.points.append(point)
        self.nmb_ids += 1
        return self.points[-1]



    def remove_points(self, remove_points, render_list):
        for gui_point in remove_points:
            for vis_point in self.points:
                if gui_point.id == vis_point.id:
                    for i in range(3):
                        render_list[i].vis_object.renderer.RemoveActor(vis_point.points2D[i].actor)
                    render_list[3].vis_object.renderer.RemoveActor(vis_point.point3D.actor)
                    self.points.remove(vis_point)
                    break



    def translate_points(self, dx, dy, orie):

        if orie == 'Axial':
            index = 0
        elif orie == 'Sagittal':
            index = 1
        elif orie == 'Coronal':
            index = 2

        for point in self.points:
            point2D = point.points2D[index]
            center = point2D.point.GetCenter()
            point2D.point.SetCenter(center[0] + dx, center[1] + dy, center[2])
            point2D.sphereMapper.Update()



### Classes to handle the points and the synchronization of the windows  ###

class SlicePoint:

    def __init__(self, id, label, pos, planes, planes_dx, translations, pixel_pos):

        self.pixel_coordinates = [int(pixel_pos[x]) for x in range(3)]
        self.id = id
        self.label = label
        self.pos = pos
        self.point3D = Point3D(self.pos[3], self.label)
        self.points2D = list()

        for i in range(3):
            self.points2D.append(Point2D(self.pos[i], planes[i], self.label, planes_dx[i], translations[i]))




class Point3D:

    def __init__(self, pos, label):

        self.point = vtk.vtkSphereSource()
        self.point.SetRadius(5)
        self.point.SetCenter(pos[0], pos[1], pos[2])
        self.point.SetThetaResolution(100)
        self.point.SetPhiResolution(100)

        cmapper = vtk.vtkPolyDataMapper()
        cmapper.SetInputConnection(self.point.GetOutputPort())
        cmapper.ScalarVisibilityOff()

        self.actor = vtk.vtkActor()
        self.actor.GetProperty().SetColor(*Settings.labels[label]['rgb'])
        self.actor.GetProperty().SetLineWidth(5)
        self.actor.SetMapper(cmapper)


class  Point2D:

    def __init__(self, pos, plane, label, plane_dx, translation):

        self.start_position = (pos[0], pos[1], pos[2] + 1)

        self.point = vtk.vtkSphereSource()
        self.point.SetRadius(2)
        self.point.SetCenter(pos[0] + translation[0], pos[1] + translation[1], \
            pos[2] - plane_dx + 1)
        self.point.SetThetaResolution(100)
        self.point.SetPhiResolution(100)

        self.sphereMapper = vtk.vtkPolyDataMapper()
        self.sphereMapper.SetInputConnection(self.point.GetOutputPort())
        self.sphereMapper.Update()

        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(self.sphereMapper.GetInput())
        cutter.Update()

        full_point = vtk.vtkContourTriangulator()
        full_point.SetInputConnection(cutter.GetOutputPort())
        full_point.Update()

        cmapper = vtk.vtkPolyDataMapper()
        cmapper.SetResolveCoincidentTopologyToPolygonOffset()
        cmapper.SetInputConnection(full_point.GetOutputPort())
        cmapper.ScalarVisibilityOff()

        self.actor = vtk.vtkActor()
        self.actor.GetProperty().SetColor(*Settings.labels[label]['rgb'])
        self.actor.GetProperty().SetAmbient(1)
        self.actor.GetProperty().SetDiffuse(0)
        self.actor.GetProperty().SetSpecular(0)
        self.actor.SetMapper(cmapper)
