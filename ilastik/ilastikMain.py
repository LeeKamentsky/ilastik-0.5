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


from OpenGL.GL import *
try:
    from OpenGL.GLX import *
    XInitThreads()
except:
    pass

import sys
import os

#force QT4 toolkit for the enthought traits UI
os.environ['ETS_TOOLKIT'] = 'qt4'

import vigra
import h5py

import threading
import traceback
import numpy
import time


from ilastik.gui.segmentationWeightSelectionDlg import SegmentationWeightSelectionDlg
from ilastik.core import version, dataMgr, projectMgr,  segmentationMgr, activeLearning, onlineClassifcator, dataImpex, connectedComponentsMgr
from ilastik.core.modules.Classification import featureMgr, classificationMgr
from ilastik.gui import ctrlRibbon, stackloader, fileloader, batchProcess
from ilastik.gui.featureDlg import FeatureDlg

import copy

from Queue import Queue as queue
from collections import deque

import ilastik.gui
from ilastik.core import projectMgr, segmentationMgr, activeLearning
from ilastik.core.modules.Classification import featureMgr, classificationMgr
from ilastik.gui import ctrlRibbon
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
import ilastik.core.jobMachine


from PyQt4 import QtCore, QtGui, uic, QtOpenGL
import getopt

from ilastik.gui import volumeeditor as ve

# Please no import *
from ilastik.gui.shortcutmanager import *

from ilastik.gui.labelWidget import LabelListWidget
from ilastik.gui.seedWidget import SeedListWidget
from ilastik.gui.objectWidget import ObjectListWidget
from ilastik.gui.backgroundWidget import BackgroundWidget
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.fullScreen = False
        self.setGeometry(50, 50, 800, 600)
        
        #self.setWindowTitle("Ilastik rev: " + version.getIlastikVersion())
        self.setWindowIcon(QtGui.QIcon(ilastikIcons.Python))

        self.activeImageLock = threading.Semaphore(1) #prevent chaning of _activeImageNumber during thread stuff
        
        self.previousTabText = ""
        
        self.labelWidget = None
        self._activeImageNumber = 0
        self._activeImage = None
        
        self.createRibbons()
        self.initImageWindows()

        self.createFeatures()
              
        self.classificationProcess = None
        self.classificationOnline = None
        
        self.featureCache = None
        self.opengl = None
        project = None        
        
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ["help", "render=", "project=", "featureCache="])
            for o, a in opts:
                if o == "-v":
                    verbose = True
                elif o in ("--help"):
                    print '%30s  %s' % ("--help", "print help on command line options")
                    print '%30s  %s' % ("--render=[s,s_gl,gl_gl]", "chose slice renderer:")
                    print '%30s  %s' % ("s", "software without 3d overview")
                    print '%30s  %s' % ("s_gl", "software with opengl 3d overview")
                    print '%30s  %s' % ("gl_gl", "opengl with opengl 3d overview")
                    print '%30s  %s' % ("--project=[filename]", "open specified project file")
                    print '%30s  %s' % ("--featureCache=[filename]", "use specified file for caching of features")
                elif o in ("--render"):
                    if a == 's':
                        self.opengl = False
                        self.openglOverview = False
                    elif a == 's_gl':
                        self.opengl = False
                        self.openglOverview = True
                    elif a == 'gl_gl':
                        self.opengl = True
                        self.openglOverview = True
                    else:
                        print "invalid --render option"
                        sys.exit()                                         
                elif o in ("--project"):
                    project = a
                elif o in ("--featureCache"):
                    self.featureCache = h5py.File(a, 'w')
                else:
                    assert False, "unhandled option"
            
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
                

        if self.opengl == None:   #no command line option for opengl was given, ask user interactively
            #test for opengl version
            gl2 = False
            w = QtOpenGL.QGLWidget()
            w.setVisible(False)
            w.makeCurrent()
            gl_version =  glGetString(GL_VERSION)
            if gl_version is None:
                gl_version = '0'
            del w

            help_text = "Normally the default option should work for you\nhowever, in some cases it might be beneficial to try to use another rendering method:"
            if int(gl_version[0]) >= 2:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', help_text, ['OpenGL + OpenGL Overview', 'Software + OpenGL Overview'], 0, False)
            elif int(gl_version[0]) > 0:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', help_text, ['Software + OpenGL Overview'], 0, False)
            else:
                dl = []
                dl.append("")
                
            self.opengl = False
            self.openglOverview = False
            if dl[0] == "OpenGL + OpenGL Overview":
                self.opengl = True
                self.openglOverview = True
            elif dl[0] == "Software + OpenGL Overview":
                self.opengl = False
                self.openglOverview = True

        self.project = None
        if project != None:
            self.project = projectMgr.Project.loadFromDisk(project, self.featureCache)
            self.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
            self._activeImageNumber = 0
            self.projectModified()
        
        self.shortcutSave = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.saveProject, self.saveProject) 
        self.shortcutFullscreen = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+F"), self, self.showFullscreen, self.showFullscreen) 
    
    def showFullscreen(self):
        if self.fullScreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.fullScreen = not self.fullScreen
                
    def updateFileSelector(self):
        self.fileSelectorList.blockSignals(True)
        self.fileSelectorList.clear()
        self.fileSelectorList.blockSignals(False)
        for item in self.project.dataMgr:
            self.fileSelectorList.addItem(item._name)
    
    def changeImage(self, number):
        self.activeImageLock.acquire()
        QtCore.QCoreApplication.processEvents()
        if hasattr(self, "classificationInteractive"):
            #self.labelWidget.disconnect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
            self.classificationInteractive.stop()
            del self.classificationInteractive
            self.classificationInteractive = True
        if self.labelWidget is not None:
            self.labelWidget._history.volumeEditor = None


        
        self.destroyImageWindows()
        
        self._activeImageNumber = number
        self._activeImage = self.project.dataMgr[number]
        
        self.project.dataMgr._activeImageNumber = number
        
        self.createImageWindows( self.project.dataMgr[number]._dataVol)
        
        self.labelWidget.repaint() #for overlays
        self.activeImageLock.release()
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive = ClassificationInteractive(self)
            #self.labelWidget.connect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
            self.classificationInteractive.updateThreadQueues()
        # Notify tabs
        self.ribbon.widget(self.ribbon.currentIndex()).on_imageChanged()
            
    def historyUndo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyUndo
        
    def historyRedo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyRedo
    
    def createRibbons(self):                     
        from ilastik.gui.ribbons.standardRibbons import ProjectTab
        
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.IlastikTabWidget(self.ribbonToolbar)
        
        self.ribbonToolbar.addWidget(self.ribbon)
        
        self.ribbonsTabs = IlastikTabBase.__subclasses__()

        for tab in self.ribbonsTabs:
            print "Adding tab ", tab.name
            self.ribbon.addTab(tab(self), tab.name)
        
   
        self.fileSelectorList = QtGui.QComboBox()
        widget = QtGui.QWidget()
        self.fileSelectorList.setMinimumWidth(140)
        self.fileSelectorList.setMaximumWidth(240)
        self.fileSelectorList.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Select Image:"))
        layout.addWidget(self.fileSelectorList)
        widget.setLayout(layout)
        self.ribbonToolbar.addWidget(widget)
        self.fileSelectorList.connect(self.fileSelectorList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeImage)

        self.ribbon.setCurrentIndex (0)
        self.connect(self.ribbon,QtCore.SIGNAL("currentChanged(int)"),self.tabChanged)


    def tabChanged(self,  index):
        """
        update the overlayWidget of the volumeEditor and switch the _history
        between seeds and labels, also make sure the 
        seed/label widget has a reference to the overlay in the overlayWidget
        they correspond to.
        """
        self.ribbon.widget(self.ribbon.currentTabNumber).on_deActivation()
        self.ribbon.currentTabNumber = index

        self.ribbon.widget(index).on_activation()

        if self.labelWidget is not None:
            self.labelWidget.repaint()     
        
        
    def saveProject(self):
        if hasattr(self,'project'):
            if self.project.filename is not None:
                self.project.saveToDisk()
            else:
                self.saveProjectDlg()
            print "saved Project to ", self.project.filename
                    
    def projectModified(self):
        self.updateFileSelector() #this one also changes the image
        self.project.dataMgr._activeImageNumber = self._activeImageNumber
        self._activeImage = self.project.dataMgr[self._activeImageNumber]

          
#    def newFeatureDlg(self):
#        self.newFeatureDlg = FeatureDlg(self)
#        self.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
#        self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
#        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
#        self.ribbon.tabDict['Classification'].itemDict['Save Classifier'].setEnabled(False)
        
        
    def initImageWindows(self):
        self.labelDocks = []
        
    def destroyImageWindows(self):
        self.volumeEditorDock = None
        self.ribbon.widget(self.ribbon.currentTabNumber).on_deActivation()
        for dock in self.labelDocks:
            self.removeDockWidget(dock)
        self.labelDocks = []
        if self.labelWidget is not None:
            self.labelWidget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.labelWidget.cleanUp()
            self.labelWidget.close()
            self.labelWidget.deleteLater()

                
    def createImageWindows(self, dataVol):
        self.labelWidget = ve.VolumeEditor(dataVol, self,  opengl = self.opengl, openglOverview = self.openglOverview)

        self.ribbon.widget(self.ribbon.currentTabNumber).on_activation()

        self.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
        self.labelWidget.normalizeData = self.project.normalizeData
        self.labelWidget.useBorderMargin = self.project.useBorderMargin
        self.labelWidget.setRgbMode(self.project.rgbData)
        
        
        dock = QtGui.QDockWidget("Ilastik Label Widget", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)
        
        self.volumeEditorDock = dock

        self.connect(self.labelWidget, QtCore.SIGNAL("labelRemoved(int)"),self.labelRemoved)
        self.connect(self.labelWidget, QtCore.SIGNAL("seedRemoved(int)"),self.seedRemoved)
        
        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

    def labelRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive.updateThreadQueues()


    def seedRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        self.project.dataMgr.removeSeed(number)
        if hasattr(self, "segmentationInteractive"):
            self.segmentatinoInteractive.updateThreadQueues()


    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        if self.project.featureMgr is not None:
            self.project.deleteFeatureOverlays()
            self.featureComputation = FeatureComputation(self)

    def on_shortcutsDlg(self):
        shortcutManager.showDialog()

#    def on_batchProcess(self):
#        dialog = batchProcess.BatchProcess(self)
#        result = dialog.exec_()
    
#    def on_changeClassifier(self):
#        dialog = ClassifierSelectionDlg(self)
#        self.project.classifier = dialog.exec_()
#        print self.project.classifier

#    def on_changeSegmentor(self):
#        dialog = SegmentorSelectionDlg(self)
#        answer = dialog.exec_()
#        if answer != None:
#            self.project.segmentor = answer
#            self.project.segmentor.setupWeights(self.project.dataMgr[self._activeImageNumber].segmentationWeights)


    def on_segmentationSegment(self):
        self.segmentationSegment = Segmentation(self)

    def on_classificationTrain(self):
        self.classificationTrain = ClassificationTrain(self)
        
    def on_classificationPredict(self):
        self.classificationPredict = ClassificationPredict(self)
    
    def on_classificationInteractive(self, state):
        if state:
            self.ribbon.getTab('Classification').btnStartLive.setText('Stop Live Prediction')
            self.classificationInteractive = ClassificationInteractive(self)
        else:
            self.classificationInteractive.stop()
            del self.classificationInteractive
            self.ribbon.getTab('Classification').btnStartLive.setText('Start Live Prediction')


    def on_segmentation_border(self):
        pass

    def on_saveClassifier(self, fileName=None):
        
        hf = h5py.File(fileName,'r')
        h5featGrp = hf['features']
        self.project.featureMgr.importFeatureItems(h5featGrp)
        hf.close()
        
        self.project.dataMgr.importClassifiers(fileName)
    
    def on_exportClassifier(self):
        global LAST_DIRECTORY
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", ilastik.gui.LAST_DIRECTORY, "HDF5 Files (*.h5)")
        LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
        
        try:
            self.project.dataMgr.exportClassifiers(fileName)
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            return

        try:
            h5file = h5py.File(str(fileName),'a')
            h5featGrp = h5file.create_group('features')
            self.project.featureMgr.exportFeatureItems(h5featGrp)
            h5file.close()
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            h5file.close()
            return
        
        #if fileName is not None:
            # global LAST_DIRECTORY
            #fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", ilastik.gui.LAST_DIRECTORY, "HDF5 Files (*.h5)")
            #ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
        
        # Make sure group 'classifiers' exist
#        print fileName
#        h5file = h5py.File(str(fileName),'a')
#        h5file.create_group('classifiers')
#        h5file.close()
#        
#        for i, c in enumerate(self.project.dataMgr.classifiers):
#            tmp = c.serialize(str(fileName), "classifiers/rf_%03d" % i)
#            print "Write Random Forest # %03d -> %d" % (i,tmp)
        
        # Export user feature selection
#        h5file = h5py.File(str(fileName),'a')
#        h5featGrp = h5file.create_group('features')
#        
#        featureItems = self.project.featureMgr.featureItems
#        for k, feat in enumerate(featureItems):
#            itemGroup = h5featGrp.create_group('feature_%03d' % k)
#            feat.serialize(itemGroup)
#        h5file.close()

        QtGui.QMessageBox.information(self, 'Success', "The classifier and the feature information have been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
        
    
    def on_connectComponents(self, background = False):
        self.connComp = CC(self)
        self.connComp.selection_key = self.project.dataMgr.connCompBackgroundKey
        self.connComp.start(background)

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Save before Exit?', "Save the Project before quitting the Application", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.saveProject()
            event.accept()
        elif reply == QtGui.QMessageBox.No:
            event.accept()
        else:
            event.ignore()
            

class FeatureComputation(object):
    def __init__(self, parent):
        self.parent = parent
        self.featureCompute() 
    
    def featureCompute(self):
        self.parent.project.dataMgr.featureLock.acquire()
        self.myTimer = QtCore.QTimer()
        self.parent.connect(self.myTimer, QtCore.SIGNAL("timeout()"), self.updateFeatureProgress)
        self.parent.project.dataMgr.properties["Classification"]["classificationMgr"].clearFeaturesAndTraining()
        numberOfJobs = self.parent.project.featureMgr.prepareCompute(self.parent.project.dataMgr)   
        self.initFeatureProgress(numberOfJobs)
        self.parent.project.featureMgr.triggerCompute()
        self.myTimer.start(200)
        
    def initFeatureProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myFeatureProgressBar = QtGui.QProgressBar()
        self.myFeatureProgressBar.setMinimum(0)
        self.myFeatureProgressBar.setMaximum(numberOfJobs)
        self.myFeatureProgressBar.setFormat(' Features... %p%')
        statusBar.addWidget(self.myFeatureProgressBar)
        statusBar.show()
    
    def updateFeatureProgress(self):
        val = self.parent.project.featureMgr.getCount() 
        self.myFeatureProgressBar.setValue(val)
        if not self.parent.project.featureMgr.featureProcess.isRunning():
            self.myTimer.stop()
            self.terminateFeatureProgressBar()
            self.parent.project.featureMgr.joinCompute(self.parent.project.dataMgr)   
            self.parent.project.createFeatureOverlays()

            
    def terminateFeatureProgressBar(self):
        self.parent.statusBar().removeWidget(self.myFeatureProgressBar)
        self.parent.statusBar().hide()
        self.parent.project.dataMgr.properties["Classification"]["classificationMgr"].buildTrainingMatrix()
        self.parent.project.dataMgr.featureLock.release()
        if hasattr(self.parent, "classificationInteractive"):
            self.parent.classificationInteractive.updateThreadQueues()
            
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
                    
    def featureShow(self, item):
        pass

class ClassificationTrain(object):
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()
        
    def start(self):
        #process all unaccounted label changes
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        
        newLabels = self.parent.labelWidget.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.updateTrainingMatrix(newLabels)
        
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
        numberOfJobs = 10                 
        self.initClassificationProgress(numberOfJobs)
        
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, self.parent.project.dataMgr, classifier = self.parent.project.classifier)
        self.classificationProcess.start()
        self.classificationTimer.start(500) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Training... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationProcess.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationProcess.isRunning():
            self.classificationTimer.stop()
            self.classificationProcess.wait()
            self.terminateClassificationProgressBar()
            self.finalize()
            
    def finalize(self):
        self.ilastik.on_classificationPredict()
                      
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        

        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(True)
        

class ClassificationInteractive(object):
    def __init__(self, parent):
        self.parent = parent
        self.stopped = False
        
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        
        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.updateThreadQueues)

        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('changedSlice(int, int)'), self.updateThreadQueues)

        self.temp_cnt = 0
        
        descriptions =  self.parent.project.dataMgr.properties["Classification"]["labelDescriptions"]
        activeImage = self.parent._activeImage
        
        for p_num,pd in enumerate(descriptions):
            #create Overlay for _prediction if not there:
            if activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] is None:
                data = numpy.zeros(activeImage.shape, 'uint8')
                ov = OverlayItem(data,  color = QtGui.QColor.fromRgba(long(descriptions[p_num-1].color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True)
                activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] = ov

        #create Overlay for uncertainty:
        if activeImage.overlayMgr["Classification/Uncertainty"] is None:
            data = numpy.zeros(activeImage.shape, 'uint8')
            ov = OverlayItem(data, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
            activeImage.overlayMgr["Classification/Uncertainty"] = ov
        
        self.start()
    
    def updateThreadQueues(self, a = 0, b = 0):
        if self.classificationInteractive is not None:
            self.myInteractionProgressBar.setVisible(True)
            self.classificationInteractive.dataPending.set()

    def updateLabelWidget(self):
        try:
            self.myInteractionProgressBar.setVisible(False)
            self.parent.labelWidget.repaint()                    
        except IndexError:
            pass
                


    def initInteractiveProgressBar(self):
        statusBar = self.parent.statusBar()
        self.myInteractionProgressBar = QtGui.QProgressBar()
        self.myInteractionProgressBar.setVisible(False)
        self.myInteractionProgressBar.setMinimum(0)
        self.myInteractionProgressBar.setMaximum(0)
        statusBar.addWidget(self.myInteractionProgressBar)
        statusBar.show()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myInteractionProgressBar)
        self.parent.statusBar().hide()
        
    def start(self):
        self.initInteractiveProgressBar()
        self.classificationInteractive = classificationMgr.ClassifierInteractiveThread(self.parent, self.parent.project.dataMgr.properties["Classification"]["classificationMgr"],classifier = self.parent.project.classifier)

        self.parent.connect(self.classificationInteractive, QtCore.SIGNAL("resultsPending()"), self.updateLabelWidget)      
    
               
        self.classificationInteractive.start()
        self.updateThreadQueues()
        
        
    def stop(self):
        self.classificationInteractive.stopped = True

        self.classificationInteractive.dataPending.set() #wake up thread one last time before his death
        self.classificationInteractive.wait()
        self.finalize()
        
        self.terminateClassificationProgressBar()
    
    def finalize(self):
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        
        self.parent.project.dataMgr.classifiers = list(self.classificationInteractive.classifiers)
        self.classificationInteractive =  None
        

class ClassificationPredict(object):
    def __init__(self, parent):
        self.parent = parent
        self.start()
    
    def start(self):       
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(False)
         
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
                    
        self.classificationPredict = classificationMgr.ClassifierPredictThread(self.parent.project.dataMgr)
        numberOfJobs = self.classificationPredict.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.classificationPredict.start()
        self.classificationTimer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Prediction... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationPredict.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationPredict.isRunning():
            self.classificationTimer.stop()

            self.classificationPredict.wait()
            self.finalize()           
            self.terminateClassificationProgressBar()

    def finalize(self):
        activeImage = self.parent._activeImage
        
        for itemindex, activeItem in enumerate(self.parent.project.dataMgr):
            display = False
            if activeImage == activeItem:
                display = True
            
            prediction = self.classificationPredict._prediction
            descriptions =  self.parent.project.dataMgr.properties["Classification"]["labelDescriptions"]
            classifiers = self.parent.project.dataMgr.properties["Classification"]["classificationMgr"].classifiers
            
            if prediction is not None:
    #            for p_i, item in enumerate(activeItem._dataVol.labels.descriptions):
    #                item._prediction[:,:,:,:] = (activeItem._prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)
                foregrounds = []
                for p_i, p_num in enumerate(classifiers[0].unique_vals):
                    #create Overlay for _prediction:
                    
                    ov = OverlayItem(prediction[itemindex][:,:,:,:,p_i],  color = QtGui.QColor.fromRgba(long(descriptions[p_num-1].color)), alpha = 0.4, colorTable = None, autoAdd = display, autoVisible = display)
                    activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] = ov
                    ov = activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]
                    foregrounds.append(ov)
    
                import ilastik.core.overlays.thresHoldOverlay as tho
                
                if activeItem.overlayMgr["Classification/Segmentation"] is None:
                    ov = tho.ThresHoldOverlay(foregrounds, [])
                    activeItem.overlayMgr["Classification/Segmentation"] = ov
                else:
                    ov = activeItem.overlayMgr["Classification/Segmentation"]
                    ov.setForegrounds(foregrounds)
    
    
                all =  range(len(descriptions))
                classifiers = self.parent.project.classificationMgr.classifiers
                if len(classifiers) > 0:
                    not_predicted = numpy.setdiff1d(all, classifiers[0].unique_vals - 1)
                    for p_i, p_num in enumerate(not_predicted):
                        prediction[:,:,:,:,p_i] = 0
    
    
    
                margin = activeLearning.computeEnsembleMargin(prediction[itemindex][:,:,:,:,:])*255.0
    
                #create Overlay for uncertainty:
                ov = OverlayItem(margin, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = display, autoVisible = False)
                activeItem.overlayMgr["Classification/Uncertainty"] = ov
    
    
        self.parent.labelWidget.repaint()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnExportClassifier.setEnabled(True)




class Segmentation(object):

    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()

    def start(self):
        self.parent.ribbon.getTab('Segmentation').btnSegment.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        self.segmentation = segmentationMgr.SegmentationThread(self.parent.project.dataMgr, self.parent.project.dataMgr[self.ilastik._activeImageNumber], self.ilastik.project.segmentor)
        numberOfJobs = self.segmentation.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.segmentation.start()
        self.timer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Segmentation... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.segmentation.count
        self.progressBar.setValue(val)
        if not self.segmentation.isRunning():
            print "finalizing segmentation"
            self.timer.stop()
            self.segmentation.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        activeItem._dataVol.segmentation = self.segmentation.result

        #temp = activeItem._dataVol.segmentation[0, :, :, :, 0]
        
        #create Overlay for segmentation:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] is None:
            ov = OverlayItem(activeItem._dataVol.segmentation, color = 0, alpha = 1.0, colorTable = self.parent.labelWidget.labelWidget.colorTab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]._data = DataAccessor(activeItem._dataVol.segmentation)
        self.ilastik.labelWidget.repaint()


        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Segmentation').btnSegment.setEnabled(True)


class CC(object):
    #Connected components
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        #self.start()

    def start(self, background = False):
        self.parent.ribbon.getTab('Connected Components').btnCC.setEnabled(False)
        self.parent.ribbon.getTab('Connected Components').btnCCBack.setEnabled(False)
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)
        overlay = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr[self.selection_key]
        if background==False:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data)
        else:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data, self.parent.project.dataMgr.connCompBackgroundClasses)
        numberOfJobs = self.cc.numberOfJobs
        self.initCCProgress(numberOfJobs)
        self.cc.start()
        self.timer.start(200)
        
    def initCCProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Connected Components... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.cc.count
        self.progressBar.setValue(val)
        if not self.cc.isRunning():
            print "finalizing connected components"
            self.timer.stop()
            self.cc.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        #activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        #activeItem._dataVol.cc = self.cc.result

        #temp = activeItem._dataVol.segmentation[0, :, :, :, 0]
        
        #create Overlay for connected components:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"] is None:
            #colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            colortab = self.makeColorTab()
            ov = OverlayItem(self.cc.result, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"]._data = DataAccessor(self.cc.result)
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
    def makeColorTab(self):
        sublist = []
        sublist.append(QtGui.qRgb(0, 0, 0))
        sublist.append(QtGui.qRgb(255, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 0))
        sublist.append(QtGui.qRgb(0, 255, 0))
        sublist.append(QtGui.qRgb(0, 0, 255))
        
        sublist.append(QtGui.qRgb(255, 255, 0))
        sublist.append(QtGui.qRgb(0, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 255))
        sublist.append(QtGui.qRgb(255, 105, 180)) #hot pink!
        
        sublist.append(QtGui.qRgb(102, 205, 170)) #dark aquamarine
        sublist.append(QtGui.qRgb(165,  42,  42)) #brown        
        sublist.append(QtGui.qRgb(0, 0, 128)) #navy
        sublist.append(QtGui.qRgb(255, 165, 0)) #orange
        
        sublist.append(QtGui.qRgb(173, 255,  47)) #green-yellow
        sublist.append(QtGui.qRgb(128,0, 128)) #purple
        sublist.append(QtGui.qRgb(192, 192, 192)) #silver
        #sublist.append(QtGui.qRgb(240, 230, 140)) #khaki
        colorlist = []
        for i in range(0, 16):
            colorlist.extend(sublist)
        print len(colorlist)
        return colorlist
        

if __name__ == "__main__":
    app = QtGui.QApplication.instance() #(sys.argv)
    #app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow(sys.argv)
      
    mainwindow.show() 
    app.exec_()
    print "cleaning up..."
    if mainwindow.labelWidget is not None:
        del mainwindow.labelWidget
    del mainwindow



    del ilastik.core.jobMachine.GLOBAL_WM

    

