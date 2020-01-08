import os
import re

def get_im_names(im_path):
    return [f for f in sorted(os.listdir(im_path)) if not f.startswith('.')]


def stripped_im_names(im_names):
    return [re.sub('_image.nii.gz', '.nii', im_name) for im_name in im_names]


def get_im_path(im_path, im_name):
    return os.path.join(im_path, im_name)


def get_mask_from_im_name(im_name):
    return re.sub('image', 'label', im_name)


def get_im_path_from_mask_name(im_path, im_name):
        im_name = re.sub('label', 'image', im_name)
        return os.path.join(im_path, im_name)


def get_im_name_from_prefix(im_name):
    return re.sub('.nii', '_image.nii.gz', im_name)
