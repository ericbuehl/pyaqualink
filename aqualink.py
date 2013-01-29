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
		self.oneTouchPanelAddr = '\x41',
		self.spaLinkPanelAddr = '\x21',
		self.allButtonPanelAddr = '\x09',
		self.httpPort = 80,
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
if __name__ == "__main__":
    theContext = Context()
    try:
        thePool = Pool("Pool", theContext)
        webUI = WebUI("WebUI", theContext, thePool)
        serialUI = SerialUI("SerialUI", theContext, thePool)
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        theContext.running = False
        time.sleep(1)
        sys.exit(0)

