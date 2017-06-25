# -*- coding: utf-8 -*-
"""
Created on Thu May 11 16:39:26 2017

@author: beats@student.ethz.ch

Versions:
--------
Anaconda Python 2.7
Scikit-learn 0.19dev0

"""

import numpy as np
import scipy as sp
import random
import time

from sklearn.decomposition import MiniBatchDictionaryLearning
from sklearn.decomposition import SparseCoder

#import poisson_disc_light
#import enhanced_grid

import matplotlib.pyplot as plt

def normalize_data(data):
    print"normalizing..."
    training_data = data.copy()
    t_mean = np.mean(training_data, axis = 0, keepdims = True)
    training_data = training_data - t_mean
    training_data = training_data - np.mean(training_data, axis = 1, keepdims = True)
    idxs = np.argsort( np.sum(training_data**2, axis = 1) )
    training_data = training_data[idxs[50:], :]
    training_data = training_data / np.std(training_data, axis = 0, keepdims = True)
    # training_data = training_data / np.std(training_data, axis = 1, keepdims = True)
    print 'normalization', np.mean(training_data), np.std(training_data)
    return training_data

def fft_transform(imgs):
    k_imgs = np.fft.fft2(imgs, axes=(0,1))
    k_imgs = np.fft.fftshift(k_imgs)
    return k_imgs

def ifft_transform(k_imgs):
    k_imgs = np.fft.ifftshift(k_imgs)
    imgs = abs(np.fft.ifft2(k_imgs, axes=(0,1)))
    return imgs

def create_masks(shape, undersampling, method, full_center=False, k=8, export_masks=False):
    
    k = int(k/2)
    masks = np.zeros((shape))
    
    if method == 'uniform':
        masks = np.random.random_sample(shape) > undersampling
        
    if method == 'gaussian_lines':
        if full_center:
            threshhold=sp.stats.norm.ppf(undersampling)
        else:
            threshhold = sp.stats.norm.ppf(undersampling)
            
        for t in range(shape[2]):
            for p in range(shape[3]):
                mask = np.random.randn(shape[0])
                for i in range(len(mask)):
                    if mask[i] < threshhold:
                        mask[i] = 0
                    else:
                        mask[i] = 1  
                for j in range(shape[1]):
                    masks[:,j,t,p] = mask
    
    if full_center:
        for t in range(shape[2]):
            for p in range(shape[3]):
                masks[int(shape[0]/2)-k:int(shape[0]/2)+k,:,t,p] = 1
        
    if export_masks:
        sp.io.savemat('masks' + '_' + str(method) + '_' + str(undersampling) + '.mat', {'masks':masks})
        
    return masks

def mask_imgs(imgs, method='uniform', full_center=False, k=8, undersampling=0.5, n_gauss=100, variance=20, return_masks=False, export=False):
    '''
    parameters
    ----------
    imgs: input images
    method: defines subsampling method
    full_center: bool if the center of the mask should be fully sampled or not
    k: amount of  frequencies to fully sample from center
    '''
    print"masking imgs..."
    
    masks = create_masks(imgs.shape, undersampling, method, full_center=full_center, k=k)
    
    for i in range(imgs.shape[3]):
        for j in range(imgs.shape[2]):
            imgs[:,:,j,i] *= masks[:,:,j,i]
    
    if return_masks:
        return imgs, masks
    
    return imgs

def imgs_to_data(imgs, n_features):

    if len(imgs.shape) < 4:
        data = np.transpose(imgs, (2,0,1))
        data = np.reshape(data, (n_features, -1), order='F')
        data = data.T
        return data
    
    data = np.transpose(imgs, (2,0,1,3))
    data = np.reshape(data, (n_features, -1), order='F')
    data = data.T
    return data

def data_to_imgs(data, shape):
    data = data.T
    
    if data.shape[0] == shape[0]*shape[1]:
        imgs = np.reshape(data, (shape[2], shape[0], shape[1]), order='F')
        return imgs
        
    imgs = np.reshape(data, (shape[2], shape[0], shape[1], -1), order='F')
    imgs = np.transpose(imgs,(1,2,0,3))
    return imgs

def imgs_error(img1, img2):
    err = np.sqrt(np.sum((img1 - img2) ** 2))
    err /= (img1.shape[0] * img1.shape[1])
    return err

def total_error(imgs_ref, imgs_rec):
    err_tot = 0
    for i in range(imgs_ref.shape[3]):
        for j in range(imgs_ref.shape[2]):
            err_tot += imgs_error(imgs_ref[:,:,j,i], imgs_rec[:,:,j,i])
    return err_tot

def peak_signal_to_noise_ratio(imgs_ref, recs):
    '''
    '''
    s = imgs_ref.shape
    P = s[0]*s[1]*s[2]
    
    err = np.linalg.norm(imgs_ref-recs)/s[3]
    
    psnr = 10*np.log10(1/(err**2/P))
        
    return psnr

def sparsity(A):
    A = np.ravel(A)
    return 1-np.float64(np.count_nonzero(A))/len(A)

def get_imgs(imgs, train_amount=0.8):
    perm = np.random.permutation(imgs.shape[3])
    imgs_train = imgs[:,:,:,perm[:int(train_amount*len(perm))]]
    imgs_test = imgs[:,:,:,perm[-int((1.0-train_amount)*len(perm)):]]
    return imgs_train, imgs_test

def initialize_dictionary(n_components, data_train):
    init = np.zeros((n_components, data_train.shape[1]))
    
    for k in range(int(n_components/2)):
        for n in range(data_train.shape[1]):
            init[k,n] = np.cos((np.pi/data_train.shape[1]*n*(k+0.5)))
            
    for i in range(int(n_components/2),n_components):
        init[i,:] = data_train[int(random.uniform(0,data_train.shape[0])),:]
    
    return init

def export_plot_as_mat(a, b, undersamp, undersamp_type, n_comp, b_s, n_iter, fit_alg, transf_alg, alpha_train, alpha_test, export_info=False):
    info = ('undersampling' + str(undersamp) + 'undersampling_type' + str(undersamp_type) + 
            'n_comp=' + str(n_comp) + ' batch_size=' + str(b_s) + 
            ' n_iter=' + str(n_iter) + ' fit_alg=' + str(fit_alg) + 
            ' transform_alg=' + str(transf_alg) + ' alpha_train=' + 
            str(alpha_train) + ' alpha_test=' + str(alpha_test))
    sp.io.savemat('psnr' + '_' + 'ncomponents' + '.mat', {str(a):a, str(b):b, 'info':info})
    
def learn_dictionary(imgs, n_components, alpha, fit_algorithm, n_iter, batch_size, n_jobs=1, verbose=0):
    training_data = imgs_to_data(imgs, imgs.shape[2])
#    training_data = normalize_data(training_data)
    init = initialize_dictionary(n_components, training_data.copy())
    dico = MiniBatchDictionaryLearning(n_components=n_components, alpha=alpha, fit_algorithm=fit_algorithm, dict_init=init.copy(),
                                       n_iter=n_iter, batch_size=batch_size, verbose=1)
    D = dico.fit(training_data).components_
    return D, init

def reconstruct_dataset(b, masks, D, p_transform_alpha, p_transform_n_nonzero_coefs, p_transform_algorithm,
                        n_iter, n_jobs=1, verbose=0):

    def reconstruct(b, masks, D, p_transform_alpha, p_transform_n_nonzero_coefs, p_transform_algorithm,
                    n_iter, n_jobs=1, verbose=0):

        Nt = masks.shape[2]
        rows, cols = masks.shape[0:2]
        X = np.zeros((rows,cols,Nt))
        coder = SparseCoder(D, transform_algorithm=p_transform_algorithm, transform_n_nonzero_coefs=p_transform_n_nonzero_coefs,
                            transform_alpha=p_transform_alpha, n_jobs=n_jobs)
        errs = np.zeros(Nt)
        if verbose:
            print 'alpha_transform= ', p_transform_alpha
        for i in range(Nt):
            X[:,:,i] = ifft_transform(b[:,:,i])
            print 'i:', i
            for it in range(n_iter):
                U = coder.transform(imgs_to_data(X, b.shape[2]))
                DU = np.dot(U, D)
                print 'DU:', DU.shape
                DU = data_to_imgs(DU, X.shape[:3])
                DU = np.squeeze(DU)
                print 'DU imgs:', DU.shape
                print 'X shape:', X.shape
                # Force the measured k-space data to persist
                for i in range(Nt):
                    f0 = b[:,:,i]
                    print 'f0:', f0.shape
                    f = fft_transform(DU[:,:,i])
                    print 'f:', f.shape
                    f[masks[:,:,i]] = f0[masks[:,:,i]]
                    X[:,:,i] = np.abs(ifft_transform(f))
                fval = np.sum((X-DU)**2)
                errs[it] = fval
                if verbose:
                    print it, ':', fval
        return X, DU, U, errs
    
    X = np.zeros(b.shape)
    for i in range(b.shape[3]):
        xtmp, dutmp, utmp, errs = reconstruct(b[:,:,:,i], masks[:,:,:,i], D, p_transform_alpha, p_transform_n_nonzero_coefs, p_transform_algorithm,
                                              n_iter, n_jobs, verbose)
        X[:,:,:,i] = xtmp
    return X, utmp, errs

def test_run(return_info=False):   
    # Parameters
    n_components=60
    undersampling = 0.5
    train_amount = 0.8
    
    # Training parameters
    batch_size = 1000
    n_iter = 250
    
    # Algorithms
    fit_algorithm = 'lars'
    transform_algorithm = 'omp'
    
    # Regularization paramters
    alpha_train = 0.2
    
    #Output
    verbose = 2
    
    # Read
    imgs = sp.io.loadmat('ismrm_ssa_imgs.mat')
    imgs = np.float64(imgs['imgs'])
    imgs /= 2000.
    
    # Preprocess
    imgs_train, imgs_test_ref = get_imgs(imgs, train_amount=train_amount)
      
    # Train
    D, init = learn_dictionary(imgs_train, n_components, alpha_train, fit_algorithm, n_iter,
                         batch_size, verbose=verbose)
    # Test
    k_test = fft_transform(imgs_test_ref)
    b, masks = mask_imgs(k_test, method='uniform', full_center=False, k=8, 
                          undersampling=undersampling, n_gauss=100, variance=30, 
                          return_masks=True)
    imgs_test = ifft_transform(b)
    
    recs, utemp, errs = reconstruct_dataset(b[:,:,:,:2], masks, D, None, 5, transform_algorithm, 20, n_jobs=1, verbose=1)
    
    # Output chain
    plt.figure(figsize=(10,10))
    plt.subplot(1,2,1)
    plt.imshow(D)
    plt.subplot(1,2,2)
    plt.imshow(abs(utemp[:10,:]))
    
    # Error vs iteration
    plt.figure(figsize=(10,10))
    plt.plot(errs)
    
    # spatial images
    plt.figure(figsize=(10,10))
    plt.subplot(1,3,1)
    plt.imshow(imgs_test_ref[:,:,0,0])
    plt.title('ground')
    plt.subplot(1,3,2)
    plt.imshow(imgs_test[:,:,0,0])
    plt.title('test image')
    plt.subplot(1,3,3)
    plt.imshow(recs[:,:,0,0])
    plt.title('reconstruction')
    
    # Slice through time
    plt.figure(figsize=(10,10))
    plt.subplot(1,3,1)
    plt.imshow(imgs_test_ref[:,int(imgs_test_ref.shape[1]/2),:,0])
    plt.title("Ground")
    plt.xlabel('time')
    plt.ylabel('y')
    plt.subplot(1,3,2)
    plt.imshow(imgs_test[:,int(imgs_test.shape[1]/2),:,0])
    plt.title("Aliased")
    plt.xlabel('time')
    plt.ylabel('y')
    plt.subplot(1,3,3)
    plt.imshow(recs[:,int(recs.shape[1]/2),:,0])
    plt.title("Reconstruction")
    plt.xlabel('time')
    plt.ylabel('y')
    if return_info:
        return imgs_train, imgs_test, recs, D, init
    return

#==============================================================================
# main  algorithm
#==============================================================================

if __name__=='__main__':
    imgs_train, imgs_test, recs, D, init = test_run(return_info=True)