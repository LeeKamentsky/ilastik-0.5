# -*- coding: utf-8 -*-
import numpy, vigra, os
import traceback, h5py
import time
import copy
import random

from ilastik.core import dataImpex

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponents
from ilastik.modules.connected_components.gui.guiThread import CC

from seedWidget import SeedListWidget
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

from segmentorSelectionDlg import SegmentorSelectionDlg


class InlineSettingsWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        # The edit_traits call will generate the widget to embed.
        self.childWidget = QtGui.QHBoxLayout(self)
        self.childWidget.setMargin(0)
        self.childWidget.setSpacing(0)
        
        self.ui = None
        
    def changeWidget(self, ui):
        if self.ui is not None:
            self.ui.close()
            self.childWidget.removeWidget(self.ui)
            del self.ui
        self.ui = None
        if ui is not None:
            self.ui = ui
            self.childWidget.addWidget(self.ui)
            self.ui.setParent(self)


class InteractiveSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Interactive Segmentation'
    position = 3
    moduleName = "Interactive_Segmentation"
    
    outputPath = os.path.expanduser("~/test-segmentation/")
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        self._initContent()
        self._initConnects()
        self.interactionLog = []
        self.defaultSegmentor = False
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        self.ilastik.labelWidget.interactionLog = self.interactionLog
        
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        #create SeedsOverlay
        ov = OverlayItem(self.ilastik._activeImage.Interactive_Segmentation.seeds._data, color = 0, alpha = 1.0, colorTable = self.ilastik._activeImage.Interactive_Segmentation.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]

        overlayWidget.addOverlayRef(ov.getRef())
        
        self.ilastik.labelWidget.setLabelWidget(SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  self.ilastik._activeImage.Interactive_Segmentation.seeds,  self.ilastik.labelWidget,  ov))
        
        if self.parent.project.dataMgr.Interactive_Segmentation.segmentor is None:
            segmentors = self.parent.project.dataMgr.Interactive_Segmentation.segmentorClasses
            for i, seg in enumerate(segmentors):
                if seg.name == "Supervoxel Segmentation":
                    self.parent.project.dataMgr.Interactive_Segmentation.segmentor = seg()
                    ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget, view='default')
                    self.inlineSettings.changeWidget(ui)
                    self.defaultSegmentor = True
                    break            
            
        
        
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
        ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]
        
        if ov is None:
            path = self.outputPath
            try:
                os.makedirs(path)
            except:
                pass            
            try:
                activeItem = self.ilastik._activeImage
                file_name = path + "done.h5"
                dataImpex.DataImpex.importOverlay(activeItem, file_name, "")
                
                """
                theDataItem = dataImpex.DataImpex.importDataItem(file_name, None)
                if theDataItem is None:
                    print "No _data item loaded"
                else:
                    if theDataItem.shape[0:-1] == activeItem.shape[0:-1]:
                        data = theDataItem[:,:,:,:,:]
                        ov = OverlayItem(data, color = QtGui.QColor(0,0,255), alpha = 0.5, colorTable = None, autoAdd = True, autoVisible = True, min = 1.0, max = 2.0)
                        activeItem.overlayMgr["Segmentation/Done"] = ov
                    else:
                        print "Cannot add " + theDataItem.fileName + " due to dimensionality mismatch"
                """
            except:
                traceback.print_exc()

        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
        if ov is not None:
            colorTableCC = CC.makeColorTab()
            ov_cc = OverlayItem(ov._data, color=0, alpha=0.7, colorTable=colorTableCC, autoAdd=False, autoVisible=False)                    
            self.ilastik._activeImage.overlayMgr["Segmentation/Objects"] = ov_cc
            #ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]

    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.interactionLog = self.ilastik.labelWidget.interactionLog
        self.ilastik.labelWidget.interactionLog = None
        if self.ilastik.labelWidget._history != self.ilastik._activeImage.Interactive_Segmentation.seeds._history:
            self.ilastik._activeImage.Interactive_Segmentation.seeds._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Interactive_Segmentation.seeds._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Interactive_Segmentation.seeds._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
        self.btnChooseDimensions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Using 3D')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        self.btnFinishSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Finish Object')
        self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Change Segmentor')
        
        self.inlineSettings = InlineSettingsWidget(self)
        
        self.only2D = False
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnChooseDimensions.setToolTip('Switch between slice based 2D segmentation and full 3D segmentation\n This is mainly useful for 3D Date with very weak border indicators, where seeds placed in one slice can bleed out badly to other regions')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        
        tl.addWidget(self.btnChooseWeights)
        
        #tl.addWidget(self.btnChooseDimensions)
        tl.addWidget(self.btnSegment)        
        tl.addWidget(self.inlineSettings)
        tl.addWidget(self.btnFinishSegment)
        tl.addStretch()
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.btnSegment.setEnabled(False)
        self.btnFinishSegment.setEnabled(False)
        self.btnChooseDimensions.setEnabled(False)
        self.btnSegmentorsOptions.setEnabled(False)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        self.connect(self.btnFinishSegment, QtCore.SIGNAL('clicked()'), self.on_btnFinishSegment_clicked)
        self.connect(self.btnChooseDimensions, QtCore.SIGNAL('clicked()'), self.on_btnDimensions)
        self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        self.shortcutSegment = QtGui.QShortcut(QtGui.QKeySequence("s"), self, self.on_btnSegment_clicked, self.on_btnSegment_clicked)
        #shortcutManager.register(self.shortcutNextLabel, "Labeling", "Go to next label (cyclic, forward)")
        
    
    def on_btnDimensions(self):
        self.only2D = not self.only2D
        if self.only2D:
            ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]
            if ov is not None:
                zerod = numpy.zeros(ov._data.shape, numpy.uint8)
                ov._data = DataAccessor(zerod)
            self.btnChooseDimensions.setText('Using 2D')
                        
        else:
            self.btnChooseDimensions.setText('Using 3D')
        self.setupWeights()
        
    
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(self.ilastik, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness", "Gradient Magnitude"],  editable = False)
            if borderIndicator[1]:
                borderIndicator = str(borderIndicator[0])
                
                sigma = 1.0
                normalizePotential = True
                #TODO: this , until now, only supports gray scale and 2D!
                if borderIndicator == "Brightness":
                    weights = volume[:,:,:].view(vigra.ScalarVolume)
                elif borderIndicator == "Darkness":
                    weights = (255 - volume[:,:,:]).view(vigra.ScalarVolume)
                elif borderIndicator == "Gradient Magnitude":
                    weights = numpy.ndarray(volume.shape, numpy.float32)
                    if weights.shape[0] == 1:
                        weights[0,:,:] = vigra.filters.gaussianGradientMagnitude((volume[0,:,:]).astype(numpy.float32), 1.0 )
                    else:
                        weights = vigra.filters.gaussianGradientMagnitude((volume[:,:,:]).astype(numpy.float32), 1.0 )
        
                if normalizePotential == True:
                    min = numpy.min(volume)
                    max = numpy.max(volume)
                    print "Weights min/max :", min, max
                    weights = (weights - min)*(255.0 / (max - min))
        
                self.setupWeights(weights)
                self.btnSegmentorsOptions.setEnabled(True)
                self.btnSegment.setEnabled(True)
                self.btnFinishSegment.setEnabled(True)
            

    def setupWeights(self, weights = None):
        self.ilastik.labelWidget.interactionLog = []
        if weights is None:
            weights = self.localMgr._segmentationWeights
        else:
            self.localMgr._segmentationWeights = weights
        if self.globalMgr.segmentor is not None:
            self.globalMgr.segmentor.setupWeights(weights)



    def clearSeeds(self):
        self._seedL = None
        self._seedIndices = None


    def mouseReleaseEvent(self, event):
        """
        mouse button release event
        """
        button = event.button()
        # select an item on which we clicked

    def on_btnFinishSegment_clicked(self):
        res = QtGui.QInputDialog.getText(self, "Finish object", "Enter object name:")
        print res
        if res[1] == True:
            path = self.outputPath+str(res[0])
            try:
                os.makedirs(path)
            except:
                pass
            ovs = self.ilastik._activeImage.overlayMgr["Segmentation/Segmentation"]
            if ovs is not None:
                dataImpex.DataImpex.exportOverlay(path + "/segmentation", "h5", ovs)
            ovseed = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]
            if ovseed is not None:
                dataImpex.DataImpex.exportOverlay(path + "/seeds", "h5", ovseed)
            f = open(path + "/interactions.log", "w")
            for l in self.ilastik.labelWidget.interactionLog:
                f.write(l + "\n")
            f.close()
            self.ilastik.labelWidget.interactionLog = []
            
            if ovs is not None:
                ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
                ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]
                
                if ov is None:
                    #create Old Overlays if not there
                    shape = self.ilastik._activeImage.shape
                    data = DataAccessor(numpy.zeros((shape), numpy.uint8))
                    bluetable = []
                    bluetable.append(long(0))
                    for i in range(0, 16):
                        bluetable.append(QtGui.qRgb(0, 0, 255))
                    bluetable.pop()
                    ov = OverlayItem(data, color = 0, colorTable=bluetable, alpha = 0.5, autoAdd = True, autoVisible = True, min = 1.0, max = 2.0)
                    colorTableCC = CC.makeColorTab()
                    ov_cc = OverlayItem(data, color=0, alpha=0.7, colorTable=colorTableCC, autoAdd=False, autoVisible=False)                    
                    self.ilastik._activeImage.overlayMgr["Segmentation/Done"] = ov
                    self.ilastik._activeImage.overlayMgr["Segmentation/Objects"] = ov_cc

                data = ov[0,:,:,:,:]
                seg = ovs[0,:,:,:,:]
                cc_object = ConnectedComponents()
                background = set()
                background.add(1)
                prev_max = numpy.max(data)
                #print "components before: ", prev_max
                res_cc = cc_object.connect(ovs[0, :, :, :, 0], background)                
                #res = numpy.where(seg > 1, seg, data)
                res = numpy.where(res_cc>0, res_cc+prev_max, data)
                ov[0,:,:,:,:] = res[:]             
                #save the current done state
                ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
                ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]
                dataImpex.DataImpex.exportOverlay(path + "/../done", "h5", ov)
            
            if ovseed is not None:
                ovseed[0,:,:,:,:] = 0
                
            f = h5py.File(path + "/history.h5", 'w')                        
            self.ilastik.labelWidget._history.serialize(f)
            f.close()
            
            
            self.ilastik._activeImage.Interactive_Segmentation.clearSeeds()
            self.ilastik._activeImage.Interactive_Segmentation._buildSeedsWhenNotThere()
            
            self.ilastik.labelWidget.repaint()

        
    def on_btnSegment_clicked(self):
        if hasattr(self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor, "bias"):
            bias = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.bias            
            s = "%f: segment(bias) %f" % (time.clock(),bias)
            self.ilastik.labelWidget.interactionLog.append(s)
            
        self.localMgr.segment()

        #create Overlay for segmentation:
        if self.activeImage.overlayMgr["Segmentation/Segmentation"] is None:
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255
            ov = OverlayItem(self.localMgr.segmentation, color = 0, alpha = 1.0, colorTable = origColorTable, autoAdd = True, autoVisible = True, linkColorTable = True)
            self.activeImage.overlayMgr["Segmentation/Segmentation"] = ov
            
            #this overlay can be shown in 3D
            #the label 0 never occurs, label 1 is assigned to the background  class
            ov.displayable3D = True
            ov.backgroundClasses = set([1])
        else:
            res = self.localMgr.segmentation
            self.activeImage.overlayMgr["Segmentation/Segmentation"]._data = DataAccessor(res)
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255            
            self.activeImage.overlayMgr["Segmentation/Segmentation"].colorTable = origColorTable
            
        if self.localMgr.potentials is not None:
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            ov = OverlayItem(self.localMgr.potentials,color = origColorTable[1], alpha = 1.0, autoAdd = True, autoVisible = True, min = 0.0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Potentials"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Potentials")
            
        if self.localMgr.borders is not None:
            #colorTab = []
            #for i in range(256):
            #    color = QtGui.QColor(random.randint(0,255),random.randint(0,255),random.randint(0,255)).rgba()
            #    colorTab.append(color)
                
            ov = OverlayItem(self.localMgr.borders, color = QtGui.QColor(), alpha = 1.0, autoAdd = True, autoVisible = False, min = 0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Supervoxels"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Supervoxels")
            
        self.parent.labelWidget.repaint()
            
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.Interactive_Segmentation.segmentor = answer
            self.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].Interactive_Segmentation._segmentationWeights)
            self.btnSegment.setEnabled(True)
            self.btnFinishSegment.setEnabled(True)
            
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget)

            self.inlineSettings.changeWidget(ui)
            self.defaultSegmentor = False
        elif self.defaultSegmentor is True:
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget)
            self.inlineSettings.changeWidget(ui)
            self.defaultSegmentor = False
            
