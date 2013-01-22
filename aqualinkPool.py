#!/usr/bin/python
# coding=utf-8

import time

from debugUtils import *
from aqualinkConf import *
from aqualinkInterface import *
from aqualinkPanel import *
from aqualinkOneTouchPanel import *
from aqualinkSpaLinkPanel import *

########################################################################################################
# state of the pool and equipment
########################################################################################################
class Pool:
    # constructor
    def __init__(self, theName, theState):
        self.name = theName
        self.state = theState

        # identity
        self.title = ""
        self.date = ""
        self.time = ""

        # environment
        self.airTemp = 0
        self.poolTemp = 0
        self.spaTemp = 0
        self.waterTemp = 0

        # modes
        self.spaMode = False
        self.cleanMode = False
        self.fountainMode = False

        # equipment states
        self.filter = False
        self.cleaner = False
        self.spa = False
        self.heater = False
        self.poolLight = False
        self.spaLight = False

        # initiate interface and panels
        self.master = Panel("Master:  ", self.state, self)
        self.oneTouchPanel = OneTouchPanel("OneTouch:", self.state, self)
        self.spaLinkPanel = SpaLinkPanel("SpaLink: ", self.state, self)
        self.panels = {oneTouchPanelAddr: self.oneTouchPanel,
                       spaLinkPanelAddr: self.spaLinkPanel}
        self.interface = Interface("Serial:  ", self.state, serialDevice, self)

    def spaOn(self):
        if not self.spa:
            self.spaLinkPanel.spaMode()

    def spaOff(self):
        if self.spa:
            self.spaLinkPanel.spaMode()

    def lightsOn(self):
        self.spaLinkPanel.LightsOn()

    def lightsOff(self):
        self.spaLinkPanel.LightsOff()

    def printState(self, delim="\n"):
        msg  = "Title:      "+self.title+delim
        msg += "Date:       "+self.date+delim
        msg += "Time:       "+self.time+delim
        msg += "Air:         %d°" %  (self.airTemp)+delim
        msg += "Pool:        %d°" %  (self.poolTemp)+delim
        msg += "Spa:         %d°" %  (self.spaTemp)+delim
        msg += "Filter:     "+self.printEquipmentState(self.filter)+delim
        msg += "Cleaner:    "+self.printEquipmentState(self.cleaner)+delim
        msg += "Spa:        "+self.printEquipmentState(self.spa)+delim
        msg += "Heater:     "+self.printEquipmentState(self.heater)+delim
        msg += "Pool light: "+self.printEquipmentState(self.poolLight)+delim
        msg += "Spa light:  "+self.printEquipmentState(self.spaLight)+delim
        return msg

    def printEquipmentState(self, equipment):
        return "ON" if equipment else "OFF"
                    
