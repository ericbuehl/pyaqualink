#!/usr/bin/python
# coding=utf-8

import struct
import time
import threading

from debugUtils import *
from aqualinkConf import *
from aqualinkPool import *

########################################################################################################
# Base Aqualink control panel
########################################################################################################

class Panel:
    """
    Base Aqualink control Panel
    """
    
    # constructor
    def __init__(self, theName, theState, thePool):
        self.name = theName
        self.state = theState
        self.pool = thePool

        # commands
        self.cmdProbe = Command("probe", 0x00, 0)
        self.cmdAck = Command("ack", 0x01, 2)
        self.cmdStatus = Command("status", 0x02, 5)
        self.cmdMsg = Command("msg", 0x03, 17)

        # buttons
        self.btnNone = Button("none", 0x00)

        # state
        self.ack = 0x00             # first byte of ack message
        self.button = self.btnNone       # current button pressed
        self.lastAck = 0x0000
        self.lastStatus = 0x0000000000

        # command parsing
        self.cmdTable = {self.cmdProbe.code: Panel.handleProbe,
                         self.cmdAck.code: Panel.handleAck,
                         self.cmdStatus.code: Panel.handleStatus,
                         self.cmdMsg.code: Panel.handleMsg}
                        
        # action events
        self.statusEvent = threading.Event()   # a status message has been received
        self.events = [self.statusEvent]
        
    # return the ack message for this panel        
    def getAckMsg(self):
        args = struct.pack("!B", self.ack)+struct.pack("!B", self.button.code)
        if self.button != self.btnNone:
            if debugAck: log(self.name, "ack", printHex(args))
        self.button = self.btnNone
        return (struct.pack("!B", self.cmdAck.code), args)
        
    # parse a message and perform commands    
    def parseMsg(self, cmd, args):
        cmdCode = int(cmd.encode("hex"), 16)
        try:
            self.cmdTable[cmdCode](self, args)
        except KeyError:
            if debug: log(self.name, "unknown", printHex(cmd), printHex(args))

    # probe command           
    def handleProbe(self, args):
        cmd = self.cmdProbe
        if debug: log(self.name, cmd.name)

    # ack command
    def handleAck(self, args):
        cmd = self.cmdAck
        if args != self.lastAck:       # only display changed values
            self.lastAck = args
            if debugAck: log(self.name, cmd.name, printHex(args))

    # status command
    def handleStatus(self, args):
        cmd = self.cmdStatus
        if args != self.lastStatus:    # only display changed values
            self.lastStatus = args
            if debugStatus: log(self.name, cmd.name, printHex(args))
        self.statusEvent.set()

    # message command
    def handleMsg(self, args):
        cmd = self.cmdMsg
        if debugMsg: log(self.name, cmd.name, printHex(args))
        
class Button:
    def __init__(self, theName, theCode):
        self.name = theName
        self.code = theCode
        
class Command:
    def __init__(self, theName, theCode, theArgLen):
        self.name = theName
        self.code = theCode
        self.argLen = theArgLen

########################################################################################################
# action thread
########################################################################################################
class ActionThread(threading.Thread):
    # constructor
    def __init__(self, theName, theSequence, theState, thePanel):
        threading.Thread.__init__(self, target=self.doAction)
        self.name = theName
        self.sequence = theSequence
        self.state = theState
        self.panel = thePanel
        for action in self.sequence:
            action.event.clear()

    def doAction(self):
        if debugAction: log(self.name, "action started")
        for action in self.sequence:
            if not self.state.running: break
            self.panel.button = action.button # set the button to be sent to start the action
            if debugAction: log(self.name, "button", action.button.name, "sent")
    #        if debugAction: log(self.name, "waiting", self.action.event.isSet())
            action.event.wait()              # wait for the event that corresponds to the completion
            if debugAction: log(self.name, "button", action.button.name, "completed")
            time.sleep(1)
        if debugAction: log(self.name, "action completed")

class Action:
    def __init__(self, theButton, theEvent):
        self.button = theButton
        self.event = theEvent

