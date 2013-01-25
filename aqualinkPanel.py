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

# commands
cmdProbe = '\x00'
cmdAck = '\x01'
cmdStatus = '\x02'
cmdMsg = '\x03'

# buttons
btnNone = '\x00'

class Panel:
    """
    Base Aqualink control Panel
    """
    
    # constructor
    def __init__(self, theName, theState, thePool):
        self.name = theName
        self.state = theState
        self.pool = thePool

        # state
        self.ack = '\x00'       # first byte of ack message
        self.button = '\x00'    # current button pressed
        self.lastAck = '\x00\x00'
        self.lastStatus = '\x00\x00\x00\x00\x00'

        # command parsing
        self.cmdTable = {cmdProbe: Panel.handleProbe,
                         cmdAck: Panel.handleAck,
                         cmdStatus: Panel.handleStatus,
                         cmdMsg: Panel.handleMsg}
                        
        # action events
        self.statusEvent = threading.Event()   # a status message has been received
        self.events = [self.statusEvent]
        
    # return the ack message for this panel        
    def getAckMsg(self):
        args = self.ack+self.button
        self.button = btnNone
        return (cmdAck, args)
        
    # parse a message and perform commands    
    def parseMsg(self, command, args):
        try:
            self.cmdTable[command](self, args)
        except KeyError:
            if debug: log(self.name, "unknown", printHex(command), printHex(args))

    # probe command           
    def handleProbe(self, args):
        if debug: log(self.name, "probe  ")

    # ack command
    def handleAck(self, args):
        if args != self.lastAck:       # only display changed values
            self.lastAck = args
#            if debug: log(self.name, "ack    ", printHex(args))

    # status command
    def handleStatus(self, args):
        if args != self.lastStatus:    # only display changed values
            self.lastStatus = args
            if debug: log(self.name, "status ", printHex(args))
        self.statusEvent.set()

    # message command
    def handleMsg(self, args):
        if debug: log(self.name, "msg    ", printHex(args))

########################################################################################################
# action thread
########################################################################################################
class Action(threading.Thread):
    # constructor
    def __init__(self, theName, theSequence, theState, thePanel):
        threading.Thread.__init__(self, target=self.doAction)
        self.name = theName
        self.sequence = theSequence
        self.state = theState
        self.panel = thePanel

    def doAction(self):
        if debug: log(self.name, "action", self.name, "started")
        for step in self.sequence:
            if not self.state.running: break
            self.panel.button = step[0] # set the button to be sent to start the action
            if debug: log(self.name, "action", self.name, "button", self.panel.btnNames[step[0]], "sent")
            step[1].clear()
            step[1].wait()              # wait for the event that corresponds to the completion
            if debug: log(self.name, "action", self.name, "button", self.panel.btnNames[step[0]], "completed")
            time.sleep(1)
        if debug: log(self.name, "action", self.name, "completed")

        

