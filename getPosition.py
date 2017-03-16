#!/usr/bin/env python
# encoding: utf-8

import time
import signal
import numpy
import collections
import os
from libs.GetDeviceInfo import getDeviceInfo
from subprocess import PIPE, Popen
from threading  import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

finishFlag = False
deviceName = '5LM7N16224000261'
currPath = os.getcwd()
scriptFileRoot = os.path.join(currPath, 'scriptFile')

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
    screenTypeValue = int(content.replace('\r\n', ''))
    screenType = 'portrait'  #默认竖屏
    if screenTypeValue == 0 or screenTypeValue == 2:
        screenType = 'portrait'   #竖屏
    elif screenTypeValue == 1 or screenTypeValue == 3:
        screenType = 'landscape'  #横屏
    return screenType

def get_resolution():
    deviceInfo = getDeviceInfo(deviceName)
    resolutioin = deviceInfo['deviceResolution']
    splitInfo = resolutioin.split('x')
    max_width = int(splitInfo[0].split()[0])
    max_height = int(splitInfo[1].split()[0])
    return (max_width, max_height)


def getevent_position():
    if cmp(deviceName , '5LM7N16224000261') == 0:
        geteventCmd = 'adb shell getevent -lt /dev/input/event5'  #华为Mate8
    elif cmp(deviceName, '63a9bca7') == 0:
        geteventCmd = 'adb shell getevent -lt /dev/input/event4'   #vivo
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
    resolution = get_resolution()
    max_width = resolution[0]
    while noOutput is False or hasLine is False:
        if finishFlag is True:
            break
        try:
            line = q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            noOutput = True
            if hasLine is False:
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

def generate_script():
    signal.signal(signal.SIGINT, signal_handler)
    clickRecord = []
    clickNum = 0
    while finishFlag is False:
        clickNum += 1
        #clickRecord[clickNum] = getevent_position()
        recordValue = getevent_position()
        if len(recordValue) > 0:
            clickRecord.append(recordValue)
            print '*********第%d次点击' % clickNum

    tapNum = 0
    swipeNum = 0
    clickNum = 0
    preClickTime = 0
    scriptFilePath = os.path.join(scriptFileRoot, '%s-testScript.py' % deviceName)
    scriptFile = open(scriptFilePath, 'w')
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
                content = '    time.sleep(%s)\r' % str(diffTime)
                scriptFile.write(content)
            content = "    os.system('adb -s %s shell input tap %d %d')\r"  % (deviceName, record['clickPosition'][0], record['clickPosition'][1])
            scriptFile.write(content)
            tapNum += 1
        elif clickType == 'swipe':
            print '第%d次点击是: %s, 屏幕状态: %s, 坐标是: %s%s, 与第%d时间间隔是%s' % (clickNum, clickType, record['screenType'], str(record['clickStartPosition']), str(record['clickEndPosition']), clickNum - 1, str(diffTime))
            if diffTime > 0:
                content = '    time.sleep(%s)\r' % str(diffTime)
                scriptFile.write(content)
            content = "    os.system('adb -s %s shell input swipe %d %d %d %d')\r" % (deviceName, record['clickStartPosition'][0], record['clickStartPosition'][1], \
                                    record['clickEndPosition'][0], record['clickEndPosition'][1])
            scriptFile.write(content)
            swipeNum += 1
        preClickTime = clickTime
    content = "    os.system('adb -s %s shell pm clear com.example.TestPlugin')\r" % deviceName
    scriptFile.write(content)
    scriptFile.write(content)
    scriptFile.write("    print 'end of test script.......'\r")
    scriptFile.close()
    print 'click次数是：%d, 其中tap 次数是: %d, swipe次数是%d' % (clickNum, tapNum, swipeNum)


if __name__ == '__main__':
    generate_script()
