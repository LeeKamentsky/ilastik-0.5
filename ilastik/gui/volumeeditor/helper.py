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

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignal

from ilastik.core.volume import DataAccessor

import numpy
import threading
import time

from collections import deque


########################################################################
class ImageWithProperties(DataAccessor):
    """adds some nice properties to the image"""
    
    def __init__(self, dataAccessor):
        DataAccessor.__init__(self, dataAccessor)
    
    def is2D(self):
        return self.shape[1] == 1
    
    def is3D(self):
        return self.shape[1] > 1


class InteractionLogger():
    #singleton pattern
    _instance = None
    _interactionLog = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(InteractionLogger, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        InteractionLogger._interactionLog = []
    
    @staticmethod
    def log(logEntry):
        if InteractionLogger._interactionLog != None:
            InteractionLogger._interactionLog.append(logEntry)
        

    

class ViewManager(QtCore.QObject):
    sliceChanged = pyqtSignal(int,int)
    
    def __init__(self, image, time = 0, position = [0, 0, 0], channel = 0):
        QtCore.QObject.__init__(self)
        self._image = image
        self._time = time
        self._position = position
        self._channel = channel
        
    def setTime(self, time):
        if self._time != time:
            self._time = time
            self.__updated()
    
    @property    
    def time(self):
        return self._time
        
    def setSlice(self, num, axis):
        if self._position[axis] != num:
            self._position[axis] = num
            self.sliceChanged.emit(num, axis)
    
    def changeSliceDelta(self, axis, delta):
        self.setSlice(self.position[axis] + delta, axis)
    
    @property        
    def slicePosition(self):
        return self._position

    @property
    def position(self):
        return self._position
    
    def setChannel(self, channel):
        self._channel = channel

    @property
    def channel(self):
        return self._channel
    
    def getVisibleState(self):
        return [self._time, self._position[0], self._position[1], self._position[2], self._channel]
    
    def __updated(self):
        #self.emit(QtCore.SIGNAL('viewChanged(ViewManager)'), self) #FIXME
        pass


#*******************************************************************************
# P a t c h A c c e s s o r                                                    *
#*******************************************************************************

class PatchAccessor():
    def __init__(self, size_x, size_y, blockSize = 128):
        self._blockSize = blockSize
        self.size_x = size_x
        self.size_y = size_y

        self._cX = int(numpy.ceil(1.0 * size_x / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = size_x % self._blockSize
        if self._cXend < self._blockSize / 3 and self._cXend != 0 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0

        self._cY = int(numpy.ceil(1.0 * size_y / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = size_y % self._blockSize
        if self._cYend < self._blockSize / 3 and self._cYend != 0 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0


        self.patchCount = self._cX * self._cY


    def getPatchBounds(self, blockNum, overlap = 0):
        #z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX

        startx = max(0, x*self._blockSize - overlap)
        endx = min(self.size_x, (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self.size_x

        starty = max(0, y*self._blockSize - overlap)
        endy = min(self.size_y, (y+1)*self._blockSize + overlap)
        if y+1 >= self._cY:
            endy = self.size_y


        return [startx,endx,starty,endy]

    def getPatchesForRect(self,startx,starty,endx,endy):
        sx = int(numpy.floor(1.0 * startx / self._blockSize))
        ex = int(numpy.ceil(1.0 * endx / self._blockSize))
        sy = int(numpy.floor(1.0 * starty / self._blockSize))
        ey = int(numpy.ceil(1.0 * endy / self._blockSize))
        
        
        if ey > self._cY:
            ey = self._cY

        if ex > self._cX :
            ex = self._cX

        nums = []
        for y in range(sy,ey):
            nums += range(y*self._cX+sx,y*self._cX+ex)
        
        return nums

        
    

#abstract base class for undo redo stuff
#*******************************************************************************
# S t a t e                                                                    *
#*******************************************************************************

class State():
    def __init__(self):
        pass

    def restore(self):
        pass


#*******************************************************************************
# L a b e l S t a t e                                                          *
#*******************************************************************************

class LabelState(State):
    def __init__(self, title, axis, num, offsets, shape, timeAxis, volumeEditor, erasing, labels, labelNumber):
        self.title = title
        self.time = timeAxis
        self.num = num
        self.offsets = offsets
        self.axis = axis
        self.erasing = erasing
        self.labelNumber = labelNumber
        self.labels = labels
        self.clock = time.clock()
        self.dataBefore = volumeEditor.labelWidget.overlayItem.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
        
    def restore(self, volumeEditor):
        temp = volumeEditor.labelWidget.overlayItem.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
        restore  = numpy.where(self.labels > 0, self.dataBefore, 0)
        stuff = numpy.where(self.labels > 0, self.dataBefore + 1, 0)
        erase = numpy.where(stuff == 1, 1, 0)
        self.dataBefore = temp
        #volumeEditor.labels._data.setSubSlice(self.offsets, temp, self.num, self.axis, self.time, 0)
        volumeEditor.setLabels(self.offsets, self.axis, self.num, restore, False)
        volumeEditor.setLabels(self.offsets, self.axis, self.num, erase, True)
        if volumeEditor.sliceSelectors[self.axis].value() != self.num:
            volumeEditor.sliceSelectors[self.axis].setValue(self.num)
        else:
            #volumeEditor.repaint()
            #repainting is already done automatically by the setLabels function
            pass
        self.erasing = not(self.erasing)          



#*******************************************************************************
# H i s t o r y M a n a g e r                                                  *
#*******************************************************************************

class HistoryManager(QtCore.QObject):
    def __init__(self, parent, maxSize = 3000):
        QtCore.QObject.__init__(self)
        self.volumeEditor = parent
        self.maxSize = maxSize
        self._history = []
        self.current = -1

    def append(self, state):
        if self.current + 1 < len(self._history):
            self._history = self._history[0:self.current+1]
        self._history.append(state)

        if len(self._history) > self.maxSize:
            self._history = self._history[len(self._history)-self.maxSize:len(self._history)]
        
        self.current = len(self._history) - 1

    def undo(self):
        if self.current >= 0:
            self._history[self.current].restore(self.volumeEditor)
            self.current -= 1

    def redo(self):
        if self.current < len(self._history) - 1:
            self._history[self.current + 1].restore(self.volumeEditor)
            self.current += 1
            
    def serialize(self, grp, name='_history'):
        histGrp = grp.create_group(name)
        for i, hist in enumerate(self._history):
            histItemGrp = histGrp.create_group('%04d'%i)
            histItemGrp.create_dataset('labels',data=hist.labels)
            histItemGrp.create_dataset('axis',data=hist.axis)
            histItemGrp.create_dataset('slice',data=hist.num)
            histItemGrp.create_dataset('labelNumber',data=hist.labelNumber)
            histItemGrp.create_dataset('offsets',data=hist.offsets)
            histItemGrp.create_dataset('time',data=hist.time)
            histItemGrp.create_dataset('erasing',data=hist.erasing)
            histItemGrp.create_dataset('clock',data=hist.clock)


    def removeLabel(self, number):
        tobedeleted = []
        for index, item in enumerate(self._history):
            if item.labelNumber != number:
                item.dataBefore = numpy.where(item.dataBefore == number, 0, item.dataBefore)
                item.dataBefore = numpy.where(item.dataBefore > number, item.dataBefore - 1, item.dataBefore)
                item.labels = numpy.where(item.labels == number, 0, item.labels)
                item.labels = numpy.where(item.labels > number, item.labels - 1, item.labels)
            else:
                #if item.erasing == False:
                    #item.restore(self.volumeEditor)
                tobedeleted.append(index - len(tobedeleted))
                if index <= self.current:
                    self.current -= 1

        for val in tobedeleted:
            it = self._history[val]
            self._history.__delitem__(val)
            del it
            
    def clear(self):
        self._history = []

#*******************************************************************************
# V o l u m e U p d a t e                                                      *
#*******************************************************************************

class VolumeUpdate():
    def __init__(self, data, offsets, sizes, erasing):
        self.offsets = offsets
        self._data = data
        self.sizes = sizes
        self.erasing = erasing
    
    def applyTo(self, dataAcc):
        offsets = self.offsets
        sizes = self.sizes
        #TODO: move part of function into DataAccessor class !! e.g. setSubVolume or something
        tempData = dataAcc[offsets[0]:offsets[0]+sizes[0],\
                           offsets[1]:offsets[1]+sizes[1],\
                           offsets[2]:offsets[2]+sizes[2],\
                           offsets[3]:offsets[3]+sizes[3],\
                           offsets[4]:offsets[4]+sizes[4]].copy()

        if self.erasing == True:
            tempData = numpy.where(self._data > 0, 0, tempData)
        else:
            tempData = numpy.where(self._data > 0, self._data, tempData)
        
        dataAcc[offsets[0]:offsets[0]+sizes[0],\
                offsets[1]:offsets[1]+sizes[1],\
                offsets[2]:offsets[2]+sizes[2],\
                offsets[3]:offsets[3]+sizes[3],\
                offsets[4]:offsets[4]+sizes[4]] = tempData  




#*******************************************************************************
# D u m m y L a b e l W i d g e t                                              *
#*******************************************************************************

class DummyLabelWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.volumeLabels = None
        
    def currentItem(self):
        return None

#*******************************************************************************
# D u m m y O v e r l a y L i s t W i d g e t                                  *
#*******************************************************************************

class DummyOverlayListWidget(QtGui.QWidget):
    def __init__(self,  parent):
        QtGui.QWidget.__init__(self)
        self.volumeEditor = parent
        self.overlays = []

#*******************************************************************************
# D r a w M a n a g e r                                                        *
#*******************************************************************************

class DrawManager(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.shape = None
        self.brushSize = 3
        #self.initBoundingBox()
        self.penVis = QtGui.QPen(QtCore.Qt.white, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDraw = QtGui.QPen(QtCore.Qt.white, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDraw.setColor(QtCore.Qt.white)
        self.pos = None
        self.erasing = False
        self.lines = []
        self.scene = QtGui.QGraphicsScene()
        
        self.color = QtCore.Qt.white

    def copy(self):
        """
        make a shallow copy of DrawManager - needed for python 2.5 compatibility
        """
        cp = DrawManager()
        cp.shape = self.shape
        cp.brushSize = self.brushSize
        cp.penVis = self.penVis
        cp.penDraw = self.penDraw
        cp.pos = self.pos
        cp.erasing = self.erasing
        cp.lines = self.lines
        cp.scene = self.scene
        cp.imageScenes = self.imageScenes
        cp.color = self.color
        return cp

    def initBoundingBox(self):
        self.leftMost = self.shape[0]
        self.rightMost = 0
        self.topMost = self.shape[1]
        self.bottomMost = 0

    def growBoundingBox(self):
        self.leftMost = max(0,self.leftMost - self.brushSize -1)
        self.topMost = max(0,self.topMost - self.brushSize -1 )
        self.rightMost = min(self.shape[0],self.rightMost + self.brushSize + 1)
        self.bottomMost = min(self.shape[1],self.bottomMost + self.brushSize + 1)

    def toggleErase(self):
        self.erasing = not(self.erasing)

    def setErasing(self):
        self.erasing = True
        self.emit(QtCore.SIGNAL('brushColorChanged(int)'), QtGui.QColor("black") )
    
    def disableErasing(self):
        self.erasing = False
        self.emit(QtCore.SIGNAL('brushColorChanged(int)'), self.color())

    def setBrushSize(self, size):      
        self.brushSize = size
        self.penVis.setWidth(size)
        self.penDraw.setWidth(size)
        self.emit(QtCore.SIGNAL('brushSizeChanged(int)'), self.brushSize)
        
    def getBrushSize(self):
        return self.brushSize
    
    def brushSmaller(self):
        b = self.brushSize
        if b > 1:
            self.setBrushSize(b-1)
        
    def brushBigger(self):
        b = self.brushSize
        if self.brushSize < 61:
            self.drawManager.setBrushSize(b+1)
        
    def setBrushColor(self, color):
        self.color = color
        self.penVis.setColor(color)
        self.emit(QtCore.SIGNAL('brushColorChanged(int)'), self.color)
        
    def beginDraw(self, pos, shape):
        self.shape = shape
        self.initBoundingBox()
        self.scene.clear()
        if self.erasing == True:
            self.penVis.setColor(QtCore.Qt.black)
        else:
            self.penVis.setColor(self.color)
        self.pos = QtCore.QPointF(pos.x()+0.0001, pos.y()+0.0001)
        
        line = self.moveTo(pos)
        return line

    def endDraw(self, pos):
        self.moveTo(pos)
        self.growBoundingBox()

        tempi = QtGui.QImage(self.rightMost - self.leftMost, self.bottomMost - self.topMost, QtGui.QImage.Format_ARGB32_Premultiplied) #TODO: format
        tempi.fill(0)
        painter = QtGui.QPainter(tempi)
        
        self.scene.render(painter, QtCore.QRectF(0,0, self.rightMost - self.leftMost, self.bottomMost - self.topMost),
            QtCore.QRectF(self.leftMost, self.topMost, self.rightMost - self.leftMost, self.bottomMost - self.topMost))
        
        oldLeft = self.leftMost
        oldTop = self.topMost
        return (oldLeft, oldTop, tempi) #TODO: hackish, probably return a class ??

    def dumpDraw(self, pos):
        res = self.endDraw(pos)
        self.beginDraw(pos, self.shape)
        return res


    def moveTo(self, pos):    
        lineVis = QtGui.QGraphicsLineItem(self.pos.x(), self.pos.y(),pos.x(), pos.y())
        lineVis.setPen(self.penVis)
        
        line = QtGui.QGraphicsLineItem(self.pos.x(), self.pos.y(),pos.x(), pos.y())
        line.setPen(self.penDraw)
        self.scene.addItem(line)

        self.pos = pos
        x = pos.x()
        y = pos.y()
        #update bounding Box :
        if x > self.rightMost:
            self.rightMost = x
        if x < self.leftMost:
            self.leftMost = x
        if y > self.bottomMost:
            self.bottomMost = y
        if y < self.topMost:
            self.topMost = y
        return lineVis

#*******************************************************************************
# I m a g e S a v e T h r e a d                                                *
#*******************************************************************************

class ImageSaveThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, None)
        self.ve = parent
        self.queue = deque()
        self.imageSaved = threading.Event()
        self.imageSaved.clear()
        self.imagePending = threading.Event()
        self.imagePending.clear()
        self.stopped = False
        self.previousSlice = None
        
    def run(self):
        while not self.stopped:
            self.imagePending.wait()
            while len(self.queue)>0:
                stuff = self.queue.pop()
                if stuff is not None:
                    filename, timeOffset, sliceOffset, format = stuff
                    if self.ve.image.shape[1]>1:
                        axis = 2
                        self.previousSlice = self.ve.sliceSelectors[axis].value()
                        for t in range(self.ve.image.shape[0]):
                            for z in range(self.ve.image.shape[3]):                   
                                self.filename = filename
                                if (self.ve.image.shape[0]>1):
                                    self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                                self.filename = self.filename + ("_z%05i" %(z+sliceOffset))
                                self.filename = self.filename + "." + format
                        
                                #only change the z slice display
                                self.ve.imageScenes[axis].thread.queue.clear()
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
                                self.ve.updateTimeSliceForSaving(t, z, axis)
                                
                                
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
        
                                self.ve.imageScenes[axis].saveSlice(self.filename)
                    else:
                        axis = 0
                        for t in range(self.ve.image.shape[0]):                 
                            self.filename = filename
                            if (self.ve.image.shape[0]>1):
                                self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                            self.filename = self.filename + "." + format
                            self.ve.imageScenes[axis].thread.queue.clear()
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.updateTimeSliceForSaving(t, self.ve.viewManager.slicePosition[0], axis)                              
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.imageScenes[axis].saveSlice(self.filename)
            self.imageSaved.set()
            self.imagePending.clear()
            if self.previousSlice is not None:
                self.ve.sliceSelectors[axis].setValue(self.previousSlice)
                self.previousSlice = None


