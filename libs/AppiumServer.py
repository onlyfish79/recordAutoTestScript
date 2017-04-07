# -*- coding: utf-8 -*-
import os
from urllib2 import urlopen
from urllib2 import URLError
import time
import socket
import subprocess
import traceback

class AppiumServer:
    def __init__(self, host, port, bootstrap_port, deviceId, appium_log_path):
        self.pid = -1
        self.host = host
        self.port = port
        self.bootstrap_port = bootstrap_port
        self.deviceId = deviceId
        self.appium_log_path = appium_log_path
        self.successFlag = False
        self.restartNum = 0

    def start_server(self):
        errormsg = ""
        appium_server_url = ""

        try:
            if self.port_is_free(self.host, self.port):
                cmd = 'appium -a ' + self.host + ' -p ' + str(self.port) + " -U " + str(self.deviceId) + " --bootstrap-port " + str(self.bootstrap_port) \
                + ' --session-override --log ' + '"' + self.appium_log_path + '" --local-timezone' + ' --command-timeout 40'
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.pid = p.pid
                print 'appium server pid is %s' % str(self.pid)
                while True:
                    if (os.path.isfile(self.appium_log_path)):
                        readFile = open(self.appium_log_path, 'r')
                        content = readFile.read()
                        if "Welcome" in content and 'requested port may already be in use' not in content:
                            appium_server_url = 'http://' + self.host +':' + str(self.port) +'/wd/hub'
                            print 'start appium success pid is ', p.pid, ', appium server url is ', appium_server_url
                            self.successFlag = True
                        elif 'requested port may already be in use' in content:
                            print 'start appium failed, need to change another free port'
                        else:
                            self.stop_server()
                            print 'other error, see log file: ', self.appium_log_path
                        break
                    else:
                        print 'appium server log is null, sleep 1s....'
                        time.sleep(1)

            else:
                print "port %s is used" % str(self.port)
        except Exception, e:
            errormsg = str(e)
            self.stop_server()
            print "start server fail, port is %d, error is %s" % (self.port, str(traceback.format_exc()))

        return appium_server_url, errormsg

    def port_is_free(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        #returns true when the port is open and false if it's not
        ret_val = s.connect_ex((host, port))
        s.close()
        return ret_val

    def stop_server(self):
        """stop the appium server
        :return:
        """
        # kill myServer
        self.successFlag = False
        print 'stop the appium server'
        #os.system('kill ' + str(self.pid))
        key = 'node /usr/local/bin/appium'
        grep_key = 'grep %s' % key
        sh_grep_key = 'grep "%s"' % key
        ps_appium_cmd = 'ps aux | grep "node /usr/local/bin/appium"'
        result = os.popen(ps_appium_cmd, 'r')
        content = result.readlines()
        result.close()
        for psItem in content:
            if key in psItem and grep_key not in psItem and sh_grep_key not in psItem:
                psItemSplit = psItem.split()
                for psArgs in psItemSplit:
                    if psArgs == str(self.port):
                        #进程id
                        pid = psItemSplit[1]
                        print 'kill appium server, pid is %s' % str(pid)
                        os.system('kill -9 %s' % str(pid))
                        return

    def restart_server(self):
        """reStart the appium server
        """
        self.restartNum += 1
        appiumLogDir = self.appium_log_path[:self.appium_log_path.rfind('/')]
        self.appium_log_path = os.path.join(appiumLogDir, 'appiumServer%d.log' % self.restartNum)
        self.stop_server()
        self.start_server()

    def is_running(self):
        """Determine whether server is running
        :return:True or False
        """
        response = None
        url = self.baseUrl+"/status"
        try:
            response = urlopen(url, timeout=5)

            if str(response.getcode()).startswith("2"):
                return True
            else:
                return False
        except URLError:
            return False
        finally:
            if response:
                response.close()

#if __name__ == "__main__":
#    appiumServerObj = AppiumServer()
#    logfile = "test.log"
#    if os.path.isfile(logfile) is True:
#        os.remove(logfile)

#    appiumServerObj.start_server("127.0.0.1", 30000, 4780, "3344545425", logfile)

