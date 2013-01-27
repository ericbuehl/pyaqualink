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

# equipment types
equipPump = 0
equipAux1 = 1
equipAux2 = 2
equipAux3 = 3
equipAux4 = 4
equipAux5 = 5
equipAux6 = 6
equipAux7 = 7
equipSpa = 8
equipHeater = 9
equipMode = 255

# equipment states
stateOff = 0
stateOn = 1
stateEna = 2
stateEnh = 4

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
        self.pump = Equipment("Pump", equipPump, self)
        self.spa = Equipment("Spa", equipSpa, self)
        self.aux1 = Equipment("Cleaner", equipAux1, self)
        self.aux2 = Equipment("Blower", equipAux2, self)
        self.aux3 = Equipment("Aux 3", equipAux3, self)
        self.aux4 = Equipment("Pool Light", equipAux4, self)
        self.aux5 = Equipment("Spa Light", equipAux5, self)
        self.aux6 = Equipment("Aux 6", equipAux6, self)
        self.aux7 = Equipment("Aux 7", equipAux7, self)
        self.heater = Equipment("Heater", equipHeater, self)

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
        self.cleanMode = Mode("Clean Mode", equipMode, self, 
                              [self.pump, self.aux1])
        self.spaMode = Mode("Spa Mode", equipMode, self, 
                            [self.spa, self.heater, self.aux4, self.aux5])
        self.lightsMode = Mode("Lights Mode", equipMode, self, 
                              [self.aux4, self.aux5])
               
        # initiate interface and panels
        self.master = Panel("Master", self.state, self)
        self.oneTouchPanel = OneTouchPanel("One Touch", self.state, self)
        self.spaLinkPanel = SpaLinkPanel("SpaLink", self.state, self)
        self.allButtonPanel = AllButtonPanel("All Button", self.state, self)
        self.panel = self.allButtonPanel
        self.panels = {allButtonPanelAddr: self.allButtonPanel,
#                       oneTouchPanelAddr: self.oneTouchPanel,
#                       spaLinkPanelAddr: self.spaLinkPanel,
                        }
        self.interface = Interface("RS485", self.state, RS485Device, self)

        # get control sequences for equipment from the panel
        for equip in self.equipList:
            equip.sequence = [self.panel.getAction(equip.type)]

    def checkTime(self):
        realTime = time.localtime()
        poolTime = time.strptime(self.date+self.time, '%m/%d/%y %a%I:%M %p')
        diffTime = (realTime.tm_year - poolTime.tm_year,
                    realTime.tm_mon - poolTime.tm_mon,
                    realTime.tm_mday - poolTime.tm_mday,
                    realTime.tm_hour - poolTime.tm_hour,
                    realTime.tm_min - poolTime.tm_min)
        if diffTime != (0, 0, 0, 0, 0):
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
                
    def printState(self, delim="\n"):
        msg  = "Title:      "+self.title+delim
        msg += "Model:      "+self.model+" Rev "+self.rev+delim
        msg += "Date:       "+self.date+delim
        msg += "Time:       "+self.time+delim
        msg += "Air Temp:    %d°%s" %  (self.airTemp, self.tempScale)+delim
        msg += "Pool Temp:   %d°%s" %  (self.poolTemp, self.tempScale)+delim
        msg += "Spa Temp:    %d°%s" %  (self.spaTemp, self.tempScale)+delim
        for equip in self.equipList:
            if equip.name != "":
                msg += "%-12s"%(equip.name+":")+equip.printState()+delim
        return msg

class Equipment:
    def __init__(self, name, theType, thePool, theSequence=None):
        self.name = name
        self.type = theType
        self.pool = thePool
        self.sequence = theSequence
        self.state = stateOff

    def setState(self, newState):
        # sets the state of the equipment object, not the actual equipment
        self.state = newState
        self.pool.stateChanged = True
        if debug: log(self.name, self.printState())

    def printState(self):
        if self.state == stateOn: return "ON"
        elif self.state == stateEna: return "ENA"
        elif self.state == stateEnh: return "ENH"
        else: return "OFF"

    def changeState(self, newState, wait=False):
        # turns the equipment on or off
        if debug: log(self.name, self.state, newState)
        if ((newState == stateOn) and (self.state == stateOff)) or\
           ((newState == stateOff) and (self.state != stateOff)):
            action = Action(self.name+(" On" if newState else " Off"), 
                            self.sequence, self.pool.state, self.pool.panel)
            action.start()
            if wait:
                if debug: log(self.name, "waiting", self.sequence[0][1].isSet())
                self.sequence[0][1].wait()

class Mode(Equipment):
    def __init__(self, name, theType, thePool, theSequence):
        Equipment.__init__(self, name, theType, thePool, theSequence)

    def changeState(self, newState):
        # turns the list of equipment on or off
        self.newState = newState
        # do the work in a thread so this returns synchronously
        modeThread = threading.Thread(target=self.doMode)
        modeThread.start()

    def doMode(self):
        if debugAction: log(self.name, "mode started", self.newState)
        if self.newState:
            # turn on equipment list in order
            for equip in self.sequence:
                equip.changeState(self.newState, wait=True)
        else:
            # turn off equipment list in reverse order
             for equip in reversed(self.sequence):
                equip.changeState(self.newState, wait=True)
        if debugAction: log(self.name, "mode completed")
                
            
