#!/usr/bin/env python
# encoding: utf-8

import time
import signal
import numpy
import collections
import os
import subprocess
from libs.GetDeviceInfo import getDeviceInfo
from subprocess import PIPE, Popen
from threading  import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x


finishFlag = False
deviceName = '5LM7N16224000261' #hw Mate8
#deviceName = 'KWG5T17105003967'  # hw P9
#deviceName = 'FA5B3BJ01146'    #htc
#deviceName = 'R4WG45TCUCUCVGKN'  #oppo
currPath = os.getcwd()
scriptFileRoot = os.path.join(currPath, 'scriptFile', deviceName)

if os.path.isdir(scriptFileRoot) is False:
    os.makedirs(scriptFileRoot)

def signal_handler(signal, frame):
    global finishFlag
    finishFlag = True
    print 'You pressed Ctrl+C!'

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        if 'ABS_MT_POSITION_X' in line or 'ABS_MT_POSITION_Y' in line:
            line = line.replace('\r\n', '')
            queue.put(line)
    out.close()

def check_portrait_landscape():
    checkCmd = "adb -s %s shell dumpsys input | grep 'SurfaceOrientation'  | awk '{ print $2 }' | head -n 1" % deviceName
    result = os.popen(checkCmd , 'r')
    content = result.read()
    result.close()
    screenType = 'portrait'  #默认竖屏
    print 'check portrait result is: %s' % repr(content)
    if len(content) > 0:
        screenTypeValue = int(content.replace('\r\n', ''))
        if screenTypeValue == 0 or screenTypeValue == 2:
            screenType = 'portrait'   #竖屏
        elif screenTypeValue == 1 or screenTypeValue == 3:
            screenType = 'landscape'  #横屏
        else:
            print 'dumpsys input has problem.......'
    return screenType

def get_resolution():
    deviceInfo = getDeviceInfo(deviceName)
    resolutioin = deviceInfo['deviceResolution']
    splitInfo = resolutioin.split('x')
    max_width = int(splitInfo[0].split()[0])
    max_height = int(splitInfo[1].split()[0])
    return (max_width, max_height)


def getevent_position(resolution):
    if cmp(deviceName , '5LM7N16224000261') == 0 or cmp(deviceName, 'R4WG45TCUCUCVGKN') == 0:
        geteventCmd = 'adb -s %s shell getevent -lt /dev/input/event5' % deviceName  #华为Mate8, oppo
    elif cmp(deviceName, '63a9bca7') == 0:
        geteventCmd = 'adb -s %s shell getevent -lt /dev/input/event4' % deviceName   #vivo
    p = Popen(geteventCmd, shell=True, stdout=PIPE)
    print p.pid
    positionRecord = collections.OrderedDict()
    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True # thread dies with the program
    t.start()

    noOutput = False
    hasLine = False
    screenType = check_portrait_landscape()
    max_width = resolution[0]
    while noOutput is False or hasLine is False:
        if finishFlag is True:
            break
        try:
            line = q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            noOutput = True
            if hasLine is False:
                screenType = check_portrait_landscape()
                time.sleep(0.5)
        else:
            hasLine = True
            noOutput = False
            splitLine = line.split()
            timeValue = splitLine[1][0:-1]
            positionValue = int(splitLine[4], 16)
            if positionRecord.has_key(timeValue) is False:
                positionRecord[timeValue] = []
            positionRecord[timeValue].append(positionValue)
    p.kill()
    p.wait()
    #checkGetEventCmd = 'ps aux | grep getevent'
    #os.system(checkGetEventCmd)
    clickOp = collections.OrderedDict()
    if len(positionRecord) == 1:
        startTime = positionRecord.keys()[0]
        positionValue = positionRecord[startTime]
        if cmp(screenType, 'landscape') == 0:
            landscape_x = positionValue[1]
            landscape_y = max_width - positionValue[0]
            positionValue = [landscape_x, landscape_y]
        clickOp['clickType'] = 'tap'
        clickOp['clickStartTime'] = startTime
        clickOp['clickPosition'] = positionValue
        clickOp['screenType'] = screenType
        print clickOp
    elif len(positionRecord) > 1:
        startTime = positionRecord.keys()[0]
        startPosition = positionRecord[startTime]
        if cmp(screenType, 'landscape') == 0:
            landscape_x = startPosition[1]
            landscape_y = max_width - startPosition[0]
            startPosition = [landscape_x, landscape_y]
        endTime = positionRecord.keys()[-1]
        endPosition = positionRecord[endTime]
        if cmp(screenType, 'landscape') == 0:
            landscape_x = endPosition[1]
            landscape_y = max_width - endPosition[0]
            endPosition = [landscape_x, landscape_y]
        startVect = numpy.array(startPosition)
        endVect = numpy.array(endPosition)
        eucDist = round(numpy.linalg.norm(endVect-startVect), 3)
        if eucDist < 20:
            clickOp['clickType'] = 'tap'
            clickOp['clickStartTime'] = startTime
            clickOp['clickPosition'] = startPosition
            clickOp['screenType'] = screenType
        else:
            clickOp['clickType'] = 'swipe'
            clickOp['clickStartTime'] = startTime
            clickOp['clickEndTime'] = endTime
            clickOp['clickStartPosition'] = startPosition
            clickOp['clickEndPosition'] = endPosition
            clickOp['eucDist'] = eucDist
            clickOp['screenType'] = screenType
        print clickOp
    print 'end of getevent position....'
    return clickOp

def write_constant(scriptFile):
    scriptFile.write('#!/usr/bin/env python\r')
    scriptFile.write('# encoding: utf-8\r')
    scriptFile.write('\r')
    scriptFile.write('import os\r')
    scriptFile.write('import time\r')
    scriptFile.write('\r')
    scriptFile.write('if __name__ == "__main__":\r')

def generate_script(pkName, resolution):
    signal.signal(signal.SIGINT, signal_handler)
    clickRecord = []
    clickNum = 0
    #resolution = get_resolution()

    while finishFlag is False:
        clickNum += 1
        #clickRecord[clickNum] = getevent_position()
        recordValue = getevent_position(resolution)
        if len(recordValue) > 0:
            clickRecord.append(recordValue)
            print '*********第%d次点击' % clickNum

    tapNum = 0
    swipeNum = 0
    clickNum = 0
    preClickTime = 0
    scriptFilePath = os.path.join(scriptFileRoot, '%s.py' % pkName)
    positionFilePath = os.path.join(scriptFileRoot, '%s.txt' % pkName)
    scriptFile = open(scriptFilePath, 'w')
    positionFile = open(positionFilePath, 'w')
    positionFile.write('#screenType[portrait/landscap]:: clickType[tap/swipe]:: position[(x,y)/(x1,y1),(x2,y2)]:: sleepTime\r')
    write_constant(scriptFile)

    for record in clickRecord:
        clickNum += 1
        clickType = record['clickType']
        clickTime = record['clickStartTime']
        diffTime = 0
        if clickNum > 1:
            diffTime = round(float(clickTime)-float(preClickTime), 1)

        if clickType == 'tap':
            print '第%d次点击是: %s, 屏幕状态: %s, 坐标是: %s, 与第%d时间间隔是%s' % (clickNum, clickType, record['screenType'], str(record['clickPosition']), clickNum - 1, str(diffTime))
            if diffTime > 0:
                printContent = '    print "sleep %s"\r' % str(diffTime)
                scriptFile.write(printContent)
                content = '    time.sleep(%s)\r' % str(diffTime)
                scriptFile.write(content)
            x_value = record['clickPosition'][0]
            y_value = record['clickPosition'][1]
            printContent = "    print 'adb shell input tap %d %d'\r" % (x_value, y_value)
            scriptFile.write(printContent)
            content = "    os.system('adb shell input tap %d %d')\r"  % (x_value, y_value)
            scriptFile.write(content)
            positionContent = '%s:: %s:: (%d, %d):: %s\r' % (record['screenType'], record['clickType'], x_value, y_value, diffTime)
            positionFile.write(positionContent)
            tapNum += 1
        elif clickType == 'swipe':
            print '第%d次点击是: %s, 屏幕状态: %s, 坐标是: %s%s, 与第%d时间间隔是%s' % (clickNum, clickType, record['screenType'], str(record['clickStartPosition']), str(record['clickEndPosition']), clickNum - 1, str(diffTime))
            x1_value = record['clickStartPosition'][0]
            y1_value = record['clickStartPosition'][1]
            x2_value = record['clickEndPosition'][0]
            y2_value = record['clickEndPosition'][1]
            if diffTime > 0:
                printContent = '    print "sleep %s"\r' % str(diffTime)
                scriptFile.write(printContent)
                content = '    time.sleep(%s)\r' % str(diffTime)
                scriptFile.write(content)
            printContent = "    print 'adb shell input swipe %d %d %d %d'\r" % (x1_value, y1_value, x2_value, y2_value)
            scriptFile.write(printContent)
            content = "    os.system('adb shell input swipe %d %d %d %d')\r" % (x1_value, y1_value, x2_value, y2_value)
            scriptFile.write(content)
            positionContent = '%s:: %s:: (%d, %d), (%d, %d):: %s\r' % (record['screenType'], record['clickType'], x1_value, y1_value, x2_value, y2_value, diffTime)
            positionFile.write(positionContent)
            swipeNum += 1
        preClickTime = clickTime
    printContent = "    print 'sleep 4'\r"
    scriptFile.write(printContent)
    content = "    time.sleep(4)\r"   #模拟点击完成后sleep(4s)
    scriptFile.write(content)
    content = "    os.system('adb shell pm clear com.example.TestPlugin')\r"
    printContent = "    print 'adb shell pm clear com.example.TestPlugin'\r"
    scriptFile.write(printContent)
    scriptFile.write(content)
    scriptFile.write(printContent)
    scriptFile.write(content)
    os.system('adb -s %s shell pm clear com.example.TestPlugin' % deviceName)
    os.system('adb -s %s shell pm clear com.example.TestPlugin' % deviceName)
    scriptFile.write("    print 'end of test script.......'\r")
    scriptFile.close()
    print 'click次数是：%d, 其中tap 次数是: %d, swipe次数是%d' % (clickNum, tapNum, swipeNum)


if __name__ == '__main__':
    clearLogCmd = 'adb shell logcat -c'
    os.system(clearLogCmd)
    readLogcatCmd = 'adb -s %s logcat -v time' % deviceName
    proc = subprocess.Popen(readLogcatCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkName = 'noName'
    resolution = get_resolution()
    for line in proc.stdout:
        if 'PluginAutoTest' in line and 'install success' in line:
            line = line.replace('\r\n', '')
            splitLine = line.split(': ')
            pkItem = splitLine[1]
            pkSplit = pkItem.split()
            pkName = pkSplit[0]
            print pkName
            break
    proc.kill()
    proc.wait()
    print 'kill adb shell logcat thread: %d' % proc.pid
    generate_script(pkName, resolution)
