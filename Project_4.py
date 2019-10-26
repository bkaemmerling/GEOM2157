# Import PyQGIS libraries
from qgis.core import *
import qgis.utils
import processing
import sys
from PyQt5.QtCore import QVariant


# Set variables for file path and filename
filepath = '/Users/Babor/Documents/UNI/Geospatial Programming GEOM2157/Project/ProjectData/'
footprint = 'ConstructionFootprint.shp'
trees = 'Trees.shp'

# Add vector layers to be used in the analysis
Footprint = iface.addVectorLayer((filepath + footprint), '', 'ogr')
Trees = iface.addVectorLayer((filepath + trees), '', 'ogr')

# Reproject layers to VICGRID 
processing.run("native:reprojectlayer", 
    {'INPUT': filepath + footprint,
    'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3111'),
    'OUTPUT': filepath + 'ConstructionFootprint_VICGRID.shp'})
FootprintVG = iface.addVectorLayer((filepath + 'ConstructionFootprint_VICGRID.shp'), '', 'ogr')

processing.run("native:reprojectlayer", 
    {'INPUT': filepath + trees,
    'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3111'),
    'OUTPUT': filepath + 'Trees_VICGRID.shp'})
TreesVG = iface.addVectorLayer((filepath + 'Trees_VICGRID.shp'), '', 'ogr')


# Add Tree Protection Zone (TPZ) and Tree Impact fields
TreesVG = iface.activeLayer()

TreesVG.startEditing()
TreesVG.dataProvider().addAttributes([QgsField('TPZ', QVariant.Double)])
TreesVG.dataProvider().addAttributes([QgsField('TreeImpact', QVariant.String)])
TreesVG.updateFields()


# Store the position (index) of each of the TPZ fields in a variable
idx1 = TreesVG.dataProvider().fieldNameIndex('TPZ')

# Calculates the Tree Protection Zone in metres by multiplying the measured Diameter at Breast Height (DBH) by 0.12
for tree in TreesVG.getFeatures():
    DBHindex = TreesVG.dataProvider().fieldNameIndex('DBH')
    DBH = (tree.attributes()[DBHindex])
    # Calculate TPZ field 
    tree[idx1] = DBH*0.12
    TreesVG.updateFeature(tree)
TreesVG.commitChanges()

# Use variable distance buffer to create TPZ geometry using SAGA tool
processing.run("saga:variabledistancebuffer", 
    {'SHAPES': filepath + 'Trees_VICGRID.shp',
    'DIST_FIELD':'TPZ',
    'DIST_SCALE':1,
    'NZONES':1,
    'DARC':5,
    'DISSOLVE       ':False,
    'POLY_INNER       ':False,
    'BUFFER': filepath + 'TPZ_Buffer_VICGRID.shp'})
TPZbuffer = iface.addVectorLayer((filepath + 'TPZ_Buffer_VICGRID.shp'), '', 'ogr')

# Add TPZ area field and Intersect Area field
TPZbuffer = iface.activeLayer()

TPZbuffer.startEditing()
TPZbuffer.dataProvider().addAttributes([QgsField('TPZ_Area', QVariant.Double)])
TPZbuffer.dataProvider().addAttributes([QgsField('Int_Area', QVariant.Double)])
TPZbuffer.dataProvider().addAttributes([QgsField('PC_Int', QVariant.Double)])
TPZbuffer.updateFields()

# Store the position (index) of each of the added fields in a variable
'''
idx2 = TPZbuffer["TreeImpact"]
idx3 = TPZbuffer["TPZ_Area"]
idx4 = TPZbuffer["Int_Area"]
idx5 = TPZbuffer["PC_Int]
'''


idx2 = TPZbuffer.dataProvider().fieldNameIndex('TreeImpact')
idx3 = TPZbuffer.dataProvider().fieldNameIndex('TPZ_Area')
idx4 = TPZbuffer.dataProvider().fieldNameIndex('Int_Area')
idx5 = TPZbuffer.dataProvider().fieldNameIndex('PC_Int')


# Intersects the TPZ buffers with the construction footprint

TPZ_features = TPZbuffer.getFeatures(QgsFeatureRequest())
FP_features = FootprintVG.getFeatures(QgsFeatureRequest())


for footprint in FP_features:
    for TPZ in TPZ_features:
        if TPZ.geometry().intersects(footprint.geometry()):
            TPZAREA = TPZ.geometry().area()
            INTAREA = TPZ.geometry().intersection(footprint.geometry()).area()
            PCINT = (INTAREA/TPZAREA)*100
        else:
            TPZAREA = TPZ.geometry().area()
            INTAREA = 0
            PCINT = 0
        print (TPZAREA, INTAREA)
        TPZ[idx3] = TPZAREA
        TPZ[idx4] = INTAREA
        TPZ[idx5] = PCINT
        TPZbuffer.updateFeature(TPZ)
        if PCINT >10:
            TPZ[idx2] = 'Lost'
        else:
            TPZ[idx2] = 'Retained'
        TPZbuffer.updateFeature(TPZ)
TPZbuffer.commitChanges()


    
