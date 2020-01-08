import numpy as np
import matplotlib.pyplot as plt
from .Settings import labels

from sklearn.metrics import pairwise_distances_argmin_min as min_dist
from skimage.segmentation import find_boundaries

from scipy.ndimage.morphology import binary_fill_holes
from scipy.ndimage.morphology import binary_closing, binary_opening

def improve_segmentation(ma_data, points):

    border = ma_data.vtkimg_to_numpy(ma_data.border_src)
    mask = ma_data.vtk_reader_to_numpy(ma_data.mask_src)

    point_dict = dict()
    for i, point in enumerate(points):
        if not point.label in point_dict.keys():
            point_dict[point.label] = {'new_pos' : [], 'ind' : []}
        point_dict[point.label]['new_pos'].append(point.pos)


    for organ in point_dict.keys():

        for new in point_dict[organ]['new_pos']:

            X = np.argwhere(border == labels[organ]['value'])
            arg_min, distance = min_dist([new], X, metric='euclidean')
            old = X[arg_min][0]

            # Print to what pixel the border is moved
            print("{} --> {}".format(old, new))

            # Used for calculations
            old = np.asarray(old)
            new = np.asarray(new)

            # Calculate the new border pixels
            nX = gaussian_weighing(mask, organ, old, new, sigma=5)

            # Remove the old points and add the new
            mask[mask == labels[organ]['value']] = 0
            mask[tuple(nX.T)] = labels[organ]['value']

            # Extract the new points and perform binary closing
            bound = binary_closing(mask == labels[organ]['value'])
            mask[bound] = labels[organ]['value']

            # Extract the pixels from binary closing and fill potential holes
            bound = binary_fill_holes(mask == labels[organ]['value'])
            mask[bound] = labels[organ]['value']

            boundaries = find_boundaries(mask)
            border = boundaries * mask


    return border, mask


def gaussian_weighing(ma_numpy, organ, old, new, sigma=1):

    # This is the directional vector to move in
    movement_direction = new - old

    min_dist = np.linalg.norm(new - old)

    # Segmentation mask
    X = np.argwhere(ma_numpy == labels[organ]['value']) # X, Y, Z

    # Gaussian weighing function, relative to old point
    weights = np.exp((-np.linalg.norm(X - new, axis=1) + min_dist)/(2*sigma))
    weights = np.expand_dims(weights, axis=0)

    # Add the vector to the current segmentation result
    movement = np.around((new-X) * weights.T).astype(int)

    return X + movement


'''

def gaussian_weighing2(ma_numpy, organ, old, new, sigma=1):

    # This is the directional vector to move in
    movement_direction = new - old
    normalized = np.sqrt(np.sum(np.power(movement_direction,2)))

    # Segmentation mask
    X = np.argwhere(ma_numpy == labels[organ]['value']) # X, Y, Z

    # Gaussian weighing function, relative to old point
    weights = np.exp(-np.linalg.norm(X - old, axis=1)/(2*sigma))

    movement_direction = np.expand_dims(movement_direction, axis=0)
    weights = np.expand_dims(weights, axis=0)

    # Add the vector to the current segmentation result
    resting_points = list()
    new_points = list()
    for i in range(2*int(normalized)): # Cast to int
        movement = np.around(movement_direction * weights.T).astype(int)
        p_mov = np.any(np.abs(movement) > 0, axis=1)

        if i == 0:
            resting_points += np.ndarray.tolist(X[p_mov == 0])
        else:
            new_points += np.ndarray.tolist(X[p_mov == 0])

        if np.any(p_mov):
            new_points += np.ndarray.tolist(X[p_mov] + movement[p_mov])
            movement_direction = movement_direction.astype('float64') - .5 * movement_direction/normalized
        else:
            break

        X = X[p_mov]
        weights = np.expand_dims(weights.squeeze()[p_mov], axis=0)

    return np.asarray(resting_points), np.unique(new_points, axis=0)

'''
