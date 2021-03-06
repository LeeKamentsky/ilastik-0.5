from PyQt4 import QtGui

#*******************************************************************************
# s h o r t c u t M a n a g e r                                                *
#*******************************************************************************

class shortcutManager():
    def __init__(self):
        self.shortcuts = dict()
        
    def register(self, shortcut, group, description):
        if not group in self.shortcuts:
            self.shortcuts[group] = dict()
        self.shortcuts[group][shortcut.key().toString()] = description
        
    def showDialog(self, parent=None):
        dlg = shortcutManagerDlg(self, parent)

#*******************************************************************************
# s h o r t c u t M a n a g e r D l g                                          *
#*******************************************************************************

class shortcutManagerDlg(QtGui.QDialog):
    def __init__(self, s, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(False)
        self.setWindowTitle("Shortcuts")
        self.setMinimumWidth(500)
        if len(s.shortcuts)>0:
            tempLayout = QtGui.QVBoxLayout()
            
            for group in s.shortcuts.keys():
                grpBox = QtGui.QGroupBox(group)
                l = QtGui.QGridLayout(self)
                
                for i, sc in enumerate(s.shortcuts[group]):
                    desc = s.shortcuts[group][sc]
                    l.addWidget(QtGui.QLabel(str(sc)), i,0)
                    l.addWidget(QtGui.QLabel(desc), i,1)
                grpBox.setLayout(l)
                tempLayout.addWidget(grpBox)
            
            self.setLayout(tempLayout)
            self.show()
        else:
            l = QtGui.QVBoxLayout()
            l.addWidget(QtGui.QLabel("Load the data by pressing the \"New\" button in the project dialog"))
            self.setLayout(l)
            self.show()
            
shortcutManager = shortcutManager()