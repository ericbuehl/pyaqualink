#!/usr/bin/python
# coding=utf-8

import struct
import time
import threading

from debugUtils import *
from aqualinkConf import *

########################################################################################################
# Base Aqualink control panel
########################################################################################################
masterAddr = '\x00'          # address of Aqualink controller

# commands
cmdProbe = '\x00'
cmdAck = '\x01'
cmdStatus = '\x02'
cmdMsg = '\x03'

class Panel:
    """
    Base Aqualink control Panel
    """
    
    # constructor
    def __init__(self, theName, theState, thePool):
        self.name = theName
        self.state = theState
        self.pool = thePool
        self.interface = thePool.interface

        # state
        self.ack = '\x00'       # first byte of ack message
        self.button = '\x00'    # current button pressed
        self.lastAck = '\x00'
        self.lastStatus = '\x00'

        # command parsing
        self.commandTable =  {cmdProbe: Panel.handleProbe,
                        cmdAck: Panel.handleAck,
                        cmdStatus: Panel.handleStatus,
                        cmdMsg: Panel.handleMsg}
                        
        # action events
        self.statusEvent = threading.Event()   # a status message has been received
        self.events = [self.statusEvent]
        
    # return the ack message for this panel        
    def getAck(self):
        args = self.ack+self.button
        self.button = btnNone
        return (masterAddr, cmdAck, args)
        
    # parse a message and perform commands    
    def parseMsg(self, command, args):
        try:
            self.commandTable[command](self, args)
        except KeyError:
            if debug: log(self.name, "unknown", printHex(command), printHex(args))

    # probe command           
    def handleProbe(self, args):
        if debug: log(self.name, "probe  ")

    # ack command
    def handleAck(self, args):
        if args != self.lastAck:       # only display changed values
            self.lastAck = args
#            if debug: log(self.name, "ack    ", printHex(args[0]), btnNames[args[1]])

    # status command
    def handleStatus(self, args):
        if args != self.lastStatus:    # only display changed values
            self.lastStatus = args
            if debug: log(self.name, "status ", printHex(args))
        self.statusEvent.set()

    # message command
    def handleMsg(self, args):
        msg = printHex(args)
        if debug: log(self.name, "msg    ", msg)

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

    def doAction(self):
        if debug: log(self.name, "action", self.name, "started")
        for step in self.sequence:
            if not self.state.running: break
            self.panel.button = step[0] # set the button to be sent to start the action
            if debug: log(self.name, "action", self.name, "button", self.panel.btnNames[step[0]])
            step[1].clear()
            step[1].wait()              # wait for the event that corresponds to the completion
        if debug: log(self.name, "action", self.name, "completed")

########################################################################################################
# One Touch panel
########################################################################################################
# addressing
baseAddr = '\x40'
maxDevices = 4

# commands
cmdLongMsg = '\x04'
cmdHilite = '\x08'  # highlight (invert) the specified line
cmdClear = '\x09'   # clear the display
cmdHiField = '\x10' # set or clear the specified 

# buttons
btnNone = '\x00'
btnOne = '\x03'
btnTwo = '\x02'
btnThree = '\x01'
btnBack = btnTwo
btnSelect = '\x04'
btnDown = '\x05'
btnUp = '\x06'

degree = '\x60'

class OneTouchPanel(Panel):
    """ 
    Aqualink One Touch Control Panel

    The One Touch control panel has a 16 character by 12 line LCD display,  6 buttons, and one 
    tri-state (green/red) LED.

    The buttons are:

       1. OneTouch1
       2. OneTouch2/Back
       3. OneTouch3
       4. Select
       5. Down
       6. Up

    The device address for Aqualink serial interface is 0x40-0x43. The address is set with jumpers.
    
    The following basic Aqualink serial commands are supported:

    Probe
        command: 0x00
        args: none
        
    Ack
        command: 0x01
        args: 2 bytes
            byte 0: 0x8b (unknown)
            byte 1: button number that was pressed
                OneTouch1          0x03
                OneTouch2/Back     0x02
                OneTouch3          0x01
                Select             0x04
                Down               0x05
                Up                 0x06
            
    Status
        command: 0x02
        args: 5 bytes
            bytes 0-4: 0x7e5a500b10 if device address is 0x40 (unknown)
                       0x0000000000 turns LED off
                       0x0000001001 turns LED red
                       0x0000004004 turns LED green

    The Long Message command is used to put a line of text on the display
        command: 0x04
        args: 17 bytes
            byte 0: Line number on display (0-11)
            bytes 1:16: display text
            
    In addition to the basic Aqualink serial commands, it also responds to the following commands:

    Unknown command sent periodically if panel sends 0x0b as the first byte of the Ack message args.
        command: 0x05
        args: none
        
    Highlight (invert) Display Line
        command: 0x08 
        args: 3 bytes
            byte 0: Line to highlight (0-11) or 255 to clear highlight
            bytes 1-2: 0x0000 (unknown)

    Clear Display
        command: 0x09 
        args: 2 bytes
            bytes 0:1: same as first 2 bytes of status command (unknown)

    Highlight (invert) Display Characters
        command: 0x10 
        args: 4 bytes
            byte 0: Line to highlight (0-11)
            byte 1: Starting character to highlight (0-15)
            byte 2: Ending character to highlight (0-15)
            byte 3: 1 to set highlight, 0 to clear highlight          
    """
    # constructor
    def __init__(self, theName, theState, thePool):
        Panel.__init__(self, theName, theState, thePool)

        # display state
        self.displayLines = ["", "", "", "", "", "", "", "", "", "", "", ""]
        self.hilitedLine = 255
        self.hilitedStart = 0
        self.hilitedEnd = -1
        self.displayMode = ""

        # state
        self.ack = '\x8b'   # first byte of ack message

        # command parsing
        self.commandTable.update({cmdLongMsg: OneTouchPanel.handleLongMsg,
                            cmdHilite: OneTouchPanel.handleHilite,
                            cmdClear: OneTouchPanel.handleClear,
                            cmdHiField: OneTouchPanel.handleHiField})

        # action events
        self.displayEvent = threading.Event()   # a display line has been updated
        self.hiliteEvent = threading.Event()    # a display line has been highlighted
        self.spaOnEvent = threading.Event()     # the spa has been turned on
        self.spaOffEvent = threading.Event()    # the spa has been turned off
        self.events = self.events + [self.displayEvent, self.hiliteEvent, self.spaOnEvent, self.spaOffEvent]

        # button sequences
        self.spaOnSeq = [(btnDown, self.hiliteEvent),
                 (btnSelect, self.hiliteEvent),
                 (btnOne, self.spaOnEvent),
                 (btnSelect, self.hiliteEvent)]
        self.spaOffSeq = [(btnDown, self.hiliteEvent),
                 (btnSelect, self.hiliteEvent),
                 (btnOne, self.spaOffEvent),
                 (btnSelect, self.hiliteEvent)]
        self.mainSeq = [(btnSelect, self.hiliteEvent)]
        self.backSeq = [(btnBack, self.hiliteEvent)]

        # button names
        self.btnNames = {btnNone: "none",
                         btnOne: "one",
                         btnTwo: "two",
                         btnThree: "three",
                         btnSelect: "select",
                         btnDown: "down",
                         btnUp: "up"}
            
        # start the thread that analyzes the display
        displayThread = DisplayThread("Display: ", 2, self)
        displayThread.start()

    # long message command
    def handleLongMsg(self, args):
        line = struct.unpack("!B", args[0])[0]
        msg = "".join(args[1:]).lstrip(" ").rstrip(" ")
        if debug: log(self.name, "longMsg", line, msg)
        self.displayLines[line] = msg
        self.displayEvent.set()

    # highlight line command
    def handleHilite(self, args):
        line = struct.unpack("!B", args[0])[0]
        if debug: log(self.name, "hilite ", line, printHex(args[1:]))
        self.hiliteDisplay(line)
        self.hiliteEvent.set()

    # clear display command
    def handleClear(self, args):
        if debug: log(self.name, "clear  ", printHex(args))
        self.clearDisplay()

    # highlight display characters command
    def handleHiField(self, args):
        line = struct.unpack("!B", args[0])[0]
        start = struct.unpack("!B", args[1])[0]
        end = struct.unpack("!B", args[2])[0]
        setClr = struct.unpack("!B", args[3])[0]
        if debug: log(self.name, "hifield", "%d %d:%d" % (line, start, end), "set" if setClr else "clear")
        if setClr:
            self.hiliteDisplay(line, start, end)
        else:
            self.hiliteDisplay(line)

    # determine the mode of the display
    def setDisplayMode(self):
        if debug: log(self.name, "setting display mode")
        if self.displayLines[0] == "EQUIPMENT ON":
            self.displayMode = "equipment"
        elif self.displayLines[11] == "MENU / HELP":
            self.displayMode = "main"
        elif self.displayLines[11] == "SYSTEM ON":
            self.displayMode = "onetouch"
        elif self.displayLines[5] == "MODEL 8156":
            self.displayMode = "init"
        else:
            self.displayMode = "menu"
        if debug: log(self.name, "display mode:", self.displayMode)
            
    # set the state of the pool
    def setPoolState(self):
        if debug: log(self.name, "setting pool state")
        if self.displayMode == "main":  # main display
            self.pool.title = self.displayLines[0]
            self.pool.date = self.displayLines[2]
            self.pool.time = self.displayLines[3]
            if self.displayLines[5] == "FILTER PUMP OFF":
                self.pool.filter = self.pool.cleaner = self.pool.spa = self.pool.heater = self.pool.poolLight = self.pool.spaLight = False
            elif self.displayLines[5] == "SPA ON":
                self.pool.filter = self.pool.spa = self.pool.heater = self.pool.poolLight = self.pool.spaLight = True
                self.pool.cleaner = False
            elif self.displayLines[5] == "SPA COOLDOWN":
                self.pool.filter = self.pool.spa = True
                self.pool.cleaner = self.pool.heater = self.pool.poolLight = self.pool.spaLight = False
            else:
                parts = self.displayLines[5].split(" ")
                if parts[0] == "POOL":
                    self.pool.poolTemp = int(parts[1][:parts[1].find(degree)])
                    self.pool.waterTemp = self.pool.poolTemp
                elif parts[0] == "SPA":
                    self.pool.spaTemp = int(parts[1][:parts[1].find(degree)])
                    self.pool.waterTemp = self.pool.spaTemp
            parts = self.displayLines[6].split(" ")
            if parts[0] == "AIR":
                self.pool.airTemp = int(parts[1][:parts[1].find(degree)])
        elif self.displayMode == "equipment":    # equipment status display
            self.pool.filter = self.pool.cleaner = self.pool.spa = self.pool.heater = self.pool.poolLight = self.pool.spaLight = False
            for msg in self.displayLines:
                if msg == "FILTER PUMP":
                    self.pool.filter = True
                elif msg == "CLEANER":
                    self.pool.cleaner = True
                elif msg == "SPA":
                    self.pool.spa = True
                elif msg == "SPA HEAT":
                    self.pool.heater = True
                elif msg == "POOL LIGHT":
                    self.pool.poolLight = True
                elif msg == "SPA LIGHT":
                    self.pool.spaLight = True
        elif self.displayMode == "onetouch":
            if self.displayLines[2][-3:] == " ON":
                self.spaOnEvent.set()
            else:
                self.spaOffEvent.set()
#        if debug: log(self.name, self.pool.printState())

    def clearDisplay(self):
        for i in range(0,len(self.displayLines)):
            self.displayLines[i] = ""
        self.hilitedLine = -1

    def hiliteDisplay(self, line, start=0, end=-1):
        self.hilitedLine = line
        self.hilitedStart = start
        self.hilitedEnd = end

    def spaOn(self):
        sequence = self.spaOnSeq
        if self.displayMode != "main":
            sequence = self.main + sequence
        actionThread = ActionThread("SpaOn", sequence, self.state, self)
        actionThread.start()

    def spaOff(self):
        sequence = self.spaOffSeq
        if self.displayMode != "main":
            sequence = self.main + sequence
        actionThread = ActionThread("SpaOff", sequence, self.state, self)
        actionThread.start()

########################################################################################################
# One Touch display analysis thread
########################################################################################################
class DisplayThread(threading.Thread):
    # constructor
    def __init__(self, theName, delay, thePanel):
        threading.Thread.__init__(self, target=self.readDisplay)
        self.name = theName
        self.delay = delay
        self.panel = thePanel

    def readDisplay(self):
        if debug: log(self.name, "starting display thread")
        while self.panel.state.running:
            self.panel.displayEvent.clear()
            if debug: log(self.name, "waiting for display update to start")
            self.panel.displayEvent.wait()
            if not self.panel.state.running: break
            if debug: log(self.name, "waiting for display update to complete")
            time.sleep(self.delay)      # wait for the display to finish updating
            lastMode = self.panel.displayMode
            self.panel.setDisplayMode()
            if (lastMode == "init") and (self.panel.displayMode != "main"): # put the display in main mode if it didn't start there
                actionThread = ActionThread("Main", self.panel.main, self.panel.state, self.panel)
                actionThread.start()
            self.panel.setPoolState()
        if debug: log(self.name, "display thread completed")
        
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
        self.poolLightOffSeq = [(btn6, self.statusEvent)]
        self.spaLightOnSeq = [(btn7, self.statusEvent)]
        self.spaLightOffSeq = [(btn7, self.statusEvent)]

    def poolLightOn(self):
        actionThread = ActionThread("PoolLightOn", self.poolLightOnSeq, self.state, self)
        actionThread.start()

    def poolLightOff(self):
        actionThread = ActionThread("PoolLightOff", self.poolLightOffSeq, self.state, self)
        actionThread.start()

    def spaLightOn(self):
        actionThread = ActionThread("SpaLightOn", self.spaLightOnSeq, self.state, self)
        actionThread.start()

    def spaLightOff(self):
        actionThread = ActionThread("SpaLightOff", self.spaLightOffSeq, self.state, self)
        actionThread.start()


