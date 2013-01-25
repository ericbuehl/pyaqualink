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
        self.tempScale = "F"
        
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
        self.pump = Equipment("Pump")
        self.spa = Equipment("Spa")
        self.aux1 = Equipment("Cleaner")
        self.aux2 = Equipment("Blower")
        self.aux3 = Equipment("Aux 3")
        self.aux4 = Equipment("Pool Light")
        self.aux5 = Equipment("Spa Light")
        self.aux6 = Equipment("Aux 6")
        self.aux7 = Equipment("Aux 7")
        self.heater = Equipment("Heater")
        self.none = Equipment() # dummy equipment - FIXME

        self.equipmentList = [self.pump,
                            self.spa,
                            self.aux1,
                            self.aux2,
                            self.aux3,
                            self.aux4,
                            self.aux5,
                            self.aux6,
                            self.aux7,
                            self.heater]
        
#        self.filter = self.pump
#        self.cleaner = self.aux1
#        self.blower = self.aux2
#        self.poolLight = self.aux4
#        self.spaLight = self.aux5

        # initiate interface and panels
        self.master = Panel("Master", self.state, self)
        self.oneTouchPanel = OneTouchPanel("One Touch", self.state, self)
        self.spaLinkPanel = SpaLinkPanel("SpaLink", self.state, self)
        self.allButtonPanel = AllButtonPanel("All Button", self.state, self)
        self.panels = {
#                       oneTouchPanelAddr: self.oneTouchPanel,
#                       spaLinkPanelAddr: self.spaLinkPanel,
                       allButtonPanelAddr: self.allButtonPanel}
        self.interface = Interface("RS485", self.state, RS485Device, self)

    def cleanModeOn(self):
        seq = []
        if not self.pump.state:
            seq += self.allButtonPanel.pumpSeq
        if not self.cleaner.state:
            seq += self.allButtonPanel.aux1Seq
        action = Action("Clean On", seq, self.state, self.allButtonPanel)
        action.start()

    def cleanModeOff(self):
        seq = []
        if self.pump.state:
            seq += self.allButtonPanel.pumpSeq
        if self.cleaner.state:
            seq += self.allButtonPanel.aux1Seq
        action = Action("Clean Off", seq, self.state, self.allButtonPanel)
        action.start()

    def spaModeOn(self):
        seq = []
        if not self.spa.state:
            seq += self.allButtonPanel.spaSeq
        if not self.heater.state:
            seq += self.allButtonPanel.spaHtrSeq
        if not self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if not self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        action = Action("Spa On", seq, self.state, self.allButtonPanel)
        action.start()

    def spaModeOff(self):
        seq = []
        if self.spa.state:
            seq += self.allButtonPanel.spaSeq
        if self.heater.state:
            seq += self.allButtonPanel.spaHtrSeq
        if self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        action = Action("Spa Off", seq, self.state, self.allButtonPanel)
        action.start()

    def lightsOn(self):
        seq = []
        if not self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if not self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        action = Action("Lights On", seq, self.state, self.allButtonPanel)
        action.start()

    def lightsOff(self):
        seq = []
        if self.poolLight.state:
            seq += self.allButtonPanel.aux4Seq
        if self.spaLight.state:
            seq += self.allButtonPanel.aux5Seq
        action = Action("Lights Off", seq, self.state, self.allButtonPanel)
        action.start()

    def printState(self, delim="\n"):
        msg  = "Title:      "+self.title+delim
        msg += "Date:       "+self.date+delim
        msg += "Time:       "+self.time+delim
        msg += "Air Temp:    %d°%s" %  (self.airTemp, self.tempScale)+delim
        msg += "Pool Temp:   %d°%s" %  (self.poolTemp, self.tempScale)+delim
        msg += "Spa Temp:    %d°%s" %  (self.spaTemp, self.tempScale)+delim
        for equipment in self.equipmentList:
            if equipment.name != "":
                msg += "%-12s"%(equipment.name+":")+equipment.printState()+delim
        return msg

# equipment states
stateOff = 0
stateOn = 1
stateEn = 2

class Equipment:
    def __init__(self, name=""):
        self.name = name
        self.state = stateOff

    def setState(self, theState):
        self.state = theState
        if debug: log(self.name, self.printState())

    def printState(self):
        if self.state == stateOn: return "ON"
        elif self.state == stateEn: return "ENA"
        else: return "OFF"

