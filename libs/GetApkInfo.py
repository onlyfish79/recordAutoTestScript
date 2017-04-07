#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

import os
from os.path import join
from math import floor, ceil
from subprocess import Popen, PIPE
import re
from config import Common

#aapt tools path
AAPT_PATH = join(Common.ANDROID_BUILD_TOOLS_PATH, 'aapt')


class ApkInfo():
    def __init__(self, apkPath):
        self.apkPath = apkPath
        self.apkInfo = {}

    #get apk version, pkName, appName, apkSize
    def getApkInfo(self):
        #get apk package name and version
        cmd = AAPT_PATH + ' dump badging "%s" | head -n 1'
        #使用android-sdk下面的aapt使用上面的命令过滤得到的格式如下"package: name='me.ele' versionCode='96' versionName='6.0' platformBuildVersionName='6.0-2438415'"
        infoRegex1 = re.compile(r"package: name='(.*)' versionCode='(.*)' versionName='(.*)' platformBuildVersionName='(.*)'", re.I)
        #使用该工程下面的tools目录下的aapt, 获取到的格式如下"package: name='me.ele' versionCode='96' versionName='6.0'"
        infoRegex2 = re.compile(r"package: name='(.*)' versionCode='(.*)' versionName='(.*)'", re.I)
        try:
            info = Popen(cmd % self.apkPath, stdout=PIPE, shell=True).communicate()[0].replace('\n', '')
            m = infoRegex1.search(info)
            if m:
                self.apkInfo['pkName'] = m.group(1)
                self.apkInfo['apkVersion'] = m.group(3)
            else:
                m = infoRegex2.search(info)
                if m:
                    self.apkInfo['pkName'] = m.group(1)
                    self.apkInfo['apkVersion'] = m.group(3)
                else:
                    self.apkInfo['pkName'] = "no.pkname"
                    self.apkInfo['apkVersion'] = 'no.version'
        except Exception, e:
            print 'get package name and version catch exception, cmd is %s, error is %s' % (cmd, e)

        #get app name
        cmd = AAPT_PATH + ' dump badging "%s" | grep application:'
        appNameRegex = re.compile(r"application: label='(.+)' icon='(.+)'", re.I)
        try:
            appName = Popen(cmd % self.apkPath, stdout=PIPE, shell=True).communicate()[0].replace('\n','')
            m = appNameRegex.search(appName)
            if m:
                self.apkInfo['appName'] = m.group(1)
            else:
                self.apkInfo['appName'] = self.apkInfo['pkName']
        except Exception, e:
            print 'get app name catch exception, cmd is %s, error is %s' % (cmd, e)


        #get launchable activity
		#使用android-sdk下面的aapt: launchable-activity: name='tv.danmaku.bili.ui.splash.SplashActivity'  label='' icon=''
		#使用tools下面的aapt: launchable activity name='tv.danmaku.bili.ui.splash.SplashActivity'label='' icon=''
        cmd = AAPT_PATH + ' dump badging "%s" | grep "launchable-activity"'
        launchableActivityRegex = re.compile(r"launchable-activity: name='(.*)'  label='(.*)' icon='(.*)'", re.I)
        try:
            lauchableActivity = Popen(cmd % self.apkPath, stdout=PIPE, shell=True).communicate()[0].replace('\n','')
            splitLaunchable = lauchableActivity.split('launchable-activity')
            if len(splitLaunchable) > 2:
                lauchableActivity = lauchableActivity[0:lauchableActivity.rfind('launchable-activity')]
            m = launchableActivityRegex.search(lauchableActivity)
            if m:
                self.apkInfo['launchableActivity'] = m.group(1)
            else:
                self.apkInfo['launchableActivity'] = 'noActivity'
        except Exception, e:
            print 'get lauchable activity catch exception, cmd is %s, error is %s' % (cmd, e)


        size = ceil(os.path.getsize(self.apkPath)/(1024*1000.0))
        self.apkInfo['apkSize'] = str(size) + "M"

def getApkInfo(apkFile):
    apkInfoObj = ApkInfo(apkFile)
    apkInfoObj.getApkInfo()
    return apkInfoObj.apkInfo

if __name__ == '__main__':
#    apkInfo = getApkInfo("com.pdager_138.apk")
    pluginFilePath = '/Users/helen/Project/autoTest/appium-sample/apps/20160804/'
    pluginFiles = {}
    apkInfoList = []
    for root, dirs, files in os.walk(pluginFilePath):
        for name in files:
            pluginFiles[name] = root

    for fileName, filePath in pluginFiles.items():
        if fileName.endswith('.apk') is False:
            continue
        apkFilePath = os.path.join(filePath, fileName)
        apkInfo = getApkInfo(apkFilePath)
        apkInfoList.append(apkInfo)
        #if 'noActivity' in apkInfo['launchableActivity']:
        #    print apkInfo
        #print apkInfo['launchableActivity']
