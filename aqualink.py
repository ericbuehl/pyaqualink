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
        thePool = Pool(theState)
        thePool.start()
        webThread = WebThread(theState, httpPort, thePool)
        webThread.start()
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        theState.running = False
        for action in thePanel.actions:
            action.set()
        time.sleep(1)
        sys.exit(0)

