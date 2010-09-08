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
#    ADVISED OF THE POSSIBILITY OF SUCH 
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4 import QtCore, QtGui

class IlastikTabWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabWidget.__init__(self, parent)
        self.tabDict = {}
        self.currentTabNumber = 0
        if parent:     
            self.connect(parent,QtCore.SIGNAL("orientationChanged(Qt::Orientation)"),self.orientationEvent)

    def orientationEvent(self, orientation):
        if orientation == QtCore.Qt.Horizontal: 
            self.setTabPosition(self.North)            
        if orientation == QtCore.Qt.Vertical: 
            self.setTabPosition(self.West)
        for tab in self.tabDict.values():
            lo = tab.layout()
            if orientation == 1:
                orientation = 0
            lo.setDirection(lo.Direction(orientation))
          
    def moveEvent(self, event):
        QtGui.QTabWidget.moveEvent(self, event)
    
    def addTab(self, page, tabName):
        self.tabDict[tabName] = page
        QtGui.QTabWidget.addTab(self, page, tabName)  
        
#<<<<<<< HEAD
#    def makeTab(self):
#        self.tabs = RibbonTabContainer(self.position)
#	stretched = False
#        for rib in self.entries:
#            item = rib.type(rib)
#	    if rib.type is RibbonStretch:
#		    stretched = True
#            self.tabs.addItem(item)
#	if not stretched:
#		self.tabs.layout().addStretch()
#        return self.tabs   
#
#def createRibbons():
#    RibbonGroupObjects = {}
#    RibbonGroupObjects["Projects"] = RibbonEntryGroup("Projects", 0)    
#    RibbonGroupObjects["Classification"] = RibbonEntryGroup("Classification", 2)   
#    RibbonGroupObjects["Segmentation"] = RibbonEntryGroup("Segmentation", 3)
#    RibbonGroupObjects["Object Processing"] = RibbonEntryGroup("Object Processing", 4)
#    RibbonGroupObjects["Automate"] = RibbonEntryGroup("Automate", 5)
#    RibbonGroupObjects["Help"] = RibbonEntryGroup("Help", 6)
#
#    #RibbonGroupObjects["Export"] = RibbonEntryGroup("Export", 3)
#    
#    RibbonGroupObjects["Projects"].append(RibbonEntry("New", ilastikIcons.New ,"New"))
#    RibbonGroupObjects["Projects"].append(RibbonEntry("Open", ilastikIcons.Open ,"Open"))
#    RibbonGroupObjects["Projects"].append(RibbonEntry("Save", ilastikIcons.Save,"Save"))
#    RibbonGroupObjects["Projects"].append(RibbonEntry("Edit", ilastikIcons.Edit ,"Edit"))
#    RibbonGroupObjects["Projects"].append(RibbonEntry("", None, "", type=RibbonStretch))
#    RibbonGroupObjects["Projects"].append(RibbonEntry("Options", ilastikIcons.Edit ,"Options"))
#    
#    RibbonGroupObjects["Classification"].append(RibbonEntry("Select Features", ilastikIcons.Select ,"Select and compute features"))
#    
#    RibbonGroupObjects["Classification"].append(RibbonEntry("Start Live Prediction", ilastikIcons.Play ,"Interactive prediction of visible image parts while drawing etc.",type=RibbonToggleButtonItem))
#    RibbonGroupObjects["Classification"].append(RibbonEntry("Train and Predict", ilastikIcons.System ,"Train Classifier and predict the whole image"))
#    RibbonGroupObjects["Classification"].append(RibbonEntry("", None, "", type=RibbonStretch))
#
#    RibbonGroupObjects["Classification"].append(RibbonEntry("Export Classifier", ilastikIcons.System ,"Save current classifier and its feature settings"))
#    RibbonGroupObjects["Classification"].append(RibbonEntry("Classifier Options", ilastikIcons.System ,"Select a classifier and change its settings"))
#
#
#
#
#    RibbonGroupObjects["Segmentation"].append(RibbonEntry("Choose Weights", ilastikIcons.System ,"Choose the edge weights for the segmentation task"))
#    RibbonGroupObjects["Segmentation"].append(RibbonEntry("Segment", ilastikIcons.Play ,"Segment the image into foreground/background"))
#    RibbonGroupObjects["Segmentation"].append(RibbonEntry("", None, "", type=RibbonStretch))
#    RibbonGroupObjects["Segmentation"].append(RibbonEntry("Change Segmentation", ilastikIcons.System ,"Select a segmentation plugin and change settings"))
#
#    RibbonGroupObjects["Object Processing"].append(RibbonEntry("Select Input", ilastikIcons.Select, "Select the input layer"))
#    RibbonGroupObjects["Object Processing"].append(RibbonEntry("CC", ilastikIcons.System, "Find connected components in the data"))
#
#    RibbonGroupObjects["Automate"].append(RibbonEntry("Batchprocess", ilastikIcons.Play ,"Batchpredict files in a directory with the currently trained classifier"))
#
#    RibbonGroupObjects["Help"].append(RibbonEntry("Shortcuts", ilastikIcons.System ,"Shortcuts"))
#
#    #RibbonGroupObjects["Segmentation"].append(RibbonEntry("Segment", ilastikIcons.Play ,"Segment Foreground/Background"))
#    #RibbonGroupObjects["Segmentation"].append(RibbonEntry("BorderSegment", ilastikIcons.Play ,"Segment Foreground/Background with Border"))
#
#    #RibbonGroupObjects["Export"].append(RibbonEntry("Export", ilastikIcons.System  ,"Export"))
#    return RibbonGroupObjects   
#=======
    def getTab(self, tabName):
        return self.tabDict[tabName] 
                   
        
        
