'''
This is version 1.0.0 of the Face Control Projection Tool.
Documentation for this tool can be found in the included README.rtf file.
Alternatively the same documentation is at http://thatcgguy.com/controlProjectionTool-documentation

This tool is not to be redistributed without prior written consent by Guy Sartorelli
Guy can be reached using the contact form on http://thatcgguy.com/
'''

import maya.cmds as mc
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import os.path
from functools import partial
import ConfigParser as cp
import maya.mel as mel



class FaceControlTool():
    
    def __init__(self):
        self.shapes = {}
        self.windowName = 'faceControlToolUI'
    
    def UI(self):
        
        def setupLabel(section):
            if section == 'mirror':
                mc.separator(h=10, style='none')
            else:
                mc.separator(h=18, style='none')
            mc.rowColumnLayout(nc=1, cw=[(1, 390)])
            mc.text(label='{0} options'.format(section), fn='smallBoldLabelFont', align='left')
            mc.separator(h=5, style='in')
            mc.setParent(u=1)
        
        # get preferred default settings
        self.settings('get')
        # get hover-over documentation annotations
        self.annotations()
        
        # define UI variables
        self.widgets = {}
        self.uiHeight = 505
        
        # delete and redefine window
        self.closeWindow()
        self.widgets['window'] = mc.window(self.windowName, w=390, h=self.uiHeight, s=0, title="Face Control Tool", menuBar=1, cc=self.closeWin)
        # force window size
        mc.window(self.widgets['window'], e=1, w=390, h=self.uiHeight)
        
        # tool settings and documentation
        mc.menu(label='Tool Settings')
        mc.menuItem(label='Restore Default settings', c=partial(self.settings, 'restore'))
        mc.menuItem(label='Save Tool Settings', c=partial(self.settings, 'save'))
        self.widgets['saveAutomatically'] = mc.menuItem(label='Save Tool Settings Automatically', checkBox=self.saveAutomatically)
        mc.menu(label='Tool Help', helpMenu=1)
        mc.menuItem(label='View Documentation', c=self.documentation)
        
        # define main layout
        mc.columnLayout(w=390, h=self.uiHeight)
        
        setupLabel('mirror')
        
        # mirror check boxes X,Y,Z (can tick more than one) and mirror transform check boxes
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        self.widgets['mirrorX'] = mc.checkBox(label='Mirror Across X ', value=self.mirror['X'], ann=self.ann['mirrorX'])
        self.widgets['mirrorTX'] = mc.checkBox(label='Mirror X Transform ', value=self.mirrorT['X'], ann=self.ann['mirrorTX'])
        self.widgets['mirrorY'] = mc.checkBox(label='Mirror Across Y ', value=self.mirror['Y'], ann=self.ann['mirrorY'])
        self.widgets['mirrorTY'] = mc.checkBox(label='Mirror Y Transform ', value=self.mirrorT['Y'], ann=self.ann['mirrorTY'])
        self.widgets['mirrorZ'] = mc.checkBox(label='Mirror Across Z ', value=self.mirror['Z'], ann=self.ann['mirrorZ'])
        self.widgets['mirrorTZ'] = mc.checkBox(label='Mirror Z Transform ', value=self.mirrorT['Z'], ann=self.ann['mirrorTZ'])
        mc.separator(h=10, style='none')
        mc.separator(h=10, style='none')
        
        # mirroring center offset values
        mc.text(label='Mirroring Center Offsets: ', align='left')
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=6, cw=[(1, 30), (2, 90), (3, 30), (4, 90), (5, 30), (6, 90)], co=[(1, 'left', 5), (2, 'left', 5), (3, 'left', 5), (4, 'left', 5), (5, 'left', 5), (6, 'both', 5)])
        mc.text(label='X: ')
        self.widgets['mirrorOffsetX'] = mc.floatField('mirrorOffsetX', value=self.mirrorZero['X'], precision=3, cc=partial(self.updateMirrorPos, 'X'), ann=self.ann['offsetX'])
        mc.text(label='Y: ')
        self.widgets['mirrorOffsetY'] = mc.floatField('mirrorOffsetY', value=self.mirrorZero['Y'], precision=3, cc=partial(self.updateMirrorPos, 'Y'), ann=self.ann['offsetY'])
        mc.text(label='Z: ')
        self.widgets['mirrorOffsetZ'] = mc.floatField('mirrorOffsetZ', value=self.mirrorZero['Z'], precision=3, cc=partial(self.updateMirrorPos, 'Z'), ann=self.ann['offsetZ'])
        # mirror helper buttons
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 120), (2, 120), (3, 130)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.button(label='X Axis Mirror Helper', c=partial(self.createMirrorHelper, 'X', False), ann=self.ann['helperX'])
        mc.button(label='Y Axis Mirror Helper', c=partial(self.createMirrorHelper, 'Y', False), ann=self.ann['helperY'])
        mc.button(label='Z Axis Mirror Helper', c=partial(self.createMirrorHelper, 'Z', False), ann=self.ann['helperZ'])
        
        # define center falloff and snapping options (NOTE: Will apply regardless of mirroring)
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 120), (2, 120), (3, 130)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.separator(h=10, style='none')
        mc.separator(h=10, style='none')
        mc.separator(h=10, style='none')
        self.widgets['centerSnapX'] = mc.checkBox(label='Snap To Center X', value=self.centerSnap['X'], ann=self.ann['snapX'])
        self.widgets['centerSnapY'] = mc.checkBox(label='Snap To Center Y', value=self.centerSnap['Y'], ann=self.ann['snapY'])
        self.widgets['centerSnapZ'] = mc.checkBox(label='Snap To Center Z', value=self.centerSnap['Z'], ann=self.ann['snapZ'])
        mc.text(label='Falloff To Center:', align='left')
        self.widgets['centerFalloff'] = mc.floatField(min=0.0, max=5, value=self.centerFalloff, precision=1, ann=self.ann['snapFalloff'])
        mc.setParent(u=1)
        
        
        setupLabel('control')
        
        # set space for control options
        mc.rowColumnLayout(nc=3, cw=[(1, 100), (2, 170), (3, 100)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.text(label="Control Shape:", align='right')
        # dropdown for control shape (with some presets already) #button to add selected shape to dropdown(dialog box to name ctrl shape or just use this once)
        self.widgets['shapesDropdown'] = mc.optionMenu(label='', ann=self.ann['ctrlShape'])
        mc.button(label='<<<', c=self.addShape, w=90, ann=self.ann['ctrlAdd'])
        # populate shapes dropdown
        self.populateDropdown()
        if self.ctrlShape in self.shapes:
            mc.optionMenu(self.widgets['shapesDropdown'], e=1, v=self.ctrlShape)
        else:
            mc.warning("Preferred shape {0} doesn't exist. Please re-save your settings.".format(self.ctrlShape))
        mc.setParent(u=1)
        # set ctrl size
        self.widgets['sizeSlider'] = mc.floatSliderGrp(label="Control Size:", ct3=('left','both','right'), co3=(5,5,5), cw3=(100,50,215),
                                     field=1, v=self.ctrlSize, min=0.01, max=5.0, fieldMaxValue=1000, precision=2, ann=self.ann['ctrlSize'])
        # set UI parent to main layout
        mc.separator(h=2.5, style='none')
        # slider for control color - values Maya uses for drawing overrides are in the 1-31 range.
        self.widgets['colorSlider'] = mc.colorIndexSliderGrp(label='Control Color:', ct3=('left','both','right'), co3=(5,5,5), cw3=(100,50,215),
                                      min=1, max=32, value=self.ctrlColor+1, ann=self.ann['ctrlColor'])
        
        
        setupLabel('hierarchy')
        
        # hierarchy options
        mc.rowColumnLayout(nc=1, cw=[(1, 380)], co=[(1, 'both', 5)])
        mc.text(label="Control System Parent Object: ", align='left')
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 125), (2, 120), (3, 125)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        # radio buttons to define parent object
        self.widgets['parentRadio'] = mc.radioCollection()
        mc.radioButton('world', label='World', ann=self.ann['parentWorld'])
        mc.radioButton('existing', label='Existing Transform', ann=self.ann['parentExisting'])
        mc.radioButton('new', label='New Group', sl=1, ann=self.ann['parentNew'])
        mc.radioCollection(self.widgets['parentRadio'], e=1, select=self.parentSpace)
        
        # define existing parent transform object
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=2, cw=[(1, 280), (2, 100)], co=[(1, 'both', 5), (2, 'both', 5)])
        self.widgets['parentExistingTextfield'] = mc.textField(pht="Define Existing Parent Transform", ann=self.ann['parentDefine'])
        self.widgets['parentExistingButton'] = mc.button(label='<<<', c=self.populateTextField, ann=self.ann['parentDefineButton'])
        
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=4, cw=[(1, 140), (2, 50), (3, 90), (4, 110)], co=[(1, 'left', 5), (2, 'left', 5), (3, 'left', 1), (4, 'right', 5)])
        # checkbox to make offset group
        self.widgets['offsetCheckbox'] = mc.checkBox(label='Create Offset Group ', value=self.makeOffset, ann=self.ann['createOffset'])
        # integer field for SDK null groups
        self.widgets['sdkNulls'] = mc.floatField(min=0, max=650, value=self.sdkNulls, precision=0, ann=self.ann['createSDK'])
        mc.text('Num SDK Groups')
        # checkbox to make joint
        self.widgets['jointCheckbox'] = mc.checkBox(label='Create Joint ', value=self.makeJnt, ann=self.ann['createJnt'])
        
        
        # set spacing for naming options
        mc.setParent(u=1)
        mc.separator(h=15, style='none')
        # collapsable layout for naming conventions
        self.widgets['namesLayout'] = mc.frameLayout(label="Naming Options", w=390, collapsable=1, collapse=1, cc=self.setWindowSize, ec=self.setWindowSize)
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        mc.separator(h=5, style='none')
        mc.separator(h=5, style='none')
        
        WIDTH = 380
        
        # textfield for parent name
        mc.text(label="New Group Name: ", align='right')
        self.widgets['prntNameField'] = mc.textField(text=self.parentName, ann=self.ann['parentNewName'])
        
        # textfield for offset name
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 190), (2, 95), (3, 95)], co=[(1, 'both', 5), (2, 'left', 5), (3, 'right', 5)])
        mc.text(label="Offset Group Prefix / Suffix: ", align='right')
        self.widgets['offsetPrefixField'] = mc.textField(text=self.offsetPrefix, ann=self.ann['offsetPrefix'])
        self.widgets['offsetSuffixField'] = mc.textField(text=self.offsetSuffix, ann=self.ann['offsetSuffix'])
        
        # textfields for sdk name
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 190), (2, 160), (3, 30)], co=[(1, 'both', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.text(label="SDK Group Suffix / Sequencer: ", align='right')
        self.widgets['sdkNameField'] = mc.textField(text=self.sdkName, ann=self.ann['sdkSuffix'])
        self.widgets['sdkSuffixField'] = mc.textField(text=self.sdkSuffix, cc=self.snipSdkSuffix, ann=self.ann['sdkSequence'])

        # textfield for ctrl name
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        mc.text(label="Control Name: ", align='right')
        self.widgets['ctrlNameField'] = mc.textField(text=self.ctrlName, ann=self.ann['ctrlName'])
        
        # textfield for joint name
        mc.text(label="Joint Name: ", align='right')
        self.widgets['jntNameField'] = mc.textField(text=self.jntName, ann=self.ann['jntName'])
        
        
        # checkbox and text fields for adding prefixes for mirroring X
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 90), (2, 200), (3, 90)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.separator(h=15, style='none'), mc.separator(h=15, style='none'), mc.separator(h=15, style='none')
        mc.text(label='')
        self.widgets['prefixXCheckBox'] = mc.checkBox(label="Add Prefix When Mirroring Across X ", value=self.prefix['X'])
        mc.text(label='')
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        mc.text(label="Positive Prefix: ", align='right')
        self.widgets['prefixXPosTextfield'] = mc.textField(text=self.prefix['XPos'], ann=self.ann['prefixXPos'])
        mc.text(label="Negative Prefix: ", align='right')
        self.widgets['prefixXNegTextfield'] = mc.textField(text=self.prefix['XNeg'], ann=self.ann['prefixXNeg'])
        
        # checkbox and text fields for adding prefixes for mirroring Y
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 90), (2, 200), (3, 90)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.separator(h=10, style='none'), mc.separator(h=10, style='none'), mc.separator(h=10, style='none')
        mc.text(label='')
        self.widgets['prefixYCheckBox'] = mc.checkBox(label="Add Prefix When Mirroring Across Y ", value=self.prefix['Y'])
        mc.text(label='')
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        mc.text(label="Positive Prefix: ", align='right')
        self.widgets['prefixYPosTextfield'] = mc.textField(text=self.prefix['YPos'], ann=self.ann['prefixYPos'])
        mc.text(label="Negative Prefix: ", align='right')
        self.widgets['prefixYNegTextfield'] = mc.textField(text=self.prefix['YNeg'], ann=self.ann['prefixYNeg'])
        
        # checkbox and text fields for adding prefixes for mirroring Z
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=3, cw=[(1, 90), (2, 200), (3, 90)], co=[(1, 'left', 5), (2, 'both', 5), (3, 'right', 5)])
        mc.separator(h=10, style='none'), mc.separator(h=10, style='none'), mc.separator(h=10, style='none')
        mc.text(label='')
        self.widgets['prefixZCheckBox'] = mc.checkBox(label="Add Prefix When Mirroring Across Z ", value=self.prefix['Z'])
        mc.text(label='')
        mc.setParent(u=1)
        mc.rowColumnLayout(nc=2, cw=[(1, 190), (2, 190)], co=[(1, 'both', 5), (2, 'both', 5)])
        mc.text(label="Positive Prefix: ", align='right')
        self.widgets['prefixZPosTextfield'] = mc.textField(text=self.prefix['ZPos'], ann=self.ann['prefixZPos'])
        mc.text(label="Negative Prefix: ", align='right')
        self.widgets['prefixZNegTextfield'] = mc.textField(text=self.prefix['ZNeg'], ann=self.ann['prefixZNeg'])
        
        
        # define buttons layout
        mc.setParent(u=1)
        mc.setParent(u=1)
        mc.separator(h=10, style='none')
        mc.rowColumnLayout(nc=3, cw=[(1, 123), (2, 123), (3, 123)], co=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
        # define enter tool and close, enter tool, close buttons.
        mc.button(label='Enter Tool', c=partial(self.initTool, fromUI=True))
        mc.button(label='Enter Tool and Close', c=partial(self.initTool, True, True))
        mc.button(label='Close', c=self.closeWindow)
        
        
        # show window
        mc.showWindow(self.widgets['window'])
        
        # create script job for mirror helpers
        for axis in ['X', 'Y', 'Z']:
            self.createMirrorHelper(axis, onlySJ=True)
    
    
    
    def closeWindow(self, *args):
        #if not windowName:
        #    windowName = self.widgets['window']
        if mc.window(self.windowName, exists=True):
            mc.deleteUI(self.windowName, window=True)
    
    
    
    def setWindowSize(self, *args):
        #check Naming Options collapsed state
        collapsed = mc.frameLayout(self.widgets['namesLayout'], q=1, collapse=1)
        
        #set window height based on collapsed state
        if collapsed:
            mc.window(self.widgets['window'], e=1, h=self.uiHeight+20)
        else:
            mc.window(self.widgets['window'], e=1, h=self.uiHeight+405)
    
    
    
    def annotations(self):
        self.ann = {}
        
        self.ann['mirrorX'] = "Mirror control hierarchy across X axis"
        self.ann['mirrorY'] = "Mirror control hierarchy across Y axis"
        self.ann['mirrorZ'] = "Mirror control hierarchy across Z axis"
        self.ann['mirrorTX'] = "Mirror control hierarchy's transforms across X axis"
        self.ann['mirrorTY'] = "Mirror control hierarchy's transforms across Y axis"
        self.ann['mirrorTZ'] = "Mirror control hierarchy's transforms across Z axis"
        
        self.ann['offsetX'] = "Offset the center from which to mirror along the X axis"
        self.ann['offsetY'] = "Offset the center from which to mirror along the Y axis"
        self.ann['offsetZ'] = "Offset the center from which to mirror along the Z axis"
        self.ann['helperX'] = "Create a helper plane to visually represent the X axis mirror offset"
        self.ann['helperY'] = "Create a helper plane to visually represent the Y axis mirror offset"
        self.ann['helperZ'] = "Create a helper plane to visually represent the Z axis mirror offset"
        
        self.ann['snapX'] = "Snap control hierarchy to the center if within the falloff value on the X axis"
        self.ann['snapY'] = "Snap control hierarchy to the center if within the falloff value on the Y axis"
        self.ann['snapZ'] = "Snap control hierarchy to the center if within the falloff value on the Z axis"
        self.ann['snapFalloff'] = "Define the falloff value within which controls will snap to the center"
        
        self.ann['ctrlShape'] = "Choose a pre-defined shape for the control"
        self.ann['ctrlAdd'] = "Add the selected curve as a control shape"
        self.ann['ctrlSize'] = "Set the size of the control"
        self.ann['ctrlColor'] = "Set the color of the control using color index values"
        
        self.ann['parentWorld'] = "Parent new control hierarchies directly under the world"
        self.ann['parentExisting'] = "Parent new control hierarchies under an existing transform node"
        self.ann['parentNew'] = "Parent new control hierarchies under a new transform node"
        self.ann['parentDefine'] = "Insert the name of the existing transform node under which to parent new control hierarchies"
        self.ann['parentDefineButton'] = "Set selected transform node as the parent for new control hierarchies"
        self.ann['createOffset'] = "Create an offset group for the control"
        self.ann['createSDK'] = "Create a 'set driven key' group for the control (under the offset group)"
        self.ann['createJnt'] = "Create a joint parented under the control"
        
        self.ann['parentNewName'] = "Name of the new control hierarchy parent group"
        self.ann['offsetPrefix'] = "Prefix for control offset group"
        self.ann['offsetSuffix'] = "Suffix for control offset group"
        self.ann['sdkSuffix'] = "Suffix for 'set driven key' group"
        self.ann['sdkSequence'] = "Starting character (int or alphabet) if multiple 'set driven key' groups are created for one control"
        self.ann['ctrlName'] = "Name of the control"
        self.ann['jntName'] = "Name of the joint"
        
        self.ann['prefixXNeg'] = "Add this prefix to control heirarchies with negative X axis translate values"
        self.ann['prefixXPos'] = "Add this prefix to control heirarchies with positive X axis translate values"
        
        self.ann['prefixYNeg'] = "Add this prefix to control heirarchies with negative Y axis translate values"
        self.ann['prefixYPos'] = "Add this prefix to control heirarchies with positive Y axis translate values"
        
        self.ann['prefixZNeg'] = "Add this prefix to control heirarchies with negative Z axis translate values"
        self.ann['prefixZPos'] = "Add this prefix to control heirarchies with positive Z axis translate values"
    
    
    
    def documentation(self, *args):
        mc.launch(web="http://thatcgguy.com/controlProjectionTool-documentation")
        mel.eval('print "// If your web browser does not open automatically, please go to http://thatcgguy.com/controlProjectionTool-documentation\\n"')
    
    
    
    def createMirrorHelper(self, axis, onlySJ, *args):
        # define helper name
        obj = 'faceCtrl_MirrorHelper_{0}0'.format(axis)
        
        if not onlySJ:
            if mc.window(self.windowName, exists=True):
                pos = [mc.floatField(self.widgets['mirrorOffsetX'], q=1, v=1),
                       mc.floatField(self.widgets['mirrorOffsetY'], q=1, v=1),
                       mc.floatField(self.widgets['mirrorOffsetZ'], q=1, v=1)]
            else:
                pos = [0,0,0]
            
            # define orientation
            orientation = {'X' : [1,0,0], 'Y' : [0,1,0], 'Z' : [0,0,1]}
            
            # delete pre-existing helper
            if mc.objExists(obj):
                mc.delete(obj)
            
            # create and position helper object, and lock rotates
            mc.polyPlane(n=obj, ch=0, ax=orientation[axis], h=10, w=10, sx=1, sy=1)
            mc.xform(obj, t=pos, ws=1)
            for at in ['.rx', '.ry', '.rz']:
                mc.setAttr(obj+at, l=1, k=0)
            
            # activate checkboxes for the appropriate axis
            if mc.window(self.windowName, exists=True):
                mc.checkBox(self.widgets['mirror%s'%axis], e=1, value=1)
                mc.checkBox(self.widgets['centerSnap%s'%axis], e=1, value=1)
        
        def setMirrorOffset(self, axis, *args):
            transAx = {'X':0, 'Y':1, 'Z':2}
            obj = 'faceCtrl_MirrorHelper_{0}0'.format(axis)
            mc.floatField('mirrorOffset{0}'.format(axis), e=1, v=mc.xform(obj, t=1, ws=1, q=1)[transAx[axis]])
        
        # create script jobs to connect obj to offset field
        if mc.objExists(obj):
            if mc.window('faceControlToolUI', exists=True):
                setMirrorOffsetP = partial(setMirrorOffset, axis)
                mc.scriptJob(attributeChange=(obj+'.t%s'%axis.lower(), setMirrorOffsetP), ro=0, p='faceControlToolUI', rp=1)
    
    
    
    def updateMirrorPos(self, axis, *args):
        # updates mirror helper position based on offset values
        obj = 'faceCtrl_MirrorHelper_{0}0'.format(axis)
        if mc.objExists(obj):
            moveBy = mc.floatField(self.widgets['mirrorOffset{0}'.format(axis)], q=1, v=1)
            eval("mc.move(moveBy, obj, {0}=1, ws=1)".format(axis.lower()))
    
    
    
    def shapesIni(self, code=False, shapeName=False):
        # define and open shapes file
        shapesFile = os.path.dirname(__file__) + '/' + 'shapes.ini'
        shapesConfig = cp.ConfigParser()
        shapesConfig.optionxform = str
        shapesConfig.read(shapesFile)
        
        if code:
            shapesConfig.set('shapes', shapeName, code)
            with open(shapesFile, 'w') as configfile:
                shapesConfig.write(configfile)
        
        else:
            # unpack shapes.ini into shapes dict
            for option in shapesConfig.options('shapes'):
                self.shapes[option] = shapesConfig.get('shapes',option)
    
    
    
    def populateDropdown(self, *args):
        # unpack shapes file
        self.shapesIni()
        
        # get items already in optionMenu
        menuItems = mc.optionMenu(self.widgets['shapesDropdown'], itemListShort=1, q=1)
        
        # populate shapes dropdown (replace if already in dropdown to preserve order)
        for shape in self.shapes:
            if menuItems:
                if shape in menuItems:
                    mc.deleteUI(shape)
            mc.menuItem(shape, label=shape, parent=self.widgets['shapesDropdown'])
    
    
    
    def addShape(self, *args):
        
        # get items already in optionMenu
        menuItems = mc.optionMenu(self.widgets['shapesDropdown'], itemListShort=1, q=1)
        
        # get nurbs shapes and check if only curve or surface selected.
        sel = mc.ls(sl=1)
        if len(sel) < 1:
            mc.error("This feature currently only accepts a single nurbs curve.")
        selShapes = mc.listRelatives(c=1, s=1)
        shapeTypes = []
        
        ctrlCodeList = []
        for shape in selShapes:
            # check if object is nurbs curve
            shapeType = mc.nodeType(shape)
            shapeTypes.append(shapeType)
            if shapeType != 'nurbsCurve' or len(selShapes) > 1:
                mc.error("This feature currently only accepts a single nurbs curve.")
            
            # get CVs and convert to a nice number (3 decimal places)
            cvs = mc.getAttr(shape+'.cv[*]')
            cvsSimple = []
            for c in cvs:
                cvsSimple.append('(%.3f*self.ctrlSize' % c[0]+', %.3f*self.ctrlSize' % c[1]+', %.3f*self.ctrlSize)' % c[2])
            
            # generate shape construction code
            code = 'mc.curve(p='  
            code += '[%s]' % ',\n'.join(cvsSimple)
            code += ',d='+str(mc.getAttr(shape+'.degree'))+', n=self.ctrlName)'
            ctrlCodeList.append(code)
        
        # generate ctrl construction code from shapes code
        ctrlCode = "{'ctrl' : " + ctrlCodeList[0] + "}"
        
        
        while True:
            nameOption = mc.promptDialog(t='Name New Ctrl Shape', m='Enter Name:', b=['Save Shape', 'Use Shape w/o Saving', 'Cancel'],
                                         text=sel[0], db='OK', cb='Cancel', ds='Cancel')
            if nameOption != 'Cancel':
                shapeName = mc.promptDialog(query=True, text=True)
                #shapeName = shapeName.lower()
                
                # check if shape already in option box and confirm override
                if shapeName in menuItems:
                    override = mc.confirmDialog(t='Shape Already Exists', m="A shape named {0} already exists in the option box. Override existing shape?".format(shapeName),
                                     b=['Yes','No'], db='Yes', cb='No', ds='No')
                    if override == 'No':
                        continue
                    else:
                        mc.deleteUI(shapeName)
                
                # populate dropdown
                self.shapes[shapeName] = ctrlCode
                mc.menuItem(shapeName, label=shapeName, parent=self.widgets['shapesDropdown'])
                mc.optionMenu(self.widgets['shapesDropdown'], e=1, v=shapeName)
                
                if nameOption == 'Save Shape':
                    # save shape into presets
                    self.shapesIni(code=ctrlCode, shapeName=shapeName)
                break
                
            else:
                break
    
    
    
    def populateTextField(self, *args):
        # get selection
        try:
            sel = mc.ls(type='transform', sl=1, long=1)[0]
        except IndexError: #IndexError if 0 objects selected
            mc.error("Must select a transform.")
        
        # populate text field with selected transform
        mc.textField(self.widgets['parentExistingTextfield'], edit=1, text=sel)
        
        # select 'existing' radio button
        mc.radioCollection(self.widgets['parentRadio'], e=1, select='existing')
    
    
    
    def snipSdkSuffix(self, *args):
        # make sure sdk suffix is only 1 character long in UI
        currentText = mc.textField(self.widgets['sdkSuffixField'], text=1, q=1).strip()
        if currentText:
            mc.textField(self.widgets['sdkSuffixField'], text=currentText[0], e=1)
        else:
            mc.textField(self.widgets['sdkSuffixField'], text='0', e=1)
    
    
    
    def settings(self, mode, fromUI=False):
        # setup prefs file (option values are to be case sensitive)
        prefsFile = os.path.dirname(__file__) + '/' + 'prefs.ini'
        prefsConfig = cp.ConfigParser()
        prefsConfig.optionxform = str
        prefsConfig.read(prefsFile)
        
        if mode == 'get':
            # get options from UI
            if fromUI:
                # get mirroring options
                self.mirror = {}
                self.mirror['X'] = mc.checkBox(self.widgets['mirrorX'], q=1, value=1)
                self.mirror['Y'] = mc.checkBox(self.widgets['mirrorY'], q=1, value=1)
                self.mirror['Z'] = mc.checkBox(self.widgets['mirrorZ'], q=1, value=1)
                self.mirrorT = {}
                self.mirrorT['X'] = mc.checkBox(self.widgets['mirrorTX'], q=1, value=1)
                self.mirrorT['Y'] = mc.checkBox(self.widgets['mirrorTY'], q=1, value=1)
                self.mirrorT['Z'] = mc.checkBox(self.widgets['mirrorTZ'], q=1, value=1)
                self.centerFalloff = mc.floatField(self.widgets['centerFalloff'], q=1, value=1)
                self.centerSnap = {}
                self.centerSnap['X'] = mc.checkBox(self.widgets['centerSnapX'], q=1, v=1)
                self.centerSnap['Y'] = mc.checkBox(self.widgets['centerSnapY'], q=1, v=1)
                self.centerSnap['Z'] = mc.checkBox(self.widgets['centerSnapZ'], q=1, v=1)
                
                # get mirror offset values
                self.mirrorZero = {'X':0, 'Y':0, 'Z':0}
                axis = {'X':0, 'Y':1, 'Z':2}
                for ax in axis:
                    self.mirrorZero[ax] = mc.floatField(self.widgets['mirrorOffset{0}'.format(ax)], q=1, v=1)

                # get ctrl options
                self.ctrlShape = mc.optionMenu(self.widgets['shapesDropdown'], q=1, value=1)
                self.ctrlSize = mc.floatSliderGrp(self.widgets['sizeSlider'], q=1, v=1)
                self.ctrlColor = mc.colorIndexSliderGrp(self.widgets['colorSlider'], q=1, value=1) - 1
                
                # get hierarchy options
                self.makeOffset = mc.checkBox(self.widgets['offsetCheckbox'], q=1, value=1)
                self.sdkNulls = int(mc.floatField(self.widgets['sdkNulls'], q=1, value=1))
                self.makeJnt = mc.checkBox(self.widgets['jointCheckbox'], q=1, value=0)
                self.parentSpace = mc.radioCollection(self.widgets['parentRadio'], q=1, select=1) #'world', 'existing', 'new'
                self.parentObj = mc.textField(self.widgets['parentExistingTextfield'], q=1, text=1).strip()
                
                # get hierarchy naming options
                self.offsetPrefix = mc.textField(self.widgets['offsetPrefixField'], q=1, text=1).strip()
                self.offsetSuffix = mc.textField(self.widgets['offsetSuffixField'], q=1, text=1).strip()
                self.sdkName = mc.textField(self.widgets['sdkNameField'], q=1, text=1).strip()
                self.sdkSuffix = mc.textField(self.widgets['sdkSuffixField'], q=1, text=1).strip()
                self.ctrlName = mc.textField(self.widgets['ctrlNameField'], q=1, text=1).strip()
                self.jntName = mc.textField(self.widgets['jntNameField'], q=1, text=1).strip()
                self.parentName = mc.textField(self.widgets['prntNameField'], q=1, text=1).strip()
                
                self.prefix = {}
                # get mirror X naming options
                self.prefix['X'] = mc.checkBox(self.widgets['prefixXCheckBox'], q=1, value=1)
                self.prefix['XNeg'] = mc.textField(self.widgets['prefixXNegTextfield'], q=1, text=1).strip()
                self.prefix['XPos'] = mc.textField(self.widgets['prefixXPosTextfield'], q=1, text=1).strip()
                
                # get mirror Y naming options
                self.prefix['Y'] = mc.checkBox(self.widgets['prefixYCheckBox'], q=1, value=1)
                self.prefix['YNeg'] = mc.textField(self.widgets['prefixYNegTextfield'], q=1, text=1).strip()
                self.prefix['YPos'] = mc.textField(self.widgets['prefixYPosTextfield'], q=1, text=1).strip()
                
                # get mirror Z naming options
                self.prefix['Z'] = mc.checkBox(self.widgets['prefixZCheckBox'], q=1, value=1)
                self.prefix['ZNeg'] = mc.textField(self.widgets['prefixZNegTextfield'], q=1, text=1).strip()
                self.prefix['ZPos'] = mc.textField(self.widgets['prefixZPosTextfield'], q=1, text=1).strip()
                
                # get misc options
                self.saveAutomatically = mc.menuItem(self.widgets['saveAutomatically'], q=1, checkBox=True)
            
            
            # get options from INI
            else:
                self.mirror = {}
                self.centerSnap = {}
                # get mirroring X options
                if mc.objExists('faceCtrl_MirrorHelper_X0'):
                    self.mirror['X'] = 1
                    self.centerSnap['X'] = 1
                else:
                    self.mirror['X'] = prefsConfig.getboolean('prefs', "mirror['X']")
                    self.centerSnap['X'] = prefsConfig.getboolean('prefs', "centerSnap['X']")
                # get mirroring Y options
                if mc.objExists('faceCtrl_MirrorHelper_Y0'):
                    self.mirror['Y'] = 1
                    self.centerSnap['Y'] = 1
                else:
                    self.mirror['Y'] = prefsConfig.getboolean('prefs', "mirror['Y']")
                    self.centerSnap['Y'] = prefsConfig.getboolean('prefs', "centerSnap['Y']")
                # get mirroring Z options
                if mc.objExists('faceCtrl_MirrorHelper_Z0'):
                    self.mirror['Z'] = 1
                    self.centerSnap['Z'] = 1
                else:
                    self.mirror['Z'] = prefsConfig.getboolean('prefs', "mirror['Z']")
                    self.centerSnap['Z'] = prefsConfig.getboolean('prefs', "centerSnap['Z']")
                # get remaining mirroring options
                self.mirrorT = {}
                self.mirrorT['X'] = prefsConfig.getboolean('prefs', "mirrorT['X']")
                self.mirrorT['Y'] = prefsConfig.getboolean('prefs', "mirrorT['Y']")
                self.mirrorT['Z'] = prefsConfig.getboolean('prefs', "mirrorT['Z']")
                self.centerFalloff = prefsConfig.getfloat('prefs', 'centerFalloff')
                
                # get mirror offset values
                self.mirrorZero = {'X':0, 'Y':0, 'Z':0}
                axis = {'X':0, 'Y':1, 'Z':2}
                for ax in axis:
                    if mc.objExists('faceCtrl_MirrorHelper_{0}0'.format(ax)):
                        self.mirrorZero[ax] = mc.xform('faceCtrl_MirrorHelper_{0}0'.format(ax), t=1, ws=1, q=1)[axis[ax]]
                    else:
                        self.mirrorZero[ax] = 0.0

                # get ctrl options
                self.ctrlShape = prefsConfig.get('prefs', 'ctrlShape') 
                self.ctrlSize = prefsConfig.getfloat('prefs', 'ctrlSize')
                self.ctrlColor = prefsConfig.getint('prefs', 'ctrlColor') - 1
                
                # get hierarchy options
                self.makeOffset = prefsConfig.getboolean('prefs', 'makeOffset')
                self.sdkNulls = prefsConfig.getint('prefs', 'sdkNulls')
                self.makeJnt = prefsConfig.getboolean('prefs', 'makeJnt')
                self.parentSpace = prefsConfig.get('prefs', 'parentSpace') #'world', 'existing', 'new'
                
                # get hierarchy naming options
                self.offsetPrefix = prefsConfig.get('prefs', 'offsetPrefix').strip()
                self.offsetSuffix = prefsConfig.get('prefs', 'offsetSuffix').strip()
                self.sdkName = prefsConfig.get('prefs', 'sdkName').strip()
                self.sdkSuffix = prefsConfig.get('prefs', 'sdkSuffix').strip()
                self.ctrlName = prefsConfig.get('prefs', 'ctrlName').strip()
                self.jntName = prefsConfig.get('prefs', 'jntName').strip()
                self.parentName = prefsConfig.get('prefs', 'parentName').strip()
                
                self.prefix = {}
                # get mirror X naming options
                self.prefix['X'] = prefsConfig.getboolean('prefs', "prefix['X']")
                self.prefix['XPos'] = prefsConfig.get('prefs', "prefix['XPos']").strip()
                self.prefix['XNeg'] = prefsConfig.get('prefs', "prefix['XNeg']").strip()
                
                # get mirror Y naming options
                self.prefix['Y'] = prefsConfig.getboolean('prefs', "prefix['Y']")
                self.prefix['YPos'] = prefsConfig.get('prefs', "prefix['YPos']").strip()
                self.prefix['YNeg'] = prefsConfig.get('prefs', "prefix['YNeg']").strip()
                
                # get mirror Z naming options
                self.prefix['Z'] = prefsConfig.getboolean('prefs', "prefix['Z']")
                self.prefix['ZPos'] = prefsConfig.get('prefs', "prefix['ZPos']").strip()
                self.prefix['ZNeg'] = prefsConfig.get('prefs', "prefix['ZNeg']").strip()
                
                # get misc options
                self.saveAutomatically = prefsConfig.getboolean('prefs', 'saveAutomatically')
        
        
        elif mode == 'save':
            # get settings from UI
            self.settings('get', fromUI=True)
            
            # save settings according to UI settings (with two exceptions)
            for option in prefsConfig.options('prefs'):
                if option == 'ctrlColor':
                    prefsConfig.set('prefs', option, self.ctrlColor+1)
                elif option == 'parentSpace' and self.parentSpace == 'existing':
                    continue
                else:
                    prefsConfig.set('prefs', option, eval("self.{0}".format(option)))
            with open(prefsFile, 'w') as configfile:
                prefsConfig.write(configfile)
            
            # print message to output field
            mel.eval('print "// Tool Settings Saved\\n"')
        
        
        elif mode == 'restore':
            # restore settings from defaults
            for option, default in zip(prefsConfig.options('prefs'), prefsConfig.items('defaults')):
                defaultSetting = default[1]
                prefsConfig.set('prefs', option, defaultSetting)
            with open(prefsFile, 'w') as configfile:
                prefsConfig.write(configfile)
            
            # reload UI
            self.UI()
            
            # print message to output field
            mel.eval('print "// Tool Settings Restored to Default\\n"')
    
    
    def closeWin(self):
        if mc.menuItem(self.widgets['saveAutomatically'], checkBox=True, q=1):
            self.settings('save')
    
    
    
    def initTool(self, closeWindow=False, fromUI=False, *args):
        
        # get options from UI or INI
        if fromUI:
            self.settings('get', fromUI=True)
        else:
            self.settings('get')
            self.shapesIni()
        
        # close UI window
        if closeWindow:
            self.closeWindow()
            
        # define intersectable objects as all meshes
        self.meshSelection = mc.ls(type='mesh', v=1)
        for axis in ['X', 'Y', 'Z']:
            if mc.objExists('faceCtrl_MirrorHelper_{0}0'.format(axis)):
                self.meshSelection.remove('faceCtrl_MirrorHelper_{0}0Shape'.format(axis))
        
        # on tool activation, restart the tool
        self.context='faceControlTool'
        if mc.draggerContext(self.context, exists=True):
            mc.deleteUI(self.context)
        
        # setup tool
        icon = os.path.dirname(__file__) + '/icons/' + 'toolIcon.png'
        mc.draggerContext(self.context, pc=self.onPress, dc=self.onDrag, rc=self.onRelease, n=self.context, cur='crossHair', ch=0, undoMode='step', i1=icon)
        mc.setToolTo(self.context)
    
    
    
    def pressActions(self, matrix, mirror='orig'):
        # make ctrl hierarchy
        offset = self.makeCtrls()
        
        # get offset dag path and pass to self.offsets{}
        sel = om.MSelectionList()
        sel.add(offset)
        mdag = sel.getDagPath(0)
        self.offsets[mirror] = mdag.fullPathName
        
        # move ctrl offset to surface of target object
        mc.xform(self.offsets[mirror](), m=matrix)
        
        # parent the ctrl in the correct parentSpace
        self.parentCtrl(self.offsets[mirror]())
    
    
    
    #onPress is called when the user clicks on the surface of the mesh      
    def onPress(self, *args):
        # clear out offsets
        self.offsets = {'orig':str, 'X':str, 'XY':str, 'XYZ':str, 'XZ':str, 'Y':str, 'YZ':str, 'Z':str}
        
        # fire the ray and pass results through to pressActions
        hit, matrix, pos, dir, isCenter = self.fireRay()
        if hit:
            self.pressActions(matrix)
        
        if not isCenter['X']:
            # X mirror actions
            if self.mirror['X']:
                hit, matrixX, posX, dirX, extraArg = self.fireRay(mirror='X')
                if hit:
                    self.pressActions(matrixX, mirror='X')
                
                if not isCenter['Y']:
                    # XY mirror actions
                    if self.mirror['Y']:
                        hit, matrixXY, posXY, dirXY, extraArg = self.fireRay(mirror='XY', mPos=posX, mDir=dirX)
                        if hit:
                            self.pressActions(matrixXY, mirror='XY')
                        
                        if not isCenter['Z']:
                            # XYZ mirror actions
                            if self.mirror['Z']:
                                hit, matrixXYZ, posXYZ, dirXYZ, extraArg = self.fireRay(mirror='XYZ', mPos=posXY, mDir=dirXY)
                                if hit:
                                    self.pressActions(matrixXYZ, mirror='XYZ')
                
                if not isCenter['Z']:
                    # XZ mirror actions
                    if self.mirror['Z']:
                        hit, matrixXZ, posXZ, dirXZ, extraArg = self.fireRay(mirror='XZ', mPos=posX, mDir=dirX)
                        if hit:
                            self.pressActions(matrixXZ, mirror='XZ')
            
            if not isCenter['Y']:
                # Y mirror actions
                if self.mirror['Y']:
                    hit, matrixY, posY, dirY, extraArg = self.fireRay(mirror='Y')
                    if hit:
                        self.pressActions(matrixY, mirror='Y')
                
                    if not isCenter['Z']:
                        # YZ mirror actions
                        if self.mirror['Z']:
                            hit, matrixYZ, posYZ, dirYZ, extraArg = self.fireRay(mirror='YZ', mPos=posY, mDir=dirY)
                            if hit:
                                self.pressActions(matrixYZ, mirror='YZ')
            
            if not isCenter['Z']:
                # Z mirror actions
                if self.mirror['Z']:
                    hit, matrixZ, posZ, dirZ, extraArg = self.fireRay(mirror='Z')
                    if hit:
                        self.pressActions(matrixZ, mirror='Z')
        
        
        # refresh the viewport
        mc.refresh()
    
    
    
    def parentCtrl(self, ctrl):
        # ctrl already in world space
        if self.parentSpace == 'world':
            return
        
        # parent ctrl under new group
        elif self.parentSpace == 'new':
            if mc.objExists(self.parentName):
                mc.parent(ctrl, self.parentName)
            else:
                mc.group(ctrl, n=self.parentName)
        
        # parent ctrl under existing transform
        elif self.parentSpace == 'existing':
            parented = False
            if mc.objExists(self.parentObj):
                if mc.nodeType(self.parentObj) == 'transform':
                    mc.parent(ctrl, self.parentObj)
                    parented = True
            
            if not parented:
                self.parentSpace = 'new'
                mc.warning("Parent transform '{0}' does not exist or is not a valid transform. Using new parent group.".format(self.parentObj))
                self.parentCtrl(ctrl)
    
    
    
    def dragActions(self, mirrorAxis, prevPos=False, prevDir=False):
        if mirrorAxis == 'orig':
            rayMirror = False
        else:
            rayMirror = mirrorAxis
        
        # fire the ray and get the location and transform matrix for hit point.
        hit, matrix, pos, dir, isCenter = self.fireRay(drag=True, mirror=rayMirror, mPos=prevPos, mDir=prevDir)
        if hit:
            if mc.objExists(self.offsets[mirrorAxis]()):
                # move ctrl offset to surface of target object
                mc.xform(self.offsets[mirrorAxis](), m=matrix)
            else:
                # create new ctrl hierarchy
                self.pressActions(matrix, mirror=mirrorAxis)
        # delete ctrl if dragging off meshes
        elif mc.objExists(self.offsets[mirrorAxis]()):
            mc.delete(self.offsets[mirrorAxis]())
        return pos, dir, isCenter
    
    
    
    # onDrag is called when the user drags on the selected area
    def onDrag(self, *args):
        # initial hierarchy actions
        pos, dir, isCenter = self.dragActions('orig', False, False)
        
        # if snapping to the center, and an X mirrored hierarchy object exists, delete it.
        if isCenter['X']:
            for obj in self.offsets:
                if 'X' in obj and mc.objExists(self.offsets[obj]()):
                    mc.delete(self.offsets[obj]())
        else:
            # X mirror actions
            if self.mirror['X']:
                posX, dirX, extraArg = self.dragActions('X')
                
                # XY mirror actions
                if self.mirror['Y']:
                    posXY, dirXY, extraArg = self.dragActions('XY', posX, dirX)
                    
                    # XYZ mirror actions
                    if self.mirror['Z']:
                        self.dragActions('XYZ', posXY, dirXY)
                
                # XZ mirror actions
                if self.mirror['Z']:
                    self.dragActions('XZ', posX, dirX)
        
        # if snapping to the center, and a Y mirrored hierarchy object exists, delete it.
        if isCenter['Y']:
            for obj in self.offsets:
                if 'Y' in obj and mc.objExists(self.offsets[obj]()):
                    mc.delete(self.offsets[obj]())
        else:
            # Y mirror actions
            if self.mirror['Y']:
                posY, dirY, extraArg = self.dragActions('Y')
                
                # YZ mirror actions
                if self.mirror['Z']:
                    self.dragActions('YZ', posY, dirY)
        
        # if snapping to the center, and a Z mirrored hierarchy object exists, delete it.
        if isCenter['Z']:
            for obj in self.offsets:
                if 'Z' in obj and mc.objExists(self.offsets[obj]()):
                    mc.delete(self.offsets[obj]())
        else:
            # Z mirror actions
            if self.mirror['Z']:
                self.dragActions('Z')
        
        
        # refresh the viewport
        mc.refresh()
    
    
    
    def fireRay(self, drag=False, mirror=False, mPos=False, mDir=False):
        
        if mc.window(self.windowName, exists=True):
            self.settings('get', fromUI=True)
        
        # get 2D mouse coords
        if drag:
            vpX, vpY, _ = mc.draggerContext(self.context, query=True, dragPoint=True)
        else:
            vpX, vpY, _ = mc.draggerContext(self.context, query=True, anchorPoint=True)
        
        # get 3D mouse coords (reassigning because when I didn't, it inexplicably altered the sources of mDir and mPos)
        if mirror and mPos:
            pos = om.MPoint(mPos[0], mPos[1], mPos[2])
            dir = om.MVector(mDir.x, mDir.y, mDir.z)
        else:
            pos = om.MPoint()
            dir = om.MVector()
            omui.M3dView().active3dView().viewToWorld(int(vpX), int(vpY), pos, dir) #Changes pos and dir
        
        # prepare axis and centering dicts
        axis = {'X':0, 'Y':1, 'Z':2}
        isCenter = {'X':False, 'Y':False, 'Z':False}
        
        # set mirror pos and dir
        if mirror:
            # set ray origin/direction at mirror of original ray
            pos[axis[mirror[-1]]] = pos[axis[mirror[-1]]] * -1 + self.mirrorZero[mirror[-1]]*2
            dir[axis[mirror[-1]]] = dir[axis[mirror[-1]]] * -1
        
        
        mouseVec = om.MVector(pos)
        dragIntersection = {}
        hitDist = {}
        fnMesh = {}
        
        for mesh in self.meshSelection:
            # get the dag path of mesh
            selectionList = om.MSelectionList()
            selectionList.add(mesh)
            dagPath = selectionList.getDagPath(0)
            fnMesh[mesh] = om.MFnMesh(dagPath)
            
            # fire ray and get ray/mesh intersect data
            dragIntersection[mesh] = fnMesh[mesh].closestIntersection(om.MFloatPoint(pos), om.MFloatVector(dir), om.MSpace.kWorld, 99999, False)
            if dragIntersection[mesh] and dragIntersection[mesh][3] != -1:
                
                # get the distance from ray origin to hitPoint
                hitPoint = dragIntersection[mesh][0]
                hitVec = om.MVector(hitPoint)
                hitDist[mesh] = (mouseVec - hitVec).length()
        
        # if there has been at least one valid hit
        if hitDist.values():
            
            # get closest mesh based on distance
            shortest = min(hitDist.values())
            mesh = hitDist.keys()[hitDist.values().index(shortest)]
            
            # unpack intersection data
            hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = dragIntersection[mesh]
            
            # get normal at hit point
            normal = fnMesh[mesh].getPolygonNormal(hitFace, om.MSpace.kWorld)
            
            # check if the ctrl is within center falloff
            for ax in axis:
                if self.centerSnap[ax]:
                    if hitPoint[axis[ax]] < (self.mirrorZero[ax] + self.centerFalloff) and hitPoint[axis[ax]] > (self.mirrorZero[ax] - self.centerFalloff):
                        hitPoint[axis[ax]] = 0.0 + self.mirrorZero[ax]
                        normalPoint = om.MPoint(hitPoint[0], hitPoint[1], hitPoint[2])
                        normal = fnMesh[mesh].getClosestNormal(normalPoint, om.MSpace.kWorld)[0]
                        isCenter[ax] = True
            
            # create new ctrl offset matrix based on surface normal and ray intersection point
            # (see https://www.youtube.com/watch?v=SKomaUCHAko at 55:30ish)
            Zv = normal
            # if normal isn't facing Y, use that to build rotation of matrix
            Yv = om.MVector([0, 1, 0])
            if abs(Zv * Yv) < 0.8:
                Xcross = Yv ^ Zv
                Xv = Xcross.normal()
                Ycross = Zv ^ Xv
                Yv = Ycross.normal()
            else:
                Xv = om.MVector([1, 0, 0])
                Ycross = Xv ^ Zv
                Yv = Ycross.normal()
                Xcross = Zv ^ Yv
                Xv = Xcross.normal()
            
            # reverse mirror transforms
            if self.mirrorT['X'] and hitPoint[0] < self.mirrorZero['X']:
                Xv = om.MVector([Xv.x * -1, Xv.y * -1, Xv.z * -1])
            if self.mirrorT['Y'] and hitPoint[1] < self.mirrorZero['Y']:
                Yv = om.MVector([Yv.x * -1, Yv.y * -1, Yv.z * -1])
            if self.mirrorT['Z'] and hitPoint[2] < self.mirrorZero['Z']:
                # Because the Z axis is facing out of the target mesh, mirrors in Z require a transformX flip
                Xv = om.MVector([Xv.x * -1, Xv.y * -1, Xv.z * -1])
                            
            
            # construct transform matrix
            matrix = [Xv.x, Xv.y, Xv.z, 0.0,
                      Yv.x, Yv.y, Yv.z, 0.0,
                      Zv.x, Zv.y, Zv.z, 0.0,
                      hitPoint[0], hitPoint[1], hitPoint[2], 1.0]
            
            return True, matrix, pos, dir, isCenter
        return False, False, pos, dir, isCenter
    
    
    
    def makeCtrls(self):
        # create control (eval value for 'ctrl' in ctrlShape dict nested in shapes dict)
        ctrl = eval(self.shapes[self.ctrlShape])['ctrl']
        
        ctrlShapes = mc.listRelatives(ctrl, s=1, f=1)
        for shape in ctrlShapes:
            # color curve-based ctrl
            if mc.nodeType(shape) == 'nurbsCurve':
                mc.setAttr(shape+'.overrideEnabled', 1)
                mc.setAttr(shape+'.overrideColor', self.ctrlColor)
            # make surface-based ctrl non-renderable and color it (leave lambert1 if color 0)
            else:
                mc.setAttr(shape+'.primaryVisibility', 0)
                mc.setAttr(shape+'.castsShadows', 0)
                mc.setAttr(shape+'.receiveShadows', 0)
                mc.setAttr(shape+'.visibleInReflections', 0)
                mc.setAttr(shape+'.visibleInRefractions', 0)
                ctrlMat = self.makeCtrlMat()
                if ctrlMat:
                    mc.sets(ctrl, edit=1, forceElement=ctrlMat)
        
        
        # create joint
        if self.makeJnt:
            mc.select(d=1)
            jnt = mc.joint(n=self.jntName)
            mc.setAttr(jnt+'.radius', self.ctrlSize)
            mc.parent(jnt, ctrl)
        
        # move control off surface
        cluster = mc.cluster(ctrl)
        mc.xform(cluster, ro=[90,0,0])
        mc.xform(cluster, t=[0, 0, self.ctrlSize * 2])
        mc.delete(ctrl, ch=1)
        
        
        # create sdk nulls
        if self.sdkNulls:
            chars = []
            # check if suffix is str
            if self.sdkSuffix:
                try:
                    self.sdkSuffix = int(self.sdkSuffix)
                    suffType = 'int'
                except ValueError:
                    suffType = 'str'
                # use suffix directly if int
                if self.sdkNulls > 1 and suffType == 'int':
                    chars = [str(n) for n in range(self.sdkSuffix, self.sdkNulls+self.sdkSuffix)]
                # count up from letters if str. Account for potential end of alphabet.
                elif self.sdkNulls > 1 and suffType == 'str':
                    nn = 0
                    num = 0
                    char1 = ''
                    ordValue = ord(self.sdkSuffix)
                    if 64 < ordValue < 91:
                        alphabetNum = 26 - ordValue + 65
                        ordStarter = 65
                    elif 96 < ordValue < 123:
                        alphabetNum = 26 - ordValue + 97
                        ordStarter = 97
                    else:
                        mc.warning("Unexpectedly large number of SDK nulls created. Resulting hierarchy may not be created as expected.")
                    
                    while num < self.sdkNulls:
                        if self.sdkNulls > alphabetNum:
                            char1 = chr(nn + ordStarter)
                            nn += 1
                        n=0
                        if nn == 1:
                            while n < alphabetNum:
                                char2 = chr(n + ordValue)
                                n += 1
                                num += 1
                                chars.append(char1+char2)
                        else:
                            while n < 26 and num < self.sdkNulls:
                                char2 = chr(n + ordStarter)
                                n += 1
                                num += 1
                                chars.append(char1+char2)
                elif self.sdkNulls <= 1:
                    chars.append('')
                else:
                    chars.append(str(self.sdkSuffix))
            else:
                chars = [str(n) for n in range(self.sdkNulls)]
            
            # build name from above and create group
            if chars:
                for char in chars:
                    if len(chars) > 1:
                        sdkName = self.ctrlName + self.sdkName + '_' + char
                    else:
                        sdkName = self.ctrlName + self.sdkName
                    ctrl = mc.group(ctrl, n=sdkName)
        
        
        # create offset group
        if self.makeOffset:
            #set offset name
            offsetName = self.offsetPrefix + self.ctrlName + self.offsetSuffix
            offset = mc.group(ctrl, n=offsetName)
            return offset
        else:
            return ctrl
    
    
    
    def makeCtrlMat(self):
        if self.ctrlColor:
            # define color names from color index
            colors = {1 : 'black',
                      2 : 'darkGrey',
                      3 : 'lightGrey',
                      4 : 'magenta',
                      5 : 'darkBlue',
                      6 : 'blue',
                      7 : 'darkGreen',
                      8 : 'purple',
                      9 : 'darkPink',
                      10 : 'brown',
                      11 : 'darkBrown',
                      12 : 'orange',
                      13 : 'red',
                      14 : 'green',
                      15 : 'blue2',
                      16 : 'white',
                      17 : 'yellow',
                      18 : 'lightBlue',
                      19 : 'lightAqua',
                      20 : 'lightPink',
                      21 : 'beige',
                      22 : 'offYellow',
                      23 : 'darkAqua',
                      24 : 'lightBrown',
                      25 : 'lightYellow',
                      26 : 'offGreen',
                      27 : 'aqua',
                      28 : 'lightBlue2',
                      29 : 'offBlue',
                      30 : 'lightPurple',
                      31 : 'pink'
                      }
            
            # name ctrl material based on color
            ctrlMatColor = mc.colorIndex(self.ctrlColor, q=True)
            ctrlMat = self.ctrlName + colors[self.ctrlColor] + '_M'
            
            # create new lambert if one doesn't exist
            if not mc.objExists(ctrlMat):
                mc.shadingNode('lambert', asShader=1, n=ctrlMat)
                for co, ch in zip(ctrlMatColor, ['R','G','B']):
                    mc.setAttr(ctrlMat+'.color%s'%ch, co)
                mc.sets(renderable=1, noSurfaceShader=1, empty=1, name=ctrlMat+'SG')
                mc.connectAttr(ctrlMat+'.outColor',  ctrlMat+'SG.surfaceShader')
            
            # return the shading group
            return ctrlMat+'SG'
        else:
            return None
    
    
    
    def onRelease(self, *args):
        # check to see which axes were used as mirrors
        mirror = {'X':False, 'Y':False, 'Z':False}
        axis = {'X':0, 'Y':1, 'Z':2}

        for offset in self.offsets:
            if mc.objExists(self.offsets[offset]()):
                for ax in axis:
                    if ax in offset:
                        mirror[ax] = True
                
                # stop loop if all three mirrors discovered
                if mirror['X'] and mirror['Y'] and mirror['Z']:
                    break
        
        
        # rename all offsets made this cycle and their decendents
        for offset in self.offsets:
            
            if mc.objExists(self.offsets[offset]()):
                
                # get offset position
                offsetPos = mc.xform(self.offsets[offset](), t=1, ws=1, q=1)
                # generate prefix based on mirrored objects and naming convention
                prefix = ''
                for ax in axis:
                    if mirror[ax]:
                        if offsetPos[axis[ax]] < self.mirrorZero[ax]:
                            neg = ax+"Neg"
                            prefix += self.prefix[neg]
                        elif offsetPos[axis[ax]] > self.mirrorZero[ax]:
                            pos = ax+"Pos"
                            prefix += self.prefix[pos]
                
                
                # rename the hierarchy (put offset prefix first if applicable)
                for item in mc.listRelatives(self.offsets[offset](), ad=1, f=1)+[self.offsets[offset]()]:
                    itemShort = item.split('|')[-1]
                    if self.offsetPrefix in itemShort and self.offsetPrefix:
                        prefixTrue = self.offsetPrefix + prefix
                        mc.rename(item, itemShort.replace(self.offsetPrefix, prefixTrue))
                    else:
                        mc.rename(item, prefix+itemShort)