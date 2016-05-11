#!/usr/bin/env python
# -*- coding: utf-8 -*-
# P300 classifier mockup
# Marian Dovgialo
from __future__ import print_function
import numpy as np 
import scipy.stats
import scipy.signal as ss
from sklearn.externals import joblib
try:
    from sklearn.lda import LDA as LinearDiscriminantAnalysis
except ImportError:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    
from collections import deque
from obci.interfaces.bci.abstract_classifier import AbstractClassifier
import pickle

LEARN_EVERY = 20 # relearn every # provided targets

def _tags_to_array(tags):
    '''returns 3D numpy array from OBCI smart tags
    epochs x channels x time'''
    min_length = min(i.get_samples().shape[1] for i in tags)
# really don't like this, but epochs generated by smart tags can vary in length by 1 sample
    array = np.dstack([i.get_samples()[:,:min_length] for i in tags])
    return np.rollaxis(array,2)

def _remove_artifact_epochs(data, labels):
    ''' data - 3D numpy array epoch x channels x time,
    labels - list of epochs labels
    returns clean data and labels
    Provisional version'''
    mask = np.ones(len(data), dtype = bool)
    for id, i in enumerate(data):
        if np.max(np.abs(i-i[:,0][:, None]))>2000:
            mask[id]=False
    newlabels = [l for l, m in zip(labels, mask) if m]
    newdata = data[mask]
    return newdata, newlabels
        

def _feature_extraction(data, Fs, bas=-0.1, window=0.4, targetFs=34):
    '''data - 3D numpy array epoch x channels x time,
    returns spatiotemporal features array epoch x features'''
    features = []
    for epoch in data:
        features.append(_feature_extraction_singular(epoch, Fs, bas,
                                                    window, targetFs))
    return np.array(features)
        
    

def _feature_extraction_singular(epoch, Fs, bas=-0.1, 
                                window = 0.5,
                                targetFs=30,):
    '''performs feature extraction on epoch (array channels x time),
    Args:
        Fs: sampling in Hz
        bas: baseline in seconds
        targetFs: target sampling in Hz (will be approximated)
        window: timewindow after baseline to select in seconds
        
    Returns: 1D array downsampled, len = downsampled samples x channels
    epoch minus mean of baseline, downsampled by factor int(Fs/targetFs)
    samples used - from end of baseline to window timepoint
     '''
    mean = np.mean(epoch[:, :-bas*Fs], axis=1) 
    decimation_factor = int(1.0*Fs/targetFs) 
    selected = epoch[:,-bas*Fs:(-bas+window)*Fs]-mean[:, None]
    features =  ss.decimate(selected, decimation_factor, axis=1, ftype='fir')
    return features.flatten()
    
def _feature_reduction_mask(ft, labels, mode):
    ''' ft - features 2d array nsamples x nfeatures
    labels - nsamples array of labels 0, 1,
    mode - 'auto', int
    returns - features mask'''
    tscore, p = scipy.stats.ttest_ind(ft[labels==1], ft[labels==0])
    if mode == 'auto':
        mask = p<0.05
        if mask.sum()<1:
            raise Exception('Feature reduction produced zero usable features')
    elif isinstance(mode, int):
        mask_ind = np.argsort(p)[-mode:]
        mask = np.zeros_like(p, dtype=bool)
        mask[mask_ind] = True
    return mask
    


class P300EasyClassifier(AbstractClassifier):
    '''Easy and modular P300 classifier
    attributes"
    '''
    
    def __init__(self, clf=None,
                    targetFs=24):
        '''Args:
               clf: scikit learn type classifier, None if you want to
                    use standard LDA with shrinkage
               targetFS: target sampling rate after downsampling for
                            feature extraction
        '''
        if clf is None:
            self.clf = LinearDiscriminantAnalysis(solver = 'lsqr', shrinkage='auto')
        self.targetFs = targetFs
        self.learning_buffor_features = list()
        self.learning_buffor_classes = list()
        
        
        
    def classify(self, features):
        '''
        Args:
            features - 1D vector of extracted features
        '''
        #probability of target
        return self.clf.predict_proba(features.reshape(1, -1))[0][1] 
        
    def learn(self, chunk, target):
        ''' 
        For online learning thread
        
        Args:
            chunk: numpy 1D features array
            target: name of the class
        '''
        if target == 'target':
            self.learning_buffor_classes.append(1)
        else: 
            self.learning_buffor_classes.append(0)
        self.learning_buffor_features.append(chunk)
        targets_count = sum(self.learning_buffor_classes)
        nontargets_count = sum(i==0 for i in self.learning_buffor_classes)
        enough = (targets_count>2 and nontargets_count>2)
        if sum(self.learning_buffor_classes)%LEARN_EVERY == 0 and enough:
            print('Classifier: fitting clf with new data')
            self.clf.fit(
                            self.learning_buffor_features,
                            self.learning_buffor_classes,
                        )
            score = self.clf.score(self.learning_buffor_features,
                                    self.learning_buffor_classes)
            print ('Classifier: Test on training set: {}'.format(score))
            
            
            
    def calibrate(self, targets, nontargets, bas=-0.1, window=0.4, Fs=None):
        '''Offline learning function
        
        Args:
            
            targets, nontargets: 3D arrays (epoch x channel x time)
                                or list of OBCI smart tags. 
                                If arrays - need to provide Fs
                                (sampling frequency) in Hz
            bas: baseline in seconds(negative), in other words start 
                 offset
            window: seconds after event to consider in classification
            Fs: needed if 3D numpy array is provided
        '''
    
        if Fs is None:
            Fs = float(targets[0].get_param('sampling_frequency'))
            target_data = _tags_to_array(targets)
            nontarget_data = _tags_to_array(nontargets)
        data = np.vstack((target_data, nontarget_data))
        self.epoch_l = data.shape[2]
        labels = np.zeros(len(data))
        labels[:len(target_data)] = 1
        data, labels = _remove_artifact_epochs(data, labels)
        features = _feature_extraction(data, Fs, bas, window, self.targetFs)
        self.clf.fit(features, labels)
        # building a list of features
        #will be saved and can be extended in online learning later
        self.learning_buffor_classes=[i for i in labels]
        self.learning_buffor_features=[i for i in features]
        return self.clf.score(features, labels)