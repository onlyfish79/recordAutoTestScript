#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from math import ceil
import math
#get phone Info
class GetDeviceInfo():
    def __init__(self, deviceId):
        self.deviceInfo = {}
        self.deviceInfo['deviceId'] = deviceId

    def getPropInfo(self, propName):
        result = os.popen("adb -s %s shell getprop | grep %s -w" % (self.deviceInfo['deviceId'], propName))
        propInfo = result.readline().split(':')
        propNameValueFormat = propInfo[1].replace(' ', '').replace('\r\n', '')
        propNameValue = propNameValueFormat[1:-1] #去掉[]
        return propNameValue

    def get_memory_total(self):
        result = os.popen("adb -s %s shell cat /proc/meminfo | grep MemTotal" % self.deviceInfo['deviceId'], "r")
        memInfo = result.readline().split("MemTotal:")
        mem_total = (memInfo[1].replace('\r\n', '')).replace(' ', '')
        mem_total_MB = str(math.floor(int(mem_total[:-2])/1024)) + 'MB'
        return mem_total_MB

    #get number of cpu kernel
    def get_cpu_kel(self):
        result = os.popen("adb -s %s shell cat /sys/devices/system/cpu/kernel_max" % self.deviceInfo['deviceId'])
        cpu_kernel = int(result.readline().replace("\r\n",'')) + 1
        return str(cpu_kernel)

    # get phone resolution
    def get_app_pix(self):
        result = os.popen("adb -s %s shell wm size" % self.deviceInfo['deviceId'], "r")
        pixInfo = result.readline().split("Physical size:")
        resolution = pixInfo[1].replace("\r\n", '')
        return resolution

    def get_device_info(self):
        self.deviceInfo['deviceResolution'] = self.get_app_pix()
        self.deviceInfo['totalMemory'] = self.get_memory_total()
        self.deviceInfo['cpuKernel'] = self.get_cpu_kel()
        self.deviceInfo['deviceRelease'] = self.getPropInfo("ro.build.version.release")
        self.deviceInfo['deviceModel'] = self.getPropInfo("ro.product.model")
        self.deviceInfo['deviceBrand'] = self.getPropInfo("ro.product.brand")
        self.deviceInfo['cpuArch'] = self.getPropInfo("ro.product.cpu.abi")

def getDeviceInfo(deviceId):
    deviceInfoObj = GetDeviceInfo(deviceId)
    deviceInfoObj.get_device_info()
    return deviceInfoObj.deviceInfo

if __name__ == '__main__':
    print getDeviceInfo("FA5B3BJ01146")

