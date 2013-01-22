#!/usr/bin/python
# coding=utf-8

import sys
import time

from debugUtils import *
from aqualinkConf import *
from aqualinkPool import *
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
        thePool = Pool("Pool:    ", theState)
        webUI = WebUI("WebUI:   ", theState, thePool)
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        theState.running = False
        time.sleep(1)
        sys.exit(0)

