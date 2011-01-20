#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

import numpy, vigra, os, sys
import traceback

import segmentors

from PyQt4 import QtCore
from ilastik.core import jobMachine

   
def LocallyDominantSegmentation(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)

    res = numpy.zeros( propmap.shape, dtype=numpy.float32)
    for k in range(propmap.shape[-1]):
        #TODO: time !!!
        if propmap.shape[1] == 1:
            res[0,0,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,0,:,:,k], sigma)
        else:
            res[0,:,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,:,:,:,k], sigma)

    return  numpy.argmax(res, axis=len(propmap.shape)-1) + 1


def LocallyDominantSegmentation2D(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)
        
    return  numpy.argmax(propmap, axis=len(propmap.shape)-1) + 1

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 


class ListOfNDArraysAsNDArray:
    """
    Helper class that behaves like an ndarray, but consists of an array of ndarrays
    """

    def __init__(self, ndarrays):
        self.ndarrays = ndarrays
        self.dtype = ndarrays[0].dtype
        self.shape = (len(ndarrays),) + ndarrays[0].shape
        for idx, it in enumerate(ndarrays):
            if it.dtype != self.dtype or self.shape[1:] != it.shape:
                print "########### ERROR ListOfNDArraysAsNDArray all array items should have same dtype and shape (array: ", self.dtype, self.shape, " item : ",it.dtype, it.shape , ")"

    def __getitem__(self, key):
        return self.ndarrays[key[0]][tuple(key[1:])]

    def __setitem__(self, key, data):
        self.ndarrays[key[0]][tuple(key[1:])] = data
        print "##########ERROR ######### : ListOfNDArraysAsNDArray not implemented"



class SegmentationThread(QtCore.QThread):
    def __init__(self, dataMgr, image, segmentor = None, segmentorOptions = None):
        QtCore.QThread.__init__(self, None)
        self.dataItem = image
        self.dataMgr = dataMgr
        if segmentor == None:
            segmentor = dataMgr.Interactive_Segmentation.segmentorClasses[0]            
        self.count = 0
        self.numberOfJobs = self.dataItem._dataVol._data.shape[0]
        self.stopped = False
        self.segmentor = segmentor
        self.segmentorOptions = segmentorOptions
        self.jobMachine = jobMachine.JobMachine()

    def segment(self, i, data, labelVolume, labelValues, labelIndices):
        self.result[i] = self.segmentor.segment(labelVolume, labelValues, labelIndices)
        self.count += 1

    def run(self):
        self.dataMgr.featureLock.acquire()

        try:
            self.result = range(0,self.dataItem._dataVol._data.shape[0])
            jobs = []
            for i in range(self.dataItem._dataVol._data.shape[0]):
                labels, indices = self.dataItem.Interactive_Segmentation.getSeeds()
                job = jobMachine.IlastikJob(SegmentationThread.segment, [self, i, self.dataItem._dataVol._data[i,:,:,:,:], self.dataItem.Interactive_Segmentation.seeds._data[i,:,:,:], labels, indices])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.result = ListOfNDArraysAsNDArray(self.result)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()