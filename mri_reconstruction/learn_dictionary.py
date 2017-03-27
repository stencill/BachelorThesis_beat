# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 14:22:40 2017

@author: beats
"""

from time import time

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
from PIL import Image

from sklearn.decomposition import MiniBatchDictionaryLearning
from sklearn.feature_extraction.image import extract_patches_2d
from sklearn.feature_extraction.image import reconstruct_from_patches_2d
from sklearn.utils.testing import SkipTest
from sklearn.utils.fixes import sp_version

def train_dictionary(images, n_components=100, patch_size=(5,5), train_percentage = 0.8): 
    '''
    learns dictionary consisting of n_components atoms of size patch_size of input images
    
    Parameters
    ----------
    images: Input Images to learn the Dictionary.
    
    n_components: Number of atoms of the dictionary
    
    patch_size: Size of atoms
    
    train_percentage: Percentage of data on which the dictionary is trained from first to last element.
    
    Return
    ------
    Returns the Dictionary V.
    
    '''
    row, cols, timesteps, persons = images.shape
    
    # Extract patches from the images
    for i in range(0,int(np.floor(persons*train_percentage))):
        for j in range(0,timesteps):
            patches = extract_patches_2d(images[:,:,j,i], patch_size)
            data[i,j,:] = patches.reshape(patches.shape[0], -1) # stack all patches in one vector?????

    data = data.reshape(data.shape[0], -1)
    data -= np.mean(data, axis=0)
    data /= np.std(data, axis=0)
    
    # Learn the Dictionary on the extracted patches
    t0 = time()
    dico = MiniBatchDictionaryLearning(n_components, alpha=1, n_iter=500)
    V = dico.fit(data).components_
    dt = time() - t0
    
    print('Dictionary trained on %d patches in %.2fs.', % (len(data), dt))
    
    return V

def test_dictionary(images, n_components, patch_size(5,5),transform_algorithms, test_percentage=0.2):
    '''
    '''
    
    
    row, cols, timesteps, persons = images.shape
    
    #extract patches from images
    
    #reconstruct images using input transform algorithm
    t0 = time()
    
    
    dt = time() - t0
    
    print('Tested on %d images in %.2fs.', %(images, dt))