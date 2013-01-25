#!/usr/bin/python
# coding=utf-8

import time

from debugUtils import *
from aqualinkConf import *
from aqualinkInterface import *
from aqualinkPanel import *
from aqualinkOneTouchPanel import *
from aqualinkSpaLinkPanel import *
from aqualinkAllButtonPanel import *

########################################################################################################
# state of the pool and equipment
########################################################################################################
class Pool:
    # constructor
    def __init__(self, theName, theState):
        self.name = theName
        self.state = theState

        # identity
        self.model = ""
        self.rev = ""
        self.title = ""
        self.date = ""
        self.time = ""

        # configuration
        self.options = 0
        
        # environment
        self.airTemp = 0
        self.poolTemp = 0
        self.spaTemp = 0
        self.solarTemp = 0
        self.waterTemp = 0

        # modes
        self.opMode = "AUTO"
        self.spaMode = False
        self.cleanMode = False
        self.fountainMode = False

        # equipment
        self.pump = Equipment()
        self.spa = Equipment()
        self.aux1 = Equipment()
        self.aux2 = Equipment()
        self.aux3 = Equipment()
        self.aux4 = Equipment()
        self.aux5 = Equipment()
        self.aux6 = Equipment()
        self.aux7 = Equipment()
        self.heater = Equipment()
        self.filter = self.pump
        self.cleaner = self.aux2
        self.poolLight = self.aux4
        self.spaLight = self.aux5

        # initiate interface and panels
        self.master = Panel("Master:  ", self.state, self)
        self.oneTouchPanel = OneTouchPanel("OneTouch:", self.state, self)
        self.spaLinkPanel = SpaLinkPanel("SpaLink: ", self.state, self)
        self.allButtonPanel = AllButtonPanel("AllButt: ", self.state, self)
        self.panels = {
#                       oneTouchPanelAddr: self.oneTouchPanel,
#                       spaLinkPanelAddr: self.spaLinkPanel,
                       allButtonPanelAddr: self.allButtonPanel}
        self.interface = Interface("RS485:   ", self.state, RS485Device, self)

    def cleanModeOn(self):
        if not self.cleaner:
            self.allButtonPanel.cleanMode()

    def cleanModeOff(self):
        if self.cleaner:
            self.allButtonPanel.cleanMode()

    def spaModeOn(self):
        if not self.spa:
            self.allButtonPanel.spaMode()

    def spaModeOff(self):
        if self.spa:
            self.allButtonPanel.spaMode()

    def lightsOn(self):
        seq = []
        if not self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if not self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        actionThread = ActionThread("LightsOn", seq, self.state, self.allButtonPanel)
        actionThread.start()

    def lightsOff(self):
        seq = []
        if self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        actionThread = ActionThread("LightsOff", seq, self.state, self.allButtonPanel)
        actionThread.start()

    def printState(self, delim="\n"):
        msg  = "Title:      "+self.title+delim
        msg += "Date:       "+self.date+delim
        msg += "Time:       "+self.time+delim
        msg += "Air:         %d°" %  (self.airTemp)+delim
        msg += "Pool:        %d°" %  (self.poolTemp)+delim
        msg += "Spa:         %d°" %  (self.spaTemp)+delim
        msg += "Filter:     "+self.printEquipmentState(self.filter.state)+delim
        msg += "Cleaner:    "+self.printEquipmentState(self.cleaner.state)+delim
        msg += "Spa:        "+self.printEquipmentState(self.spa.state)+delim
        msg += "Heater:     "+self.printEquipmentState(self.heater.state)+delim
        msg += "Pool light: "+self.printEquipmentState(self.poolLight.state)+delim
        msg += "Spa light:  "+self.printEquipmentState(self.spaLight.state)+delim
        return msg

    def printEquipmentState(self, equipment):
        return "ON" if equipment else "OFF"

class Equipment:
    def __init__(self, name=""):
        self.name = name
        self.state = False

    def setState(self, theState):
        if theState != 0:
            self.state = True
        else:
            self.state = False
