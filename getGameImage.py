#!/usr/bin/env python
# encoding: utf-8

import cv2
import numpy as np
import sys
import os
import time
import math
import subprocess
from libs.AdbCommand import screencap
from PIL import Image
from libs.GetDeviceInfo import getDeviceInfo

currPath = os.getcwd()
queryImageRoot = os.path.join(currPath, 'queryImage')
x_reduceRatio = 2   #截图横坐标缩放倍数
y_reduceRatio = 2   #截图纵坐标缩放倍数
thumbnailSize = (540.0, 960.0)

def filter_matches(kp1, kp2, matches, ratio = 0.75):
    mkp1, mkp2 = [], []
    for m in matches:
        if len(m) == 2 and m[0].distance < m[1].distance * ratio:
            m = m[0]
            mkp1.append( kp1[m.queryIdx] )
            mkp2.append( kp2[m.trainIdx] )
    p1 = np.float32([kp.pt for kp in mkp1])
    p2 = np.float32([kp.pt for kp in mkp2])
    kp_pairs = zip(mkp1, mkp2)
    return p1, p2, list(kp_pairs)

def getImgCordinate(filePath, sceneFilePath, flag):
    img1 = cv2.imread(filePath)
    img2 = cv2.imread(sceneFilePath)
    detector = cv2.AKAZE_create()  #特征识别算法初始化
    norm = cv2.NORM_HAMMING
    matcher = cv2.BFMatcher(norm)

    if img1 is None:
        print 'Failed to load fn1:', filePath
        sys.exit(1)

    if img2 is None:
        print 'Failed to load fn2:', sceneFilePath
        sys.exit(1)

    if detector is None:
        print 'unknown feature'
        sys.exit(1)

    print 'using akaze'

    kp1, desc1 = detector.detectAndCompute(img1, None)
    kp2, desc2 = detector.detectAndCompute(img2, None)
    print 'matching....'
    raw_matches = matcher.knnMatch(desc1, trainDescriptors=desc2, k=2) #2特征之匹配
    p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)

    if len(p1) >= 4:
        H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)  #获取转换矩阵
        print '%d / %d inliers/matched' % (np.sum(status), len(status))
    else:
        H, status = None, None
        print '%d matches found, not enough for homography estimation' % len(p1)

    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    obj_corners = np.float32([[0,0], [w1, 0], [w1, h1], [0, h1]])
    obj_corners = obj_corners.reshape(1, -1, 2)
    scene_corners = cv2.perspectiveTransform(obj_corners, H)  #坐标映射
    scene_corners = scene_corners.reshape(-1, 2)
    img3 = cv2.rectangle(img2, (int(round(scene_corners[3][0])), int(round(scene_corners[3][1]))), (int(round(scene_corners[1][0])), int(round(scene_corners[1][1]))), (0, 255, 0), 3)
    resultFilePath = os.path.join(queryImageRoot, pkName, flag+'_match.png')
    cv2.imwrite(resultFilePath, img3)
    mid_cordinate_x = int(round((scene_corners[3][0]+scene_corners[1][0])/2))   #计算中心坐标
    mid_cordinate_y = int(round((scene_corners[3][1]+scene_corners[1][1])/2))
    #通过特征提取的图片被缩放了，所以计算真正比例的坐标需要在将计算得到的中心坐标在放大reduceRatio
    return math.floor(mid_cordinate_x*x_reduceRatio), math.floor(mid_cordinate_y*y_reduceRatio)

def thumbnail_pic(path):
    im = Image.open(path)
    x, y = im.size
    # thumbnailSize = x/reduceRatio, y/reduceRatio
    im.thumbnail(thumbnailSize)
    savePath = path.replace('.png', '-thumbnail.png')
    print savePath
    im.save(savePath)
    return savePath

def get_resolution():
    deviceInfo = getDeviceInfo(deviceName)
    resolutioin = deviceInfo['deviceResolution']
    splitInfo = resolutioin.split('x')
    max_width = int(splitInfo[0].split()[0])
    max_height = int(splitInfo[1].split()[0])
    return (max_width, max_height)

if __name__ == '__main__':
    global x_reduceRatio, y_reduceRatio
    queryPicPath = '/Users/helen/Project/autoTest/recordTestScript/queryImage/com.brianbaek.popstar/newGame.png'
    thumbnail_pic(queryPicPath)
    sys.exit()
    clearLogCmd = 'adb shell logcat -c'
    os.system(clearLogCmd)
    #readLogcatCmd = 'adb -s %s logcat -v time' % deviceName
    readLogcatCmd = 'adb logcat -v time'
    proc = subprocess.Popen(readLogcatCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkName = 'noName'
    resolution = get_resolution()
    x_reduceRatio = round(resolution[0]/thumbnailSize[0],2)
    y_reduceRatio = round(resolution[1]/thumbnailSize[1],2)
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
    print 'kill adb shell logcat thread: %d, pkName is %s' % (proc.pid, pkName)

    screenCapFlag = raw_input("start to capture: ")
    #为了等待需要截图的画面，如果输入是'cap'的话，则开始截图，否则等待
    while True:
        if screenCapFlag == 'start':
            print 'start to screencap'
            break
        else:
            time.sleep(1)
            screenCapFlag = raw_input("start to capture: ")
    #如果打开失败，或者是闪退，则输入'stop'退出
    if screenCapFlag != 'stop':
        queryPkImageRoot = os.path.join(queryImageRoot, pkName)
        if os.path.isdir(queryPkImageRoot) is False:
            os.makedirs(queryPkImageRoot)

        screenCapName = 'start'  #第一次截图的名字为start，后面的名字根据输入获取
        while True:
            startTime = time.time()
            #queryImagePath = os.path.join(queryImageRoot, pkName, '%s-enter-part.png' % pkName)
            sceneFilePath = os.path.join(queryImageRoot, pkName, '%s.png'%screenCapName)
            screencap(sceneFilePath, None)

            #queryImageThumbnailPath = thumbnail_pic(queryImagePath)
            sceneFileThumbnailPath = thumbnail_pic(sceneFilePath)

            #print getImgCordinate(queryImageThumbnailPath, sceneFileThumbnailPath, 'start')
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


