#!/usr/bin/python
# coding=utf-8

import struct
import time
import threading

from aqualinkPool import *
from aqualinkPanel import *

########################################################################################################
# All Button panel
########################################################################################################

class AllButtonPanel(Panel):
    """ 
    Aqualink All Button Control Panel

    The All Button control panel has a 16 character by 1 line LCD display, 12 buttons, and 12 LEDs.

    The buttons are:

    The device address for Aqualink serial interface is 0x08-0x0b. The address is set by jumpers.
    
    The following basic Aqualink serial commands are supported:

    Probe
        command: 0x00
        args: none
        
    Ack
        command: 0x01
        args: 2 bytes
            byte 0: 0x00
            byte 1: button number that was pressed
            
    Status
        command: 0x02
        args: 5 bytes
            bytes 0-4:  LED status

    Message
        command: 0x03
        args: 17 bytes
            byte 0: line
            bytes 1-16: message

    Long Message
        command: 0x04
        args: 17 bytes
            byte 0: line
            bytes 1-16: message
    """
    # constructor
    def __init__(self, theName, theContext, thePool):
        Panel.__init__(self, theName, theContext, thePool)

        # addressing
        self.baseAddr = 0x08
        self.maxDevices = 4

        self.degSym = '\xdf'
        
        # commands
        self.cmdLongMsg = Command("longMsg", 0x04, 17)

        # buttons
        self.btnPump         = Button("pump", 0x02)
        self.btnSpa          = Button("spa", 0x01)
        self.btnAux1         = Button("aux1", 0x05)
        self.btnAux2         = Button("aux2", 0x0a)
        self.btnAux3         = Button("aux3", 0x0f)
        self.btnAux4         = Button("aux4", 0x06)
        self.btnAux5         = Button("aux5", 0x0b)
        self.btnAux6         = Button("aux6", 0x10)
        self.btnAux7         = Button("aux7", 0x15)
        self.btnPoolHtr      = Button("poolhtr", 0x12)
        self.btnSpaHtr       = Button("spahtr", 0x17)
        self.btnSolarHtr     = Button("solarhtr", 0x1c)
        self.btnMenu         = Button("menu", 0x09)
        self.btnCancel       = Button("cancel", 0x0e)
        self.btnLeft         = Button("left", 0x13)
        self.btnRight        = Button("right", 0x18)
        self.btnHold         = Button("hold", 0x19)
        self.btnOverride     = Button("override", 0x1e)
        self.btnEnter        = Button("enter", 0x1d)

        # command parsing
        del(self.cmdTable[self.cmdStatus.code])
        del(self.cmdTable[self.cmdMsg.code])
        self.cmdTable.update({self.cmdStatus.code: AllButtonPanel.handleStatus,
                              self.cmdMsg.code: AllButtonPanel.handleMsg,
                              self.cmdLongMsg.code: AllButtonPanel.handleLongMsg})
        self.firstMsg = True

        # action events
        self.msgEvent = threading.Event()

        # create the list of associations between equipment, button codes, and status masks.
        self.equipList = [PanelEquip(self.pool.aux2, self.btnAux2, 0xc000000000),
                          PanelEquip(self.pool.aux3, self.btnAux3, 0x3000000000),
                          PanelEquip(self.pool.aux7, self.btnAux7, 0x0300000000),
                          PanelEquip(self.pool.aux5, self.btnAux5, 0x00c0000000),
                          PanelEquip(self.pool.pump, self.btnPump, 0x0030000000),
                          PanelEquip(self.pool.spa, self.btnSpa, 0x000c000000),
                          PanelEquip(self.pool.aux1, self.btnAux1, 0x0003000000),
                          PanelEquip(self.pool.aux6, self.btnAux6, 0x0000c00000),
                          PanelEquip(self.pool.aux4, self.btnAux4, 0x0000030000),
                          PanelEquip(self.pool.heater, self.btnSpaHtr, 0x000000000f),
                          PanelEquip(self.pool.heater, self.btnPoolHtr, 0x000000f000),
                          PanelEquip(self.pool.heater, self.btnSolarHtr, 0x00000000f0)]

        # add equipment events to the event list
        self.events += [self.msgEvent]
        for equip in self.equipList:
            self.events += [equip.event]
        
        # menu actions
        self.menuAction = Action(self.btnMenu, self.msgEvent)
        self.leftAction = Action(self.btnLeft, self.msgEvent)
        self.rightAction = Action(self.btnRight, self.msgEvent)
        self.cancelAction = Action(self.btnCancel, self.msgEvent)
        self.enterAction = Action(self.btnEnter, self.msgEvent)

    def dupAction(self, nTimes):
        # create a sequence containing a right or left action duplicated n times
        seq = []
        if nTimes != 0:
            action = self.rightAction if nTimes > 0 else self.leftAction
            for i in range(0, abs(nTimes)):
                seq += [action]
        return seq
            
    def adjustTime(self, timeDiff):
        # create and execute a sequence that adjusts the time on the controller by the specified difference.
        if self.context.debug: self.context.log(self.name)
        seq = [self.menuAction] + self.dupAction(3) + [self.enterAction]+ [self.enterAction] +\
               self.dupAction(timeDiff[0]) + [self.enterAction] +\
               self.dupAction(timeDiff[1]) + [self.enterAction] +\
               self.dupAction(timeDiff[2]) + [self.enterAction] +\
               self.dupAction(timeDiff[3]) + [self.enterAction] +\
               self.dupAction(timeDiff[4]) + [self.enterAction]
        action = ActionThread("set time", self.context, seq, self)
        action.start()

    def menu(self):
        if self.context.debug: self.context.log(self.name)
        action = ActionThread("menu", self.context, [self.menuAction], self)
        action.start()

    def left(self):
        if self.context.debug: self.context.log(self.name)
        action = ActionThread("left", self.context, [self.leftAction], self)
        action.start()

    def right(self):
        if self.context.debug: self.context.log(self.name)
        action = ActionThread("right", self.context, [self.rightAction], self)
        action.start()

    def cancel(self):
        if self.context.debug: self.context.log(self.name)
        action = ActionThread("cancel", self.context, [self.cancelAction], self)
        action.start()

    def enter(self):
        if self.context.debug: self.context.log(self.name)
        action = ActionThread("enter", self.context, [self.enterAction], self)
        action.start()

    def getAction(self, poolEquip):
        # return the action associated with the specified equipment
        for equip in self.equipList:
            if equip.equip == poolEquip:
                return equip.action
        return None
                
    # status command
    def handleStatus(self, args):
        cmd = self.cmdStatus
        status = int(args.encode("hex"), 16)
        if status != self.lastStatus:    # only process changed values
            if self.context.debugStatus: self.context.log(self.name, cmd.name, "%010x"%(status))
            for equip in self.equipList:
                shift = min(filter(lambda s: (equip.mask >> s) & 1 != 0, xrange(8*cmd.argLen)))
                newState = (status & equip.mask) >> shift
                oldState = (self.lastStatus & equip.mask) >> shift
                if newState != oldState:
                    if self.context.debugStatus: self.context.log(self.name, cmd.name, equip.equip.name, "state current", "%x"%oldState, "new", "%x"%newState)
                    # set the equipment state
                    equip.equip.setState(newState)
                    # set the event
                    equip.event.set()
            self.lastStatus = status

    # message command
    def handleMsg(self, args):
        cmd = self.cmdMsg
        self.handleMessage(cmd, args)

    # long message command
    def handleLongMsg(self, args):
        cmd = self.cmdLongMsg
        self.handleMessage(cmd, args)

    # handle messages
    def handleMessage(self, cmd, args):
        line = struct.unpack("!B", args[0])[0]
        msg = args[1:].strip(" ")
        if self.context.debugMsg: self.context.log(self.name, cmd.name, line, args[1:])
        msgParts = msg.split()
        if line == 0:
            self.msgEvent.set()
            if len(msgParts) > 1:
                if self.firstMsg:
                    self.pool.setModel(msgParts[0], msgParts[2])
                    self.firstMsg = False
                    return
                if msgParts[1] == "TEMP":
                    if msgParts[0] == "POOL":
                        self.pool.setPoolTemp(self.parseTemp(msgParts[2]))
                    elif msgParts[0] == "SPA":
                        self.pool.setSpaTemp(self.parseTemp(msgParts[2]))
                    elif msgParts[0] == "AIR":
                        self.pool.setAirTemp(self.parseTemp(msgParts[2]))
                    return
                dateParts = msgParts[0].split("/")
                if len(dateParts) > 1:
                    self.pool.setDate(msg)
                    return
                timeParts = msgParts[0].split(":")
                if len(timeParts) > 1:
                    self.pool.setTime(msg)
                    return
            if (msgParts[-1] != "OFF") and (msgParts[-1] != "ON"):
                if self.pool.title == "":
                    self.pool.setTitle(msg)

    def parseTemp(self, msg):
        degPos = msg.find(self.degSym)
        return (int(msg[:degPos]), msg[degPos+1:])

class PanelEquip(object):
    def __init__(self, theEquip, theButton, theMask):
        self.equip = theEquip
        self.button = theButton
        self.mask = theMask
        self.event = threading.Event()
        self.action = Action(self.button, self.event)

