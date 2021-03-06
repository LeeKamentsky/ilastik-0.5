# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QSplitter, QWidget
from PyQt4.Qt import QSizePolicy
from PyQt4 import uic
import os
import qimage2ndarray
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.gui import overlayDialogs
import ilastik
import numpy


#*******************************************************************************
# M y L i s t W i d g e t I t e m                                              *
#*******************************************************************************

#FIXME name. This seems to refer to the list "Add File(s) Overlay", Thresholding Overlay", "Add Stack Overlay"
class MyListWidgetItem(QtGui.QListWidgetItem):
    def __init__(self, item):
        QtGui.QListWidgetItem.__init__(self, item.name)
        self.origItem = item

#*******************************************************************************
# O v e r l a y C r e a t e S e l e c t i o n D l g                            *
#*******************************************************************************

class OverlayCreateSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastikMain):
        QtGui.QWidget.__init__(self, ilastikMain)
        self.setWindowTitle("Overlay Dialog")
        self.ilastik = ilastikMain

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        #self.connect(self.settingsButton, SIGNAL('pressed()'), self.classifierSettings)

        self.overlayDialogs = overlayDialogs.overlayClassDialogs.values()
        
        self.currentOverlay = self.overlayDialogs[0]
        
        j = 0
        for i, o in enumerate(self.overlayDialogs):
            self.listWidget.addItem(MyListWidgetItem(o))

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)

        self.listWidget.setCurrentRow(0)
        
        
        self.settingsButton.setVisible(False)

    def currentRowChanged(self, current):
        o = self.currentOverlay = self.overlayDialogs[current]
        
        self.name.setText(o.name)
        self.homepage.setText(o.homepage)
        self.description.setText(o.description)
        self.author.setText(o.author)


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return self.currentOverlay
        else:
            return None

#*******************************************************************************
# M y Q L a b e l                                                              *
#*******************************************************************************

class MyQLabel(QtGui.QLabel):
    def __init(self, parent):
        QtGui.QLabel.__init__(self, parent)
    #enabling clicked signal for QLabel
    def mouseReleaseEvent(self, ev):
        self.emit(QtCore.SIGNAL('clicked()'))
        
#*******************************************************************************
# M y T r e e W i d g e t                                                      *
#*******************************************************************************

class MyTreeWidget(QtGui.QTreeWidget):
    def __init__(self, *args):
        QtGui.QTreeWidget.__init__(self, *args)
    #enabling space key signal (for checking selected items)
    def event(self, event):
        if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==QtCore.Qt.Key_Space):
            self.emit(QtCore.SIGNAL("spacePressed"))
            return True
        return QtGui.QTreeWidget.event(self, event)

#*******************************************************************************
# O v e r l a y T r e e W i d g e t I t e r                                    *
#*******************************************************************************

class OverlayTreeWidgetIter(QtGui.QTreeWidgetItemIterator):
    def __init__(self, *args):
        QtGui.QTreeWidgetItemIterator.__init__(self, *args)
    def next(self):
        self.__iadd__(1)
        value = self.value()
        if value:
            return self.value()
        else:
            return False

#*******************************************************************************
# O v e r l a y T r e e W i d g e t I t e m                                    *
#*******************************************************************************

class OverlayTreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, item, overlayPathName):
        """
        item:            OverlayTreeWidgetItem
        overlayPathName: string
                         full name of the overlay, for example 'File Overlays/My Data'
        """
        self.overlayPathName = overlayPathName
        QtGui.QTreeWidgetItem.__init__(self, [item.name])
        self.item = item

#*******************************************************************************
# O v e r l a y S e l e c t i o n D i a l o g                                  *
#*******************************************************************************

class OverlaySelectionDialog(QtGui.QDialog):
    def __init__(self, ilastik, forbiddenItems=[], singleSelection=True, selectedItems=[]):
        QtGui.QWidget.__init__(self, ilastik)
        
        self.pixmapImage = None
        
        # init
        # ------------------------------------------------
        self.setMinimumWidth(600)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.selectedOverlaysList = []
        self.selectedOverlayPaths = []
        self.ilastik = ilastik
        self.christophsDict = ilastik.project.dataMgr[ilastik._activeImageNumber].overlayMgr
        self.forbiddenOverlays = forbiddenItems
        self.preSelectedOverlays = selectedItems
        self.singleOverlaySelection = singleSelection
        self.scaleList = [0.1, 0.125, 0.17, 0.25, 0.33, 0.50, 0.67, 1, 2, 3, 4, 5, 6, 7, 8]
        self.scalePrev = 0.67
        self.scaleNext = 2
        self.scaleIndex = 7
        
        # widgets and layouts
        # ------------------------------------------------
        
        # splits the layout into the left part
        # (select overlay from tree over available overlays)
        # and the right part
        # (previews the currently selected overlay)
        splitter = QSplitter()
        
        treeGroupBoxLayout = QtGui.QGroupBox("Overlays")
        treeAndButtonsLayout = QtGui.QVBoxLayout()
        self.treeWidget = MyTreeWidget()
        self.connect(self.treeWidget, QtCore.SIGNAL('spacePressed'), self.spacePressedTreewidget)
        self.treeWidget.header().close()
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.installEventFilter(self)
        #self.treeWidget.itemClicked.connect(self.treeItemSelectionChanged)
        self.treeWidget.itemSelectionChanged.connect(self.treeItemSelectionChanged)
        self.connect(self.treeWidget, QtCore.SIGNAL('itemChanged(QTreeWidgetItem *,int)'), self.treeItemChanged)


        treeButtonsLayout = QtGui.QHBoxLayout()
        self.expandCollapseButton = QtGui.QPushButton("Collapse All")
        self.connect(self.expandCollapseButton, QtCore.SIGNAL('clicked()'), self.expandOrCollapse)
        treeButtonsLayout.addWidget(self.expandCollapseButton)
        treeButtonsLayout.addStretch()
        treeAndButtonsLayout.addWidget(self.treeWidget)
        treeAndButtonsLayout.addLayout(treeButtonsLayout)
        treeGroupBoxLayout.setLayout(treeAndButtonsLayout)

        rightLayout = QtGui.QVBoxLayout()
        previewGroupBox = QtGui.QGroupBox("Preview")
        previewLayout = QtGui.QVBoxLayout()
        self.grview = QtGui.QGraphicsView()
        self.grview.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.grview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.grview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.grscene = QtGui.QGraphicsScene()
        self.grview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grviewHudLayout = QtGui.QVBoxLayout(self.grview)
        grviewHudLayout.addStretch()
        grviewHudZoomElementsLayout = QtGui.QHBoxLayout()
        self.min = MyQLabel()
        self.min.setPixmap(QtGui.QPixmap(ilastikIcons.RemSelx16))
        self.connect(self.min, QtCore.SIGNAL('clicked()'), self.scaleDown)
        self.zoomScaleLabel = MyQLabel("100%")
        #self.zoomScaleLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.zoomScaleLabel.setStyleSheet("color: lightGray; font-weight:bold;")
        self.connect(self.zoomScaleLabel, QtCore.SIGNAL('clicked()'), self.clickOnLabel)
        self.max = MyQLabel()
        self.max.setPixmap(QtGui.QPixmap(ilastikIcons.AddSelx16))
        self.connect(self.max, QtCore.SIGNAL('clicked()'), self.scaleUp)
        grviewHudZoomElementsLayout.addStretch()
        grviewHudZoomElementsLayout.addWidget(self.min)
        grviewHudZoomElementsLayout.addWidget(self.zoomScaleLabel)
        grviewHudZoomElementsLayout.addWidget(self.max)
        grviewHudZoomElementsLayout.addStretch()
        grviewHudLayout.addLayout(grviewHudZoomElementsLayout)
        
        grviewSpinboxLayout = QtGui.QHBoxLayout()
        self.channelSpinboxLabel = QtGui.QLabel("Channel")
        self.channelSpinbox = QtGui.QSpinBox(self)
        self.channelSpinbox.setEnabled(False)
        self.connect(self.channelSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.channelSpinboxValueChanged)
        self.sliceSpinboxLabel = QtGui.QLabel("Slice")
        self.sliceSpinbox = QtGui.QSpinBox(self)
        self.sliceSpinbox.setEnabled(False)
        sliceItem = OverlayTreeWidgetItem(self.christophsDict[self.christophsDict.keys()[0]], "")
        self.sliceValue = (sliceItem.item._data.shape[1]-1)/2
        self.sliceSpinbox.setMaximum(sliceItem.item._data.shape[1]-1)
        self.sliceSpinbox.setValue(self.sliceValue)
        self.connect(self.sliceSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.sliceSpinboxValueChanged)
        grviewSpinboxLayout.addWidget(self.channelSpinboxLabel)
        grviewSpinboxLayout.addWidget(self.channelSpinbox)
        grviewSpinboxLayout.addStretch()
        grviewSpinboxLayout.addWidget(self.sliceSpinboxLabel)
        grviewSpinboxLayout.addWidget(self.sliceSpinbox)
        grviewSpinboxLayout.addStretch()
        previewLayout.addWidget(self.grview)
        previewLayout.addLayout(grviewSpinboxLayout)
        previewGroupBox.setLayout(previewLayout)

        infoGroupBox = QtGui.QGroupBox("Information")
        infoLayout = QtGui.QVBoxLayout()
        self.overlayItemLabel = QtGui.QLabel()
        self.overlayItemLabel.setWordWrap(True)
        self.overlayItemLabel.setAlignment(QtCore.Qt.AlignTop)
        self.overlayItemSizeLabel = QtGui.QLabel("Size: 123 bytes")
        self.overlayItemPageOutLabel = QtGui.QLabel("Memory/Hard drive")
        infoLayout.addWidget(self.overlayItemLabel)
        infoLayout.addWidget(self.overlayItemPageOutLabel)
        infoGroupBox.setLayout(infoLayout)

        rightLayout.addWidget(previewGroupBox)
        rightLayout.addWidget(infoGroupBox)
        splitter.addWidget(treeGroupBoxLayout)
        w = QWidget()
        w.setLayout(rightLayout)
        splitter.addWidget(w)
        
        tempLayout = QtGui.QHBoxLayout()
        self.cancelButton = QtGui.QPushButton("&Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.cancel)
        self.addSelectedButton = QtGui.QPushButton("&Add Selected")
        self.addSelectedButton.setEnabled(False)
        self.addSelectedButton.setDefault(True)
        self.connect(self.addSelectedButton, QtCore.SIGNAL('clicked()'), self.addSelected)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.addSelectedButton)
        
        if self.singleOverlaySelection == True:
            self.setWindowTitle("Overlay Single Selection")
            self.overlayItemLabel.setText("Single Selection Mode")
        else:
            self.setWindowTitle("Overlay Multi Selection")
            self.overlayItemLabel.setText("Multi Selection Mode")
            self.treeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        self.layout.addWidget(splitter)
        self.layout.addLayout(tempLayout)
        
        self.addOverlaysToTreeWidget()
        self.treeWidget.expandAll()
        self.treeWidgetExpanded = True
        
    # methods
    # ------------------------------------------------
    def wheelEvent(self, event):
        if self.grview.underMouse():
            if event.delta() > 0:
                self.sliceSpinbox.setValue(self.sliceSpinbox.value() + 1)
            elif event.delta() < 0:
                self.sliceSpinbox.setValue(self.sliceSpinbox.value() - 1)

    
    def addOverlaysToTreeWidget(self):
        testItem = QtGui.QTreeWidgetItem("a")
        for keys in self.christophsDict.keys():
            if self.christophsDict[keys] in self.forbiddenOverlays:
                continue
            else:
                boolStat = False
                split = keys.split("/")
            for i in range(len(split)):
                if len(split) == 1:
                    newItemsChild = OverlayTreeWidgetItem(self.christophsDict[keys], keys)
                    self.treeWidget.addTopLevelItem(newItemsChild)                   
                    boolStat = False
                    if self.christophsDict[keys] in self.preSelectedOverlays:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
                elif i+1 == len(split) and len(split) > 1:
                    newItemsChild = OverlayTreeWidgetItem(self.christophsDict[keys], keys)
                    testItem.addChild(newItemsChild)
                    if self.christophsDict[keys] in self.preSelectedOverlays:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
                elif self.treeWidget.topLevelItemCount() == 0 and i+1 < len(split):
                    newItem = QtGui.QTreeWidgetItem([split[i]])
                    self.treeWidget.addTopLevelItem(newItem)
                    testItem = newItem
                    boolStat = True
                    
                elif self.treeWidget.topLevelItemCount() != 0 and i+1 < len(split):
                    if boolStat == False:
                        for n in range(self.treeWidget.topLevelItemCount()):
                            if self.treeWidget.topLevelItem(n).text(0) == split[i]:
                                testItem = self.treeWidget.topLevelItem(n)
                                boolStat = True
                                break
                            elif n+1 == self.treeWidget.topLevelItemCount():
                                newItem = QtGui.QTreeWidgetItem([split[i]])
                                self.treeWidget.addTopLevelItem(newItem)
                                testItem = newItem
                                boolStat = True
                        
                    elif testItem.childCount() == 0:
                        newItem = QtGui.QTreeWidgetItem([split[i]])
                        testItem.addChild(newItem)
                        testItem = newItem
                        boolStat = True
                    else:
                        for x in range(testItem.childCount()):
                            if testItem.child(x).text(0) == split[i]:
                                testItem = testItem.child(x)
                                boolStat = True
                                break
                            elif x+1 == testItem.childCount():
                                newItem = QtGui.QTreeWidgetItem([split[i]])
                                testItem.addChild(newItem)
                                testItem = newItem
                                boolStat = True


    def treeItemChanged(self, item, column):
        currentItem = item
        it = OverlayTreeWidgetIter(self.treeWidget, QtGui.QTreeWidgetItemIterator.Checked)
        i = 0
        while (it.value()):
            if self.singleOverlaySelection == True and currentItem.checkState(column) == 2:
                if it.value() != currentItem:
                    it.value().setCheckState(0, 0)
            it.next()
            i += 1
        if i == 0:
            self.addSelectedButton.setEnabled(False)
        else:
            self.addSelectedButton.setEnabled(True)


    def drawPreview(self):
        currentItem = self.treeWidget.currentItem()
        if self.pixmapImage is not None:
            self.grscene.removeItem(self.pixmapImage)
            
        item = currentItem.item
        
        if isinstance(currentItem, OverlayTreeWidgetItem):
            itemdata = imageArray = currentItem.item._data[0, self.sliceValue, :, :, currentItem.item.channel]
            if item.getColorTab() is not None:
                if item.dtype != 'uint8':
                    """
                    if the item is larger we take the values module 256
                    since QImage supports only 8Bit Indexed images
                    """
                    olditemdata = itemdata           
                    itemdata = numpy.ndarray(olditemdata.shape, 'uint8')
                    if olditemdata.dtype == 'uint32':
                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
                    elif olditemdata.dtype == 'uint64':
                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
                    elif olditemdata.dtype == 'int32':
                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
                    elif olditemdata.dtype == 'int64':
                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
                    elif olditemdata.dtype == 'uint16':
                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,8),8)[:]
                    else:
                        raise TypeError(str(olditemdata.dtype) + ' <- unsupported image _data type (in the rendering thread, you know) ')
                   
                if len(itemdata.shape) > 2 and itemdata.shape[2] > 1:
                    image0 = qimage2ndarray.array2qimage(itemdata, normalize=False)
                else:
                    image0 = qimage2ndarray.gray2qimage(itemdata, normalize=False)
                    image0.setColorTable(item.getColorTab() [:])
                self.pixmapImage = self.grscene.addPixmap(QtGui.QPixmap.fromImage(image0))
            else:
                
                if currentItem.item.min is not None:
                    self.pixmapImage = self.grscene.addPixmap(QtGui.QPixmap(qimage2ndarray.gray2qimage(imageArray, normalize = (currentItem.item.min, currentItem.item.max))))
                else:
                    self.pixmapImage = self.grscene.addPixmap(QtGui.QPixmap(qimage2ndarray.gray2qimage(imageArray)))
            self.grview.setScene(self.grscene)


    def treeItemSelectionChanged(self):
        currentItem = self.treeWidget.currentItem()
        if isinstance(currentItem, OverlayTreeWidgetItem):
            self.overlayItemLabel.setText(currentItem.item.key)
            self.channelSpinbox.setEnabled(True)
            self.sliceSpinbox.setEnabled(True)
            self.drawPreview()
            self.channelSpinbox.setValue(currentItem.item.channel)
        else:
            self.channelSpinbox.setEnabled(False)
            self.sliceSpinbox.setEnabled(False)
            self.overlayItemLabel.setText(self.treeWidget.currentItem().text(0))


    def scaleUp(self):
        if self.scaleNext == 8:
            self.grview.resetTransform()
            self.grview.scale(self.scaleNext, self.scaleNext)
            self.zoomScaleLabel.setText(str(self.scaleNext * 100) + "%")
            self.scaleIndex = 14
            self.scalePrev = self.scaleList[self.scaleIndex - 1]
        else:
            self.grview.resetTransform()
            self.grview.scale(self.scaleNext, self.scaleNext)
            self.zoomScaleLabel.setText(str(self.scaleNext * 100) + "%")
            self.scalePrev = self.scaleList[self.scaleIndex]
            self.scaleIndex +=1
            self.scaleNext = self.scaleList[self.scaleIndex+1]


    def clickOnLabel(self):
        self.grview.resetTransform()
        self.zoomScaleLabel.setText("100%")
        self.scaleIndex = 7
        self.scalePrev = self.scaleList[self.scaleIndex-1]
        self.scaleNext = self.scaleList[self.scaleIndex+1]


    def scaleDown(self):
        if self.scalePrev == 0.1:
            self.grview.resetTransform()
            self.grview.scale(self.scalePrev, self.scalePrev)
            self.zoomScaleLabel.setText(str(self.scalePrev * 100) + "%")
            self.scaleIndex = 0
            self.scaleNext = self.scaleList[self.scaleIndex+1]
        else:
            self.grview.resetTransform()
            self.grview.scale(self.scalePrev, self.scalePrev)
            self.zoomScaleLabel.setText(str(self.scalePrev * 100) + "%")
            self.scalePrev = self.scaleList[self.scaleIndex-2]
            self.scaleIndex -=1
            self.scaleNext = self.scaleList[self.scaleIndex+1]


    def channelSpinboxValueChanged(self, value):
        currentItem = self.treeWidget.currentItem()
        if currentItem.item._data.shape[-1]-1 >= value:
            self.treeWidget.currentItem().item.channel = value
            self.drawPreview()
        else:
            self.channelSpinbox.setValue(currentItem.item._data.shape[-1]-1)


    def sliceSpinboxValueChanged(self, value):
        self.sliceValue = value
        self.drawPreview()


    def expandOrCollapse(self):
        if self.treeWidgetExpanded == True:
            self.collapseAll()
            self.expandCollapseButton.setText('Expand All')
            self.treeWidgetExpanded = False
        else:
            self.expandAll()
            self.treeWidgetExpanded = True
            self.expandCollapseButton.setText('Collapse All')
            
    

    def collapseAll(self):
        self.treeWidget.collapseAll()
    

    def expandAll(self):
        self.treeWidget.expandAll()


    def createNew(self):
        dlg = OverlayCreateSelectionDlg(self.ilastik)
        answer = dlg.exec_()
        if answer is not None:
            dlg_creation = answer(self.ilastik)
            answer = dlg_creation.exec_()
            if answer is not None:
                name = QtGui.QInputDialog.getText(self,"Edit Name", "Please Enter the name of the new Overlay:", text = "Custom Overlays/My Overlay" )
                name = str(name[0])
                self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr[name] = answer
                self.cancel()



    def cancel(self):
        self.reject()


    def addSelected(self):
        it = OverlayTreeWidgetIter(self.treeWidget, QtGui.QTreeWidgetItemIterator.Checked)
        while (it.value()):
            self.selectedOverlaysList.append(it.value().item)
            self.selectedOverlayPaths.append(it.value().overlayPathName)
            it.next()
        self.accept()


    def spacePressedTreewidget(self):
        for item in self.treeWidget.selectedItems():
            if item.childCount() == 0:
                if item.checkState(0) == 0:
                    item.setCheckState(0, 2)
                else: 
                    item.setCheckState(0, 0)


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.selectedOverlaysList
        else:
            return []
