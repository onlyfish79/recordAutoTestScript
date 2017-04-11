#!/usr/bin/env python
# encoding: utf-8

#import sys
import os
import time
import subprocess
from libs.AdbCommand import screencap
from PIL import Image
from libs.GetDeviceInfo import getDeviceInfo

currPath = os.getcwd()
sceneImageRoot = os.path.join(currPath, 'imageFile/sceneImage')
#thumbnail size = 1.5
#portrait_thumbnailSize = (720.0, 1280.0)
#landscape_thumbnailSize = (1280.0, 720.0)
#thumbnail size = 1.2
#portrait_thumbnailSize = (900.0, 1600.0)
#landscape_thumbnailSize = (1600.0, 900.0)
portrait_thumbnailSize = (1080.0, 1920.0)
landscape_thumbnailSize = (1920.0, 1080.0)
deviceName = 'KWG5T17105003967'
#deviceName = '5LM7N16224000261'
#deviceName = 'LGH8689e43a709'

def thumbnail_pic(path, thumbnailSize):
    im = Image.open(path)
    x, y = im.size
    im.thumbnail(thumbnailSize)
    savePath = path.replace('.png', '-thumbnail.png')
    print savePath
    im.save(savePath)
    return savePath

def get_resolution():
    deviceInfo = getDeviceInfo(deviceName)
    resolution = deviceInfo['deviceResolution']
    splitInfo = resolution.split('x')
    max_width = int(splitInfo[0].split()[0])
    max_height = int(splitInfo[1].split()[0])
    return (max_width, max_height)

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

if __name__ == '__main__':
    x_reduceRatio = 2   #截图横坐标缩放倍数
    y_reduceRatio = 2   #截图纵坐标缩放倍数
    clearLogCmd = 'adb shell logcat -c'
    os.system(clearLogCmd)
    #readLogcatCmd = 'adb -s %s logcat -v time' % deviceName
    readLogcatCmd = 'adb logcat -v time'
    proc = subprocess.Popen(readLogcatCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkName = 'noName'
    resolution = get_resolution()
    for line in proc.stdout:
        if 'ActivityManager' in line and 'Displayed' in line:
            line = line.replace('\r\n', '')
            splitLine = line.split(': ')
            pkItem = splitLine[1]
            pkSplit = pkItem.split()
            startInfo = pkSplit[1]
            pkName = startInfo[0:startInfo.find('/')]
            print pkName
            break
    proc.kill()
    proc.wait()
    print 'kill adb shell logcat thread: %d, pkName is %s' % (proc.pid, pkName)

    screenCapFlag = raw_input("start to capture: ")
    #为了等待需要截图的画面，如果输入是'cap'的话，则开始截图，否则等待
    #while True:
    #    if screenCapFlag == 'start':
    #        print 'start to screencap'
    #        break
    #    else:
    #        time.sleep(1)
    #        screenCapFlag = raw_input("start to capture: ")
    #如果打开失败，或者是闪退，则输入'stop'退出
    if screenCapFlag != 'stop':
        scenePkImageRoot = os.path.join(sceneImageRoot, pkName)
        if os.path.isdir(scenePkImageRoot) is False:
            os.makedirs(scenePkImageRoot)

        #screenCapName = 'start'  #第一次截图的名字为start，后面的名字根据输入获取
        screenCapName = screenCapFlag
        while True:
            startTime = time.time()
            sceneFilePath = os.path.join(scenePkImageRoot, '%s.png'%screenCapName)
            screenType = check_portrait_landscape()
            screencap(sceneFilePath, None)

            if cmp(screenType, 'landscape') == 0:
                thumbnailSize = landscape_thumbnailSize
            else:
                thumbnailSize = portrait_thumbnailSize
            print 'thumbnailSize is %s' % str(thumbnailSize)

            if cmp(screenType, 'landscape') == 0:
                x_reduceRatio = round(resolution[0]/thumbnailSize[1],2)
                y_reduceRatio = round(resolution[1]/thumbnailSize[0],2)
            else:
                x_reduceRatio = round(resolution[0]/thumbnailSize[0],2)
                y_reduceRatio = round(resolution[1]/thumbnailSize[1],2)
            print'resolution is %s, x_reduceRatio is %s, y_reduceRatio is %s' % (str(resolution), str(x_reduceRatio), str(y_reduceRatio))

            #sceneFileThumbnailPath = thumbnail_pic(sceneFilePath, thumbnailSize)

            endTime = time.time()
            print 'spend time is %s' % str(round(endTime-startTime, 3))
            while True:
                screenCapName = raw_input("continue to capture, please input screenCap name: ")
                if len(screenCapName) == 0:
                    time.sleep(1)
                    screenCapName = raw_input("continue to capture, please input screenCap name: ")
                else:
                    break
            #如果输入的是'stop'，停止截图
            if screenCapName == 'stop':
                break
    print 'finish to capture....'


