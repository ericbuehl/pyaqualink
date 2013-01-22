#!/usr/bin/python
# coding=utf-8

import struct
import time
import threading

from debugUtils import *
from aqualinkConf import *
from aqualinkPanel import *

########################################################################################################
# SpaLink panel
########################################################################################################
# addressing
baseAddr = '\x20'
maxDevices = 3

# buttons
btn1 = '\x09'
btn2 = '\x06'
btn3 = '\x03'
btn4 = '\x08'
btn5 = '\x02'
btn6 = '\x07'
btn7 = '\x04'
btn8 = '\x01'

class SpaLinkPanel(Panel):
    # constructor
    def __init__(self, theName, theState, thePool):
        Panel.__init__(self, theName, theState, thePool)

        # button names
        self.btnNames = {btn1: "1",
                         btn2: "2",
                         btn3: "3",
                         btn4: "4",
                         btn5: "5",
                         btn6: "6",
                         btn7: "7",
                         btn8: "8"}
            
        # button sequences
        self.poolLightOnSeq = [(btn6, self.statusEvent)]
        self.spaLightOnSeq = [(btn7, self.statusEvent)]
        self.LightsOnSeq = [(btn6, self.statusEvent),
                            (btn7, self.statusEvent)]
        self.poolLightOffSeq = [(btn6, self.statusEvent)]
        self.spaLightOffSeq = [(btn7, self.statusEvent)]
        self.LightsOffSeq = [(btn6, self.statusEvent),
                            (btn7, self.statusEvent)]

    def poolLightOn(self):
        actionThread = ActionThread("PoolLightOn", self.poolLightOnSeq, self.state, self)
        actionThread.start()

    def spaLightOn(self):
        actionThread = ActionThread("SpaLightOn", self.spaLightOnSeq, self.state, self)
        actionThread.start()

    def LightsOn(self):
        actionThread = ActionThread("LightsOn", self.LightsOnSeq, self.state, self)
        actionThread.start()

    def poolLightOff(self):
        actionThread = ActionThread("PoolLightOff", self.poolLightOffSeq, self.state, self)
        actionThread.start()

    def spaLightOff(self):
        actionThread = ActionThread("SpaLightOff", self.spaLightOffSeq, self.state, self)
        actionThread.start()

    def LightsOff(self):
        actionThread = ActionThread("LightsOff", self.LightsOffSeq, self.state, self)
        actionThread.start()


