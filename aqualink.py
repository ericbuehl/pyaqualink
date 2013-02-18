#!/usr/bin/python
# coding=utf-8

import sys
import time

from aqualinkPool import *
from aqualinkWeb import *
from aqualinkSerial import *

########################################################################################################
# program configuration and state
########################################################################################################
class Context:
    # constructor
    def __init__(self):
        self.running = True         # True until something terminates the program
        self.defaultConfig()
        self.readConfig()

    def defaultConfig(self):
		self.logFileName = "aqualink.log",
		self.debug = False,
		self.debugData = False,
		self.debugRaw = False,
		self.debugAck = False,
		self.debugStatus = False,
		self.debugAction = False,
		self.debugMsg = False,
		self.debugHttp = False,
		self.debugWeb = False,
		self.RS485Device = "/dev/ttyUSB0",
		self.RS232Device = "/dev/ttyUSB1",
		self.allButtonPanelAddr = '\x09',
		self.httpPort = 8080,
		self.monitorMode = False,
        
    def readConfig(self):
        inFile = open("aqualinkConf.py")
        for line in inFile:
            try:
                line = line[:line.find("#")].strip()
                if line != "":
                    param = line.split("=")
                    setattr(self, param[0].strip(), eval(param[1].strip()))
            except:
                print "Bad configuration parameter"
                print line
        inFile.close()
    
    def log(self, *args):
        message = "%-16s: "%args[0]
        for arg in args[1:]:
            message += arg.__str__()+" "
        logFile = open(self.logFileName, "a")
        logFile.write(time.strftime("%Y-%m-%d %H:%M:%S")+" - "+message+"\n")
        logFile.close()

########################################################################################################
# main routine
########################################################################################################

class M(object):
    """ mock object """
    def __init__(self, d):
        self.d = d
    def __getattribute__(self, k):
        return object.__getattribute__(self, "d")[k]

if __name__ == "__main__":
    theContext = Context()
    thePool = M({"airTemp": 70,
                 "poolTemp": 60,
                 "spaTemp": 80,
                 "title": "Mock Pool",
                 "spa": M({
                     "state": "ON",
                     }),
                 "heater": M({
                     "state": "ON",
                     }),
                 "aux4": M({
                     "state": False,
                     }),
                 "aux5": M({
                     "state": False,
                     }),
                 })
    #thePool = Pool("Pool", theContext)
    #serialUI = SerialUI("SerialUI", theContext, thePool)
    webUI = WebUI("WebUI", theContext, thePool)
    webUI.block()

