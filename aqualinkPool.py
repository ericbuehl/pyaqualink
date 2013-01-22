#!/usr/bin/python
# coding=utf-8

import time
import threading

from debugUtils import *
from aqualinkConf import *
from aqualinkInterface import *
from aqualinkPanel import *

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
        self.interface = Interface("Serial:  ", serialDevice)
        self.master = Panel("Master:  ", theState, self)
        self.oneTouchPanel = OneTouchPanel("OneTouch:", theState, self)
        self.spaLinkPanel = SpaLinkPanel("SpaLink: ", theState, self)
        self.panels = {oneTouchPanelAddr: self.oneTouchPanel,
                       spaLinkPanelAddr: self.spaLinkPanel}

        readThread = ReadThread("Read:    ", self.state, self)
        readThread.start()

    def spaOn(self):
        self.oneTouchPanel.spaOn()

    def spaOff(self):
        self.oneTouchPanel.spaOff()

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
                    
########################################################################################################
# message reading thread
########################################################################################################
class ReadThread(threading.Thread):
    # constructor
    def __init__(self, theName, theState, thePool):
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.state = theState
        self.pool = thePool
        self.lastDest = '\x00'
        
    # data reading loop
    def readData(self):
        if debug: log(self.name, "starting read thread")
        while self.state.running:
            if not self.state.running: break
            (dest, command, args) = self.pool.interface.readMsg()
            try:                         # messages that are related to this device
                if not monitorMode:      # send ACK if not passively monitoring
                    self.pool.interface.sendMsg(self.pool.panels[dest].getAck())
                self.pool.panels[dest].parseMsg(command, args)
                self.lastDest = dest
            except:                      # ignore other messages except...
                if (dest == '\x00') and (self.lastDest in self.pool.panels.keys()): # ack messages to controller that are from the panels
                    self.pool.master.parseMsg(command, args)
        for panel in self.pool.panels.values():   # force all pending events to complete
            for event in panel.events:
                event.set()
        if debug: log(self.name, "terminating read thread")

