#!/bin/env python
'''
2018-12-06
@author: Tyler Lemon

Version successfully converts widgets from opi to edl format.
Currently working on adding ability to convert opi's basic colors to edl.

Supported EDM widgets:
static text
lines
circles
rectangles
arcs
gif images
png images
bar monitor
text monitor
text update
text control*

*denotes widgets that have not been tested yet.
'''

import sys
import os.path
from math import sqrt
import argparse

wedmPath = '/cs/opshome/edm/hlc/spectrometers/'

#Base properties for EDM screen.
edlScreenProps = ['4 0 1','beginScreenProperties','major 4','minor 0',\
    'release 1','x 0','y 0','w WIDTH','h HEIGHT',\
    'font "helvetica-medium-r-18.0"','ctlFont "helvetica-medium-r-8.0"',\
    'btnFont "helvetica-medium-r-18.0"','fgColor index 14','bgColor index 4',\
    'textColor index 14','ctlFgColor1 index 30','ctlFgColor2 index 32',\
    'ctlBgColor1 index 34','ctlBgColor2 index 35','topShadowColor index 37',\
    'botShadowColor index 44','snapToGrid','gridSize 5','endScreenProperties\n']

#Properties for EDM Graphics
#Static text (aka labels)
edlStaticTextFmt = ['# (Static Text)','object activeXTextClass',\
    'beginObjectProperties','major 4','minor 1','release 1','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','font "helvetica-bold-r-14.0"',\
    'fontAlign "center"','fgColor index 14','bgColor index 0','useDisplayBg',\
    'value {','  "LABEL_TEXT"','}','autoSize','endObjectProperties\n']

#lines
edlLineFmt = ['# (Lines)','object activeLineClass','beginObjectProperties',\
    'major 4','minor 0','release 1','x X_POS','y Y_POS','w WIDTH','h HEIGHT',\
    'lineColor index COLOR','fillColor index 51','lineWidth LINE_WEIGHT',\
    'numPoints NUM_PTS','xPoints {','X_POINTS','}','yPoints {',\
    'Y_POINTS','}','endObjectProperties\n']

#circles (or ellipses)
edlCircleFmt = ['# (Circle)','object activeCircleClass',\
    'beginObjectProperties','major 4','minor 0','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','lineColor index 14','fillColor index COLOR',\
    'endObjectProperties\n']

#Rectangles
edlRectangleFmt = ['# (Rectangle)','object activeRectangleClass',\
    'beginObjectProperties','major 4','minor 0','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','lineColor index 14','fillColor index COLOR',\
    'endObjectProperties\n']

#Arcs - NOTE: this widget conversion seem to be a little buggy.
edlArcFmt = ['# (Arc)','object activeArcClass','beginObjectProperties',\
    'major 4','minor 0','release 0','x X_POS','y Y_POS','w WIDTH','h HEIGHT',\
    'lineColor index 14','fillColor index 51','endObjectProperties\n']

#Gif Images
edlGifFmt = ['# (GIF Image)','object cfcf6c8a_dbeb_11d2_8a97_00104b8742df',\
    'beginObjectProperties','major 4','minor 0','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','file "PATH_TO_PIC"','endObjectProperties\n']

#PNG images
edlPngFmt = ['# (PNG Image)','object activePngClass','beginObjectProperties',\
    'major 4','minor 0','release 0','x X_POS','y Y_POS','w WIDTH','h HEIGHT',\
    'file "PATH_TO_PIC"','endObjectProperties\n']

#Bar monitors - if rotated 90 deg, can act as liquid level indicators
edlBarMonFmt = ['# (Bar)','object activeBarClass','beginObjectProperties',\
    'major 4','minor 1','release 1','x X_POS','y Y_POS','w WIDTH','h HEIGHT',\
    'indicatorColor indexCOLOR','fgColor index 14','bgColor index 9',\
    'indicatorPv "PV_NAME"','showScale','origin "0"',\
    'font "helvetica-medium-r-8.0"','border','precision "10"','min "MIN"',\
    'max "MAX"','scaleFormat "FFloat"','endObjectProperties\n']

#Text monitor
edlTextMonFmt = ['# (Text Monitor)','object activeXTextDspClass:noedit',\
    'beginObjectProperties','major 4','minor 7','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','controlPv "PV_NAME"',\
    'font "helvetica-medium-r-18.0"','fgColor index 14',\
    'bgColor index 51','topShadowColor index 50',\
    'botShadowColor index 10','useDisplayBg','autoHeight',\
    'limitsFromDb','nullColor index 14','useHexPrefix',\
    'newPos','objType "monitors"','endObjectProperties\n']

#Text update - the standard text indicator
edlTextUpdateFmt = ['# (Textupdate)','object TextupdateClass',\
    'beginObjectProperties','major 10','minor 0','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','controlPv "PV_NAME"',\
    'fgColor index 14','fgAlarm','bgColor index 51','fill',\
    'font "helvetica-medium-r-14.0"','endObjectProperties\n']

#Text controls - NOTE: this is the one widget that has yet to be tested.
edlTextCtrlFmt = ['# (Text Control)','object activeXTextDspClass',\
    'beginObjectProperties','major 4','minor 7','release 0','x X_POS',\
    'y Y_POS','w WIDTH','h HEIGHT','controlPv "PV_NAME"',\
    'font "helvetica-medium-r-18.0"','fgColor index 14',\
    'bgColor index 51','topShadowColor index 50',\
    'botShadowColor index 10','useDisplayBg','autoHeight','limitsFromDb',\
    'nullColor index 14','useHexPrefix','newPos',\
    'objType "controls"','endObjectProperties\n']


#colorList are acceptable colors for WEDM. Index of list element corresponds
#to EDM color pallet index for WEDM.
colorsList = [['255','255','255'],['235','235','235'],['218','218','218'],\
    ['200','200','200'],['187','187','187'],['174','174','174'],\
    ['158','158','158'],['145','145','145'],['133','133','133'],\
    ['120','120','120'],['105','105','105'],['90','90','90'],\
    ['70','70','70'],['45','45','45'],['0','0','0'],['0','216','0'],\
    ['30','187','0'],['51','153','0'],['45','142','0'],['33','108','0'],\
    ['253','0','0'],['222','19','9'],['190','25','11'],['160','18','7'],\
    ['130','4','0'],['88','147','255'],['89','126','225'],['75','110','199'],\
    ['58','94','171'],['39','84','141'],['251','243','74'],['249','200','60'],\
    ['238','182','43'],['225','144','21'],['205','97','0'],['255','176','255'],\
    ['214','127','226'],['174','78','188'],['139','26','150'],\
    ['97','10','117'],['164','170','255'],['135','147','226'],\
    ['106','115','193'],['77','82','164'],['52','51','134'],\
    ['199','187','109'],['183','157','92'],['164','126','60'],\
    ['125','86','39'],['88','52','15'],['153','255','255'],\
    ['115','223','255'],['78','165','249'],['42','99','228'],\
    ['10','0','184'],['235','241','181'],['212','219','157'],\
    ['187','193','135'],['166','164','98'],['139','130','57'],\
    ['115','255','107'],['82','218','59'],['60','180','32'],\
    ['40','147','21'],['26','115','9'],['0','255','255'],\
    ['0','224','224'],['0','192','192'],['0','160','160'],\
    ['0','128','128'],['255','0','255'],['192','0','192'],\
    ['206','220','205'],['185','198','184'],['166','178','165'],\
    ['225','248','177'],['202','223','159'],['244','218','168'],\
    ['183','164','126'],['122','109','84'],['181','249','215'],\
    ['162','224','193'],['194','218','217'],['174','196','195'],\
    ['156','176','175'],['176','218','249'],['158','196','224'],\
    ['205','202','221'],['184','181','198'],['165','162','178'],\
    ['222','196','251'],['199','175','225'],['198','181','198'],\
    ['178','162','178'],['251','235','236'],['225','176','212'],\
    ['255','150','168'],['192','113','126'],['184','46','0']]


# Function parses line form OPI file for parameter set by "prop".
# "prop" must be a string.
def returnProp(item,prop):
    startText = '<'+prop+'>'
    endText = '</'+prop+'>'
    val = [s for s in item if startText in s][0][[s for s in item if \
        startText in s][0].find(startText)+len(startText):][:[s for s in \
        item if startText in s][0][[s for s in item if startText in \
        s][0].find(startText)+len(startText):].find(endText)]
    return val

#All widgets have x,y-position and width and height properties.
#This function just simplifies later code by consolidating common properties
#into one command.
def edlPlaceWidget(props,template):
    edlFmt = []
    xPos,yPos,width,height = props[1:]
    for line in template:
        line = line.replace('X_POS',str(xPos))
        line = line.replace('Y_POS',str(yPos))
        line = line.replace('WIDTH',str(width))
        line = line.replace('HEIGHT',str(height))
        edlFmt.append(line)
    return edlFmt

#Checks working directory for image. This command isn't really necessary, but
#during intial development, I thought it seemed necessary.
def lookForImage(image):
    if os.path.isfile(image):
        imageFile = image
    else:
        print('"'+image+'" not found.')
        print('Put "'+image+'" in directory with OPI file and re-run \
conversion.')
        imageFile = 'NOT_FOUND'
    return imageFile

#Function parses OPI line widget to pull coordinates of line segments and then
#formats them into the EDL format.
def ptsGet(widget,lineFmt):
    pts = [[],[]]
    opiPts = [line for line in widget if '<point x="' in line]
    ptFmt = '  N PT'
    count = 0
    for p,pt in enumerate(opiPts):
        x = ptFmt.replace('N',str(p))
        x = x.replace('PT',str(pt.split('"')[1]))
        y = ptFmt.replace('N',str(p))
        y = y.replace('PT',str(pt.split('"')[3]))
        pts[0].append(x)
        pts[1].append(y)
        count += 1
    ptFmt = lineFmt[: -6]
    midPtFmt = lineFmt[-5: -3]
    postPtFmt = lineFmt[-2:]
    for pt in pts[0]:
        ptFmt.append(pt)
    for item in midPtFmt:
        ptFmt.append(item)
    for pt in pts[1]:
        ptFmt.append(pt)
    for item in postPtFmt:
        ptFmt.append(item)
    return ptFmt,str(count)

#Looks to see whether widget has transparent components and then looks at
#RGB color of widget and finds which EDM color is closest.
def convertColor(colorConst,widget):
    #try-except for widgets that do not have transparent property.
    try:
        transparent = returnProp(widget,'transparent')
    except:
        transparent = 'false'
    for e,line in enumerate(widget):
        if '<background_color>' in line and '</background_color>' \
        in widget[e+2]:
            origColor = widget[e+1].split('"')[1::2]
            dMatch = 99999
            match = 9999
            for index,color in enumerate(colorsList):
                r1,g1,b1 = color
                r2,g2,b2 = origColor
                d = sqrt((int(r2)-int(r1))**2 + (int(g2)-int(g1))**2 + \
                    (int(b2)-int(b1))**2)
                if d < dMatch:
                    dMatch = d
                    match = index
    outColor = str(match)
    return outColor,transparent



parser = argparse.ArgumentParser()
parser.add_argument('opi',help='CSS .OPI file to convert to WEDM.')
parser.add_argument('-o','--output',help='Path of where to write resulting \
WEDM file to.')
args = parser.parse_args()

inputArg = args.opi

if args.output != None:
    outputPath = args.output
    if outputPath == '.':  outputPath = os.getcwd()
    if outputPath.strip()[-1] != '/':  outputPath += '/'
    print('WEDM files will be written to "'+outputPath+'".')
else:
    outputPath = ''


#Allows user to input a directory instead of a file to convert the directory
#all at once instead of having to run command for every file in path.
files,skipped = [],[]
if os.path.isdir(inputArg):
    if inputArg[-1] != '/':  inputArg += '/'
    for f in os.listdir(inputArg):
        if f[-4:].lower() != '.opi':
            skipped.append(inputArg+f)
        elif f[-4:].lower() == '.opi':
                files.append(inputArg+f)
        else:
            print('Error in reading in files. Check files and re-run script.')
else:
    if inputArg[-4:].lower() != '.opi':
        skipped.append(inputArg)
    if inputArg[-4:].lower() == '.opi':
        files.append(inputArg)
    else:
        print('Error in reading in files. Check files and re-run script.')

print('\nOPI files entered into script:')

for opi in files:
    unable = []
    print('\n'+opi)
    edl = opi[opi.rfind('/')+1:][:opi[opi.rfind('/')+1:].find('.opi')]+'.edl'

    # Reads in file names for .opi file from arguement.
    # Creates .edl file name by removing opi file extension and appending .edl.


    # Opens .opi file as text and stores all lines as list elements.
    with open(opi,'r') as f:
        opiLines = f.readlines()

    # Processes OPI file lines to determine widget type and other properties.
    hold = 0
    # Separates OPI file lines into different widgets and pulls out relevant
    # properties.
    final = []
    # dimensions of screen.
    width = returnProp(opiLines,'width')
    height = returnProp(opiLines,'height')
    for line in edlScreenProps:
        line = line.replace('WIDTH',width)
        line = line.replace('HEIGHT',height)
        final.append(line)

    #widget properties
    for i,line in enumerate(opiLines):
        #separates opi file into widgets.
        if '<widget typeId=' in line and hold == 0:
            hold = i
        elif '</widget>' in line and hold != 0:
            widget = opiLines[hold:i+1]
            hold = 0
            wType = returnProp(widget,'widget_type')
            xPos = returnProp(widget,'x')
            yPos = returnProp(widget,'y')
            width = returnProp(widget,'width')
            height = returnProp(widget,'height')
            props = [wType,xPos,yPos,width,height]
            #Text update
            if wType == 'Text Update':
                fmt = edlPlaceWidget(props,edlTextUpdateFmt)
                for row in fmt:
                    row = row.replace('PV_NAME',returnProp(widget,'pv_name'))
                    final.append(row)
            #Static Text / Label
            elif wType == 'Label':
                fmt = edlPlaceWidget(props,edlStaticTextFmt)
                for row in fmt:
                    row = row.replace('LABEL_TEXT',returnProp(widget,'text'))
                    final.append(row)
            #Images - checks whether image is PNG or GIF.
            elif wType == 'Image':
                imageFile = returnProp(widget,'image_file')
                if imageFile[-4:].lower() == '.png':
                    fmt = edlPlaceWidget(props,edlPngFmt)
                    conv = True
                elif imageFile[-4:].lower() == '.gif':
                    fmt = edlPlaceWidget(props,edlGifFmt)
                    conv = True
                else:
                    print('NOTICE: File type of image in OPI not supported \
in EDM.')
                    print('Image will not be converted to EDL.')
                    conv = False
                if conv == True:
                    for row in fmt:
                        row = row.replace('PATH_TO_PIC',wedmPath+imageFile)
                        final.append(row)
                    #print('Be sure to copy "'+imageFile+'" to WEDM.')
            #Line
            elif wType == 'Polyline':
                pts,nPts = ptsGet(widget,edlLineFmt)
                fmt = edlPlaceWidget(props,pts)
                outColor,transparent = convertColor(colorsList,widget)
                for row in fmt:
                    row = row.replace('COLOR',outColor)
                    row = row.replace('NUM_PTS',nPts)
                    row = row.replace('LINE_WEIGHT',returnProp(widget,\
                        'line_width'))
                    final.append(row)
            #Rectangle
            elif wType == 'Rectangle' or wType == 'Rounded Rectangle':
                fmt = edlPlaceWidget(props,edlRectangleFmt)
                outColor,transparent = convertColor(colorsList,widget)
                for r,row in enumerate(fmt):
                    if 'fillColor' in row and transparent == 'false':
                        final.append('fill')
                    row = row.replace('COLOR',outColor)
                    final.append(row)
            #Circle / Ellipse
            elif wType == 'Ellipse':
                fmt = edlPlaceWidget(props,edlCircleFmt)
                outColor,transparent = convertColor(colorsList,widget)
                for row in fmt:
                    if 'fillColor' in row and transparent == 'false':
                        final.append('fill')
                    row = row.replace('COLOR',outColor)
                    final.append(row)
            #Arc - NOTE: this widget conversion seems to be a little buggy,
            elif wType == 'Arc':
                fmt = edlPlaceWidget(props,edlArcFmt)
                for row in fmt:
                    final.append(row)
            #Bar Monitor
            elif wType == 'Progress Bar' or wType == 'Tank':
                fmt = edlPlaceWidget(props,edlBarMonFmt)
                outColor,transparent = convertColor(colorsList,widget)
                try:
                    orientation = returnProp(widget,'horizontal')
                except:
                    orientation = 'false'
                for row in fmt:
                    row = row.replace('PV_NAME',returnProp(widget,'pv_name'))
                    row = row.replace('MAX',returnProp(widget,'maximum'))
                    row = row.replace('MIN',returnProp(widget,'minimum'))
                    if 'endObjectProperties' in row and orientation == 'false':
                        final.append('orientation "vertical"')
                    final.append(row)
            else:
                unable.append(wType)
    if unable != []:
        unable = set(unable)
        print(', '.join(unable)+' conversion not supported. Widgets skipped.')


    # Writes resulting "final" list to text to .edl file for EDM.
    with open(outputPath+edl,'w') as f:
        for line in final:
            f.write(line)
            f.write('\n')
    print(opi+' converted to '+edl)
