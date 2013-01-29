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
    def __init__(self, theName, newState):
        self.name = theName
        self.state = newState
        self.stateChanged = True
        self.stateFileName = "pool.dat"

        # identity
        self.model = ""
        self.rev = ""
        self.title = ""
        self.date = ""
        self.time = ""

        # configuration
        self.options = 0
        self.tempScale = ""
        
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
        self.pump = Equipment("Pump", self)
        self.spa = Equipment("Spa", self)
        self.aux1 = Equipment("Cleaner", self)
        self.aux2 = Equipment("Blower", self)
        self.aux3 = Equipment("Aux 3", self)
        self.aux4 = Equipment("Pool Light", self)
        self.aux5 = Equipment("Spa Light", self)
        self.aux6 = Equipment("Aux 6", self)
        self.aux7 = Equipment("Aux 7", self)
        self.heater = Equipment("Heater", self)

        self.equipList = [self.pump,
                            self.spa,
                            self.aux1,
                            self.aux2,
                            self.aux3,
                            self.aux4,
                            self.aux5,
                            self.aux6,
                            self.aux7,
                            self.heater]

        # Modes
        self.cleanMode = Mode("Clean Mode", self, 
                              [self.pump, self.aux1])
        self.spaMode = Mode("Spa Mode", self, 
                            [self.spa, self.heater, self.aux4, self.aux5])
        self.lightsMode = Mode("Lights Mode", self, 
                              [self.aux4, self.aux5])
               
        # initiate interface and panels
        self.master = Panel("Master", self.state, self)
#        self.oneTouchPanel = OneTouchPanel("One Touch", self.state, self)
#        self.spaLinkPanel = SpaLinkPanel("SpaLink", self.state, self)
        self.allButtonPanel = AllButtonPanel("All Button", self.state, self)
        self.panels = {allButtonPanelAddr: self.allButtonPanel,
#                       oneTouchPanelAddr: self.oneTouchPanel,
#                       spaLinkPanelAddr: self.spaLinkPanel,
                        }
        self.panel = self.panels.values()[0]
        self.interface = Interface("RS485", self.state, RS485Device, self)

        # get control sequences for equipment from the panel
        for equip in self.equipList:
            equip.action = self.panel.getAction(equip)

        # start cron thread
        cronThread = threading.Thread(target=self.doCron)
        cronThread.start()

    def doCron(self):
        while True:
            # check the time every hour
            self.checkTime()
            time.sleep(3600)
        
    def checkTime(self):
        if (self.date != "") and (self.time != ""):
            realTime = time.localtime()
            poolTime = time.strptime(self.date+self.time, '%m/%d/%y %a%I:%M %p')
            diffTime = (realTime.tm_year - poolTime.tm_year,
                        realTime.tm_mon - poolTime.tm_mon,
                        realTime.tm_mday - poolTime.tm_mday,
                        realTime.tm_hour - poolTime.tm_hour,
                        realTime.tm_min - poolTime.tm_min - 1)
            if diffTime != (0, 0, 0, 0, 0):
                log("controller time", time.asctime(poolTime))
                log("adjusting to", time.asctime(realTime))
                self.panel.adjustTime(diffTime)

    def setModel(self, model, rev=""):
        if model != self.model:
            self.model = model
            self.rev = rev
            self.stateChanged = True
        self.logState()        

    def setTitle(self, title):
        if title != self.title:
            self.title = title
            self.stateChanged = True
        self.logState()        

    def setDate(self, theDate):
        if theDate != self.date:
            self.date = theDate
            self.stateChanged = True
        self.logState()        

    def setTime(self, theTime):
        if theTime != self.time:
            self.time = theTime
            self.stateChanged = True
        self.logState()        
        
    def setAirTemp(self, temp):
        if temp[0] != self.airTemp:
            self.airTemp = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.logState()        
                    
    def setPoolTemp(self, temp):
        if temp[0] != self.poolTemp:
            self.poolTemp = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.logState()        
        
    def setSpaTemp(self, temp):
        if temp[0] != self.spaTemp:
            self.spaTemp = temp[0]
            self.tempScale = temp[1]
            self.stateChanged = True
        self.logState()        

    def logState(self):
        if self.stateChanged:
            stateFile = open(self.stateFileName, "w")
            stateFile.write(self.printState())
            stateFile.close()
            stateChanged = False
                
    def printState(self, start="", end="\n"):
        msg  = start+"Title:      "+self.title+end
        msg += start+"Model:      "+self.model+" Rev "+self.rev+end
        msg += start+"Date:       "+self.date+end
        msg += start+"Time:       "+self.time+end
        msg += start+"Air Temp:    %d°%s" %  (self.airTemp, self.tempScale)+end
        msg += start+"Pool Temp:   %d°%s" %  (self.poolTemp, self.tempScale)+end
        msg += start+"Spa Temp:    %d°%s" %  (self.spaTemp, self.tempScale)+end
        for equip in self.equipList:
            if equip.name != "":
                msg += start+"%-12s"%(equip.name+":")+equip.printState()+end
        return msg

class Equipment:
    # equipment states
    stateOff = 0
    stateOn = 1
    stateEna = 2
    stateEnh = 4

    def __init__(self, name, thePool, theAction=None):
        self.name = name
        self.pool = thePool
        self.action = theAction
        self.state = Equipment.stateOff

    def setState(self, newState):
        # sets the state of the equipment object, not the actual equipment
        self.state = newState
        self.pool.stateChanged = True
        log(self.name, self.printState())

    def printState(self):
        if self.state == Equipment.stateOn: return "ON"
        elif self.state == Equipment.stateEna: return "ENA"
        elif self.state == Equipment.stateEnh: return "ENH"
        else: return "OFF"

    def changeState(self, newState, wait=False):
        # turns the equipment on or off
        if debug: log(self.name, self.state, newState)
        if ((newState == Equipment.stateOn) and (self.state == Equipment.stateOff)) or\
           ((newState == Equipment.stateOff) and (self.state != Equipment.stateOff)):
            action = ActionThread(self.name+(" On" if newState else " Off"), 
                            [self.action], self.pool.state, self.pool.panel)
            action.start()
            if wait:
#                if debug: log(self.name, "waiting", self.action.event.isSet())
                self.action.event.wait()

class Mode(Equipment):
    # a Mode is defined by an ordered list of Equipment that is turned on or off
    def __init__(self, name, thePool, theEquipList):
        self.name = name
        self.pool = thePool
        self.equipList = theEquipList
        self.state = Equipment.stateOff

    def changeState(self, newState):
        # turns the list of equipment on or off
        self.newState = newState
        # do the work in a thread so this returns synchronously
        modeThread = threading.Thread(target=self.doMode)
        modeThread.start()

    def doMode(self):
        if debugAction: log(self.name, "mode started", self.newState)
        if self.newState == Equipment.stateOn:
            # turn on equipment list in order
            for equip in self.equipList:
                equip.changeState(self.newState, wait=True)
        else:
            # turn off equipment list in reverse order
             for equip in reversed(self.equipList):
                equip.changeState(self.newState, wait=True)
        if debugAction: log(self.name, "mode completed")
        self.state = self.newState
        log(self.name, self.printState())
                
            
