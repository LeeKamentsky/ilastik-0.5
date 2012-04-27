#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2011 L Fiaschi, T Kroeger, C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

import __builtin__
from setuptools import setup
import os
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Copied from install-ilastik-deps.py ==> move to common place

__builtin__.installDir = "/ilastik"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APP = [installDir + '/ilastik/ilastik/ilastikMain.py']
DATA_FILES = [  #installDir+'/plugins/imageformats/libqtiff.dylib',
                #installDir+'/plugins/imageformats/libqjpeg.dylib',
                installDir+"/lib/qt_menu.nib",
                installDir+"/vigra-ilastik-05/lib/libvigraimpex.3.dylib",
                installDir+"/vigra-ilastik-05/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/vigra/vigranumpycore.so",
                installDir+"/lib/libvtkCommonPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkPythonCore.5.10.0.dylib",
                installDir+"/lib/libvtkCommon.5.10.0.dylib",
                installDir+"/lib/libvtkPythonCore.5.10.0.dylib",
                installDir+"/lib/libvtksys.5.10.0.dylib",
                installDir+"/lib/libvtkFilteringPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkFiltering.5.10.0.dylib",
                installDir+"/lib/libvtkIOPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkIO.5.10.0.dylib",
                installDir+"/lib/libvtkDICOMParser.5.10.0.dylib",
                installDir+"/lib/libvtkNetCDF.5.10.0.dylib",
                installDir+"/lib/libvtkNetCDF_cxx.dyli/libb",
                installDir+"/lib/libvtkmetaio.5.10.0.dylib",
                installDir+"/lib/libvtksqlite.5.10.0.dylib",
                installDir+"/lib/libvtkpng.5.10.0.dylib",
                installDir+"/lib/libvtkzlib.5.10.0.dylib",
                installDir+"/lib/libvtkjpeg.5.10.0.dylib",
                installDir+"/lib/libvtktiff.5.10.0.dylib",
                installDir+"/lib/libvtkexpat.5.10.0.dylib",
                installDir+"/lib/libvtkImagingPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkImaging.5.10.0.dylib",
                installDir+"/lib/libvtkGraphicsPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkGraphics.5.10.0.dylib",
                installDir+"/lib/libvtkverdict.5.10.0.dylib",
                installDir+"/lib/libvtkGenericFilteringPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkGenericFiltering.5.10.0.dylib",
                installDir+"/lib/libvtkRenderingPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkRendering.5.10.0.dylib",
                installDir+"/lib/libvtkftgl.5.10.0.dylib",
                installDir+"/lib/libvtkfreetype.5.10.0.dylib",
                installDir+"/lib/libvtkVolumeRenderingPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkVolumeRendering.5.10.0.dylib",
                installDir+"/lib/libvtkHybridPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkHybrid.5.10.0.dylib",
                installDir+"/lib/libvtkexoIIc.5.10.0.dylib",
                installDir+"/lib/libvtkWidgetsPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkWidgets.5.10.0.dylib",
                installDir+"/lib/libvtkChartsPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkCharts.5.10.0.dylib",
                installDir+"/lib/libvtkViewsPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkViews.5.10.0.dylib",
                installDir+"/lib/libvtkInfovisPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkInfovis.5.10.0.dylib",
                installDir+"/lib/libvtklibxml2.5.10.0.dylib",
                installDir+"/lib/libvtkalglib.5.10.0.dylib",
                installDir+"/lib/libvtkGeovisPythonD.5.10.0.dylib",
                installDir+"/lib/libvtkGeovis.5.10.0.dylib",
                installDir+"/lib/libvtkproj4.5.10.0.dylib",
                installDir+"/lib/libvtkQtPythonD.dylib",
                installDir+"/lib/libQVTKWidgetPlugin.dylib",
                installDir+"/lib/libQVTK.dylib",
                installDir+"/lib/libQVTK.5.10.0.dylib",
                installDir+"/lib/libQVTK.5.10.0.dylib",
                installDir+"/lib/vtkQtPython.so",
                installDir+"/lib/QVTKPython.so",
                installDir+"/lib/libboost_python.dylib",
                installDir+"/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/VTK-5.10.0-py2.7.egg/vtk/vtkCommonPython.so",
                installDir+"/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/VTK-5.10.0-py2.7.egg/vtk/vtkCommonPythonSIP.so",
            ]
            

OPTIONS = {'argv_emulation': False,
           'packages':['PyQt4'],
           'includes':[\
                'distutils', 'sip', 'ctypes','ctypes.util','h5py._conv','h5py.utils',
                # http://permalink.gmane.org/gmane.comp.python.enthought.devel/26705
                # The backends are dynamically imported and thus we need to
                # tell py2app about them.
                # Essential entries for bundling PyQt
                'PyQt4.pyqtconfig', 'PyQt4.uic','PyQt4.QtCore','PyQt4.QtGui',
                'site', 'os','vtk',
                'vtk.vtkCommonPythonSIP',
                #'vtk.vtkFilteringPythonSIP',
                'vtk.vtkRenderingPythonSIP',
                'vtk.vtkFilteringPythonSIP',
                'numpy.core.multiarray',
                'vigra', 'h5py._proxy', 'csv', #'vigra.svs',
                'enthought',
                'enthought.qt',
                'enthought.pyface.*',
                'enthought.pyface.ui.qt4.*',
                'enthought.pyface.ui.qt4.action.*',
                'enthought.pyface.ui.qt4.timer.*',
                'enthought.pyface.ui.qt4.wizard.*',
                'enthought.pyface.ui.qt4.workbench.*',
                'enthought.pyface.action.*',
                'enthought.pyface.toolkit',
                'enthought.traits',
                'enthought.traits.api',
                'enthought.traits.ui.*',
                'enthought.traits.ui.qt4.*',
                'enthought.traits.ui.qt4.extra.*',
                'enthought.pyface.ui.null',
                'enthought.pyface.ui.null.action.*',
                'qimage2ndarray',
                #New Graph stuff
                'greenlet',
                'psutil',
             ],
            'frameworks': [],
          }

class ilastik_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('ilastik')
        if m is None:
            return None
        
        return dict(
            packages=['ilastik'],
            prescripts=['osx-bundle-pre-launch.py']
        )

import py2app.recipes
py2app.recipes.ilastik   = ilastik_recipe()

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    iconfile='appIcon.icns',
)