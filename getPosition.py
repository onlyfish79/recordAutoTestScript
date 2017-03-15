#!/usr/bin/env python
# encoding: utf-8

import time
import sys
import signal
import numpy
import collections
import os
from subprocess import PIPE, Popen
from threading  import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

#ON_POSIX = 'posix' in sys.builtin_module_namess
ON_POSIX = True

MAXWAITTIME=300
finishFlag = False
def timer(proc):
    global finishFlag
    count = MAXWAITTIME
    while count > 0:
        if finishFlag is True:
            break
        count -= 1
        time.sleep(1)
        print 'sleep %d' % (MAXWAITTIME-count)

    finishFlag = True
    #proc.kill()
    #proc.wait()
    print 'end of timer, finishFlag is %d, kill adb shell getevent process.......' % finishFlag

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

def getevent_position():
    geteventCmd = 'adb shell getevent -lt /dev/input/event5'
    p = Popen(geteventCmd, shell=True, stdout=PIPE)
    print p.pid
    #thread.start_new_thread(timer, (proc, ))
    positionRecord = collections.OrderedDict()
    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True # thread dies with the program
    t.start()

    noOutput = False
    hasLine = False
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
    checkGetEventCmd = 'ps aux | grep getevent'
    os.system(checkGetEventCmd)
    print '**********position len is %d' % len(positionRecord)
    clickOp = collections.OrderedDict()
    if len(positionRecord) == 1:
        startTime = positionRecord.keys()[0]
        clickOp['clickType'] = 'tap'
        clickOp['clickStartTime'] = startTime
        clickOp['clickPosition'] = positionRecord[startTime]
        print clickOp
    elif len(positionRecord) > 1:
        startTime = positionRecord.keys()[0]
        startPosition = positionRecord[startTime]
        endTime = positionRecord.keys()[-1]
        endPosition = positionRecord[endTime]
        startVect = numpy.array(startPosition)
        endVect = numpy.array(endPosition)
        eucDist = round(numpy.linalg.norm(endVect-startVect), 3)
        if eucDist < 20:
            clickOp['clickType'] = 'tap'
            clickOp['clickStartTime'] = startTime
            clickOp['clickPosition'] = startPosition
        else:
            clickOp['clickType'] = 'swipe'
            clickOp['clickStartTime'] = startTime
            clickOp['clickEndTime'] = endTime
            clickOp['clickStartPosition'] = startPosition
            clickOp['clickEndPosition'] = endPosition
            clickOp['eucDist'] = eucDist
        print clickOp
    print 'end of getevent position....'
    return clickOp


signal.signal(signal.SIGINT, signal_handler)
#clickRecord = collections.OrderedDict()
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
for record in clickRecord:
    clickNum += 1
    clickType = record['clickType']
    clickTime = record['clickStartTime']
    if clickNum > 1:
        diffTime = round(float(clickTime)-float(preClickTime), 1)
        print '第%d次点击是: %s, 与第%d时间间隔是%s' % (clickNum, clickType, clickNum - 1, str(diffTime))
    else:
        print '第%d次点击是: %s' % (clickNum, clickType)

    if clickType == 'tap':
        tapNum += 1
    elif clickType == 'swipe':
        swipeNum += 1
    preClickTime = clickTime
print 'click次数是：%d, 其中tap 次数是: %d, swipe次数是%d' % (clickNum, tapNum, swipeNum)



