#!/usr/bin/python
# coding=utf-8

import sys
import time
import threading

from debugUtils import *
from webUtils import *
from aqualinkConf import *
from aqualinkPool import *
from aqualinkInterface import *
from aqualinkPanel import *
from aqualinkWeb import *

########################################################################################################
# message reading thread
########################################################################################################
class ReadThread(threading.Thread):
    # constructor
    def __init__(self, state, serialDevice, theAddr, thePool, thePanel):
        threading.Thread.__init__(self, target=self.readData)
        self.state = state
        self.pool = thePool
        self.panel = thePanel
        self.interface = Interface(serialDevice)
        self.addr = theAddr
        self.lastDest = '\x00'
        
    # data reading loop
    def readData(self):
        if debug: log("starting read thread")
        while self.state.running:
            if not self.state.running: break
            (dest, command, args) = self.interface.readMsg()
            if (dest == self.addr):# or (self.lastDest == self.addr): # messages that are related to this device
                if not monitorMode:                                 # send ACK if not passively monitoring
                    self.interface.sendMsg(masterAddress, cmdAck, ['\x8b', thePanel.button])
                    thePanel.button = btnNone
                self.panel.parseMsg(command, args)
            self.lastDest = dest
        del(self.interface)
        if debug: log("terminating read thread")

########################################################################################################
# program state
########################################################################################################
class State:
    # constructor
    def __init__(self):
        self.running = True         # True until something terminates the program
    
########################################################################################################
# main routine
########################################################################################################
if __name__ == "__main__":
    theState = State()
    try:
        thePool = Pool()
        thePanel = Panel(theState, thePool)
        readThread = ReadThread(theState, serialDevice, panelAddress, thePool, thePanel)
        readThread.start()
        webThread = WebThread(theState, httpPort, thePool, thePanel)
        webThread.start()
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        theState.running = False
        for action in thePanel.actions:
            action.set()
        time.sleep(1)
        sys.exit(0)

