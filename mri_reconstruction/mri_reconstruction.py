# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 15:50:26 2017

@author: beats
"""

print(__doc__)

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp

from learn_dictionary import train_dictionary
from learn_dictionary import test_dictionary

# import matlab data (johannes')
try:
    imgs = sp.io.loadmat('ismrm_ssa_imgs.mat')
    imgs = imgs['imgs']
except:
    print('Error while loading images!')

height, width, timesteps, persons = imgs.shape
    
# Transform to k-Space
k_imgs = np.fft.fft2(imgs, axes=(0,1))

# Train dictionary on fully sampled data
V = learn_dictionary(imgs, n_components=100, patch_size=(5,5))

# Create undersampling Mask
undersampling = 0.3
sample_mask = np.random.choice([0, 1], size=height, p=[undersampling, 1-undersampling])
sample_mask = np.array([sample_mask]*height).transpose()

# Apply to all timesteps and persons
k_undersampled = k_imgs.copy()
for i in range(1,imgs.shape[2]):
    for j in range(1,imgs.shape[3]):
        k_undersampled[:,:,i,j] = sample_mask * k_imgs[:,:,i,j]

# Reconstruction via ifft2
reconstructions_undersampled = np.fft.ifft2(k_undersampled, axes=(0,1))
reconstructions = np.fft.ifft2(k_imgs, axes=(0,1))

# Test dictionary

# Plot various Images
plt.figure(figsize=(40,40))
plt.subplot(1,5,1)
plt.imshow(imgs[:,:,1,10], cmap='gray')
plt.subplot(1,5,2)
plt.imshow(np.log(np.abs(k_imgs[:,:,1,10])),  cmap='gray')
plt.subplot(1,5,3)
plt.imshow(np.real(reconstructions[:,:,1,10]),  cmap='gray')
plt.subplot(1,5,4)
plt.imshow(np.log(np.abs(k_undersampled[:,:,1,10])),  cmap='gray')
plt.subplot(1,5,5)
plt.imshow(np.real(reconstructions_undersampled[:,:,1,10]),  cmap='gray')
