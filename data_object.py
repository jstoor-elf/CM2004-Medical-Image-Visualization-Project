from vtk.util.numpy_support import vtk_to_numpy
from vtk.util.numpy_support import numpy_to_vtk
import vtk

import numpy as np

from skimage.morphology import binary_opening
from skimage.segmentation import find_boundaries
import numpy as np

import Utilities.datareader as dr
from Utilities import Settings

from skimage.morphology import ball, binary_dilation, binary_erosion


class DataObject:

    # Static methods
    def vtkimg_to_numpy(self, vtkimg):
        dims = vtkimg.GetDimensions()
        sc = vtkimg.GetPointData().GetScalars()
        a = vtk_to_numpy(sc)
        a = a.reshape(*dims, order='F')

        return a


    def set_sources(self, im_path):

        if im_path:
            im_src = vtk.vtkNIFTIImageReader()
            im_src.SetFileName(im_path)
            im_src.Update()
            return im_src
        else:
            return None


    def vtk_reader_to_numpy(self, vtk):
        vtk.Update()
        return self.vtkimg_to_numpy(vtk.GetOutput())


class ImageObject(DataObject):

    def __init__(self, name, im_type='Train'):

        self.im_name   = dr.get_im_name_from_prefix(name)
        self.im_type   = im_type
        self.im_path   = self.__setup_im_path()

        self.im_src = self.set_sources(self.im_path)

        self.hist = self.calculate_histogram()

    def calculate_histogram(self):
        im_np = self.vtkimg_to_numpy(self.im_src.GetOutput())
        return np.unique(im_np, return_counts=True)


    def get_histogram(self):
        return self.hist


    def __setup_im_path(self):

        if self.im_type == 'Train':
            return dr.get_im_path(Settings.im_train_path, self.im_name)
        else:
            return dr.get_im_path(Settings.im_test_path, self.im_name)



class MaskObject(DataObject):

    def __init__(self, name, init_border=True):

        self.mask_name = dr.get_mask_from_im_name(dr.get_im_name_from_prefix(name))
        self.mask_path   = dr.get_im_path(Settings.mask_train_path, self.mask_name)


        self.mask_src = self.set_sources(self.mask_path)
        self.border_src = self.border_of_mask() if init_border else None
        self.improved = None


    def border_of_mask(self):
        self.mask_src.Update()

        im_nump = self.vtkimg_to_numpy(self.mask_src.GetOutput())
        boundaries = find_boundaries(im_nump)
        new_im = im_nump*boundaries

        return self.numpy_to_vtkimg(new_im)


    def numpy_to_vtkimg(self, np_im):

        VTK_data = numpy_to_vtk(num_array=np_im.ravel(order='F'), \
            deep=True, array_type=vtk.VTK_UNSIGNED_INT)

        depthImageData = vtk.vtkImageData()
        depthImageData.SetDimensions(self.mask_src.GetOutput().GetDimensions())
        #assume 0,0 origin and 1,1 spacing.
        depthImageData.SetSpacing(self.mask_src.GetOutput().GetSpacing())
        depthImageData.SetOrigin(self.mask_src.GetOutput().GetOrigin())
        depthImageData.GetPointData().SetScalars(VTK_data)

        return depthImageData


    def renew_border_mask(self, np_im):
        self.border_src = self.numpy_to_vtkimg(np_im)
