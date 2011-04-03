from vtk import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from functools import partial

import sys, h5py, copy
from numpy2vtk import toVtkImageData

#make the program quit on Ctrl+C
import signal, numpy
signal.signal(signal.SIGINT, signal.SIG_DFL)

#Read
#http://www.vtk.org/pipermail/vtkusers/2010-July/110094.html
#for information on why not to inherit from QThread

class QThreader(QThread):
    #see here
    #http://wiki.maemo.org/PyQt_Tips_and_Tricks
    #why this is needed
    def run(self):
        print "QThreader::run()"
        #t = QTimer()
        #t.setInterval(0)
        #t.setSingleShot(True)
        #self.connect(t, SIGNAL("timeout"), self.exec_)
        #t.start()
        self.exec_()
    def exec_(self):
        print "QThreader::exec_()"
        QThread.exec_(self)

class MeshExtractor(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        
        self.inputImage = None
        self.numpyVolume = None
        self.meshes = dict()
        self.suppressLabels = list()
        self.smooth = True
        
        t = QTimer()
        t.setInterval(0)
        t.setSingleShot(True)
        self.connect(t, SIGNAL("timeout()"), self.extract)
        
        print "init MeshExtractor"
    
    def progressCallback(self, caller, eventId):
        self.emit(SIGNAL("currentStepProgressChanged(float)"), caller.GetProgress())
    
    def SetInput(self, numpyVolume):
        self.numpyVolume = numpyVolume.copy()
    def SuppressLabels(self, labelList):
        print "will suppress labels =", labelList
        self.suppressLabels = labelList
    def Smooth(self, smooth):
        self.smooth = smooth
    
    def run(self):
        print "Extractor.run()"
        #t = QTimer()
        #t.setInterval(0)
        #t.setSingleShot(True)
        #self.connect(t, SIGNAL("timeout()"), self.extract)
        #self.exec_()
        self.extract()
    
    def extract(self):
        print "MeshExtractor::extract()"
        self.meshes = dict()
        
        #self.elapsed.restart()
        count = 0
        
        if self.numpyVolume is None:
            raise RuntimeError("You need to call SetInput() first")
   
        self.inputImage = toVtkImageData(self.numpyVolume)
   
        #Create all of the classes we will need   
        histogram     = vtkImageAccumulate()
        discreteCubes = vtkDiscreteMarchingCubes()
        smoother      = vtkWindowedSincPolyDataFilter()
        selector      = vtkThreshold()
        scalarsOff    = vtkMaskFields()
        geometry      = vtkGeometryFilter()
        #writer        = vtkXMLPolyDataWriter()

        #Define all of the variables
        startLabel          = 0
        endLabel            = numpy.max(self.numpyVolume[:])
        filePrefix          = 'label'
        smoothingIterations = 15
        passBand            = 0.001
        featureAngle        = 120.0

        #Generate models from labels
        #1) Read the meta file
        #2) Generate a histogram of the labels
        #3) Generate models from the labeled volume
        #4) Smooth the models
        #5) Output each model into a separate file

        self.emit(SIGNAL("newStep(QString)"), QString("Histogram"))
        qDebug("*** Histogram ***")
        histogram.SetInput(self.inputImage)
        histogram.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
        histogram.SetComponentExtent(0, endLabel, 0, 0, 0, 0)
        histogram.SetComponentOrigin(0, 0, 0)
        histogram.SetComponentSpacing(1, 1, 1)
        histogram.Update()

        self.emit(SIGNAL("newStep(QString)"), QString("Marching Cubes"))
        qDebug("*** Marching Cubes ***")
        discreteCubes.SetInput(self.inputImage)
        discreteCubes.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
        discreteCubes.GenerateValues(endLabel - startLabel + 1, startLabel, endLabel)

        if self.smooth:
            self.emit(SIGNAL("newStep(QString)"), QString("Smoothing"))
            qDebug("*** Smoothing ***")
            smoother.SetInput(discreteCubes.GetOutput())
            smoother.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
            smoother.SetNumberOfIterations(smoothingIterations)
            smoother.BoundarySmoothingOff()
            smoother.FeatureEdgeSmoothingOff()
            smoother.SetFeatureAngle(featureAngle)
            smoother.SetPassBand(passBand)
            smoother.NonManifoldSmoothingOn()
            smoother.NormalizeCoordinatesOn()
            smoother.Update()

        self.emit(SIGNAL("newStep(QString)"), QString("Preparing meshes"))
        qDebug("*** Preparing meshes ***")
        if self.smooth:
            selector.SetInput(smoother.GetOutput())
        else:
            selector.SetInput(discreteCubes.GetOutput())
        selector.SetInputArrayToProcess(0, 0, 0,
                                        vtkDataObject.FIELD_ASSOCIATION_CELLS,
                                        vtkDataSetAttributes.SCALARS)

        #Strip the scalars from the output
        scalarsOff.SetInput(selector.GetOutput())
        scalarsOff.CopyAttributeOff(vtkMaskFields.POINT_DATA,
                                    vtkDataSetAttributes.SCALARS)
        scalarsOff.CopyAttributeOff(vtkMaskFields.CELL_DATA,
                                    vtkDataSetAttributes.SCALARS)

        geometry.SetInput(scalarsOff.GetOutput())

        #writer.SetInput(geometry.GetOutput())
        
        selector.ThresholdBetween(2, 2)
        
        self.emit(SIGNAL("newStep(QString)"), QString("Writing meshes"))
        qDebug("*** Writing meshes ***")
        for i in range(startLabel, endLabel+1):
            self.emit(SIGNAL("currentStepProgressChanged(float)"), (i-startLabel+1)/float(endLabel-startLabel+1))
            
            if i in self.suppressLabels:
                print " - suppressed label:",i
                continue
            
            #see if the label exists, if not skip it
            frequency = histogram.GetOutput().GetPointData().GetScalars().GetTuple1(i)
            if frequency == 0.0:
                print " - labels %d does not occur" % (i)
                continue

            #select the cells for a given label
            selector.ThresholdBetween(i, i)
            selector.Update()
            
            #this seems to be a bug in VTK, why should this call be necessary?
            geometry.GetOutput().Update()
        
            #FIXME
            #In ILASTIK, the axes 0 and 2 are flipped.
            #We have to correct for that here
            #<begin> FIXME
            f = vtkTransformPolyDataFilter()
            t = vtkTransform()
            t.Scale(1,1,-1)
            t.RotateY(90)
            f.SetTransform(t)
            f.SetInput(geometry.GetOutput())
            f.Update()
            #<end> FIXME
            
            poly = vtkPolyData()
            poly.DeepCopy(f.GetOutput())
            
            print "test"
            #poly.PrintSelf()
            
            print " - adding mesh for label %d" % (i)
            self.meshes[i] = poly
            
        print " ==> list of labels:", self.meshes.keys()
        #print "MeshExtractor::done"
        self.emit(SIGNAL('done()'))

class MeshExtractorDialog(QDialog):
    currentStep = 0
    extractor   = None
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        #w = QWidget()
        #self.setCentralWidget(w)
        
        l = QVBoxLayout()
        self.setLayout(l)
        
        self.overallProgress = QProgressBar()
        self.overallProgress.setRange(0, 5)
        self.overallProgress.setFormat("step %v of 5")
        
        self.currentStepProgress = QProgressBar()
        self.currentStepProgress.setRange(0, 100)
        self.currentStepProgress.setFormat("%p %")
        
        self.overallLabel = QLabel("Overall progress")
        self.currentStepLabel = QLabel("Current step")
        
        l.addWidget(self.overallLabel)
        l.addWidget(self.overallProgress)
        l.addWidget(self.currentStepLabel)
        l.addWidget(self.currentStepProgress)
        
        self.update()

    def __onNewStep(self, description):
        print "MeshExtractorDialog new step: %s" % (description)
        self.currentStep += 1
        self.currentStepProgress.setValue(0)
        self.overallProgress.setValue(self.currentStep)
        self.currentStepLabel.setText(description)
        self.update()

    def __onCurrentStepProgressChanged(self, progress):
        print "  - MeshExtractorDialog progress=", progress
        self.currentStepProgress.setValue( round(100.0*progress) )
        self.update()

    def run(self, segVolume, suppressLabels = list(), smooth=True):
        self.extractor = MeshExtractor(self)
        self.extractor.SetInput(segVolume)
        self.extractor.SuppressLabels(suppressLabels)
        self.extractor.Smooth(smooth)
        
        self.connect(self.extractor, SIGNAL("newStep(QString)"), self.__onNewStep, Qt.BlockingQueuedConnection)
        self.connect(self.extractor, SIGNAL("currentStepProgressChanged(float)"), self.__onCurrentStepProgressChanged, Qt.BlockingQueuedConnection)

        #please read:
        #http://www.riverbankcomputing.com/pipermail/pyqt/2007-February/015512.html

        #self.connect(thread, SIGNAL('started()'), extractor, SLOT("extract"))
        #self.connect(thread, SIGNAL('started()'), extractor.testing)
        self.extractor.connect(self.extractor, SIGNAL('finished()'), self.onMeshesExtracted)

        self.extractor.start()
    
    def onMeshesExtracted(self):
        self.emit(SIGNAL('done()'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    f=h5py.File("/home/thorben/phd/src/vtkqt-test/seg.h5")
    seg=f['volume/data'][0,:,:,:,0]
    f.close()

    window = MeshExtractorDialog()
    window.show()
    QTimer.singleShot(200, partial(window.run, seg));
    app.exec_()

