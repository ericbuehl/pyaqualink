#!/usr/bin/python
# coding=utf-8

import serial, struct, sys, time, threading, socket, select
from webUtils import *
from debugUtils import *
from aqualinkConf import *

########################################################################################################
# state of the pool and equipment
########################################################################################################
class Pool:
    # constructor
    def __init__(self):
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
# Aqualink serial interface
########################################################################################################
# ASCII constants
NUL = '\x00'
DLE = '\x10'
STX = '\x02'
ETX = '\x03'

class Interface:
    # constructor
    def __init__(self, serialDevice):
        self.port = serial.Serial(serialDevice, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.msg = "\x00\x00"
        # skip bytes until synchronized with the start of a message
        while (self.msg[-1] != STX) or (self.msg[-2] != DLE):
            self.msg += self.port.read(1)
        self.msg = self.msg[-2:]
          
    # read the next message
    def readMsg(self):
        while True: # keep reading until a message with a valid checksum is read
            # read bytes until the end of message
            dleFound = False
            self.msg += self.port.read(2)
            while (self.msg[-1] != ETX) or (not dleFound):
                self.msg += self.port.read(1)
                if self.msg[-1] == DLE:
                    dleFound = True
                if (self.msg[-2] == DLE) and (self.msg[-1] == NUL): # skip a NUL following a DLE
                    self.msg = self.msg[:-1]
                    dleFound = False
            self.msg.lstrip('\x00')  # skip any NULs between messages
            dlestx = self.msg[0:2]
            dest = self.msg[2:3]
            command = self.msg[3:4]
            args = self.msg[4:-3]
            checksum = self.msg[-3:-2]
            dleetx = self.msg[-2:]
            self.msg = ""
            if struct.pack("!B", self.checksum(dlestx+dest+command+args)) == checksum:
                if debugData: log("-->", printHex(dlestx), printHex(dest), printHex(command), printHex(args), printHex(checksum), printHex(dleetx))
                return (dest, command, args)
            else:
                if debugData: log("-->", printHex(dlestx), printHex(dest), printHex(command), printHex(args), printHex(checksum), printHex(dleetx), "*bad checksum*")

    # send a message
    def sendMsg(self, addr, command, args):
        bytes = [DLE, STX, addr, command] + args
        bytes = bytes + [struct.pack("!B", self.checksum(bytes)), DLE, ETX]
        for i in range(2,len(bytes)-2):   # if a byte in the message has the value of DLE, add a NUL after it to escape it
            if bytes[i] == DLE:
                bytes = bytes[0:i+1] + NUL + bytes[i+1:]
        msg = "".join(bytes)
        if debugData: log("<--", printHex(msg[0:2]), printHex(msg[2:3]), printHex(msg[3:4]), printHex(msg[4:-3]), printHex(msg[-3:-2]), printHex(msg[-2:]))
        n = self.port.write(msg)

    # compute checksum                
    def checksum(self, bytes):
        return reduce(lambda x,y:x+y, map(ord, bytes)) % 256

    # destructor
    def __del__(self):
        self.port.close()
                
########################################################################################################
# Aqualink One Touch Control Panel
#
#    The One Touch control panel has a 16 character by 12 line LCD display,  6 buttons, and one 
#    tri-state (green/red) LED.
#
#    The buttons are:
#
#       1. OneTouch1
#       2. OneTouch2/Back
#       3. OneTouch3
#       4. Select
#       5. Down
#       6. Up
#
#    The device address for Aqualink serial interface is 0x40-0x43. The address is set with jumpers.
#    
#    The following basic Aqualink serial commands are supported:
#
#    Probe
#        command: 0x00
#        args: none
#        
#    Ack
#        command: 0x01
#        args: 2 bytes
#            byte 0: 0x8b (unknown)
#            byte 1: button number that was pressed
#            
#    Status
#        command: 0x02
#        args: 5 bytes
#            bytes 0-4: 0x7e5a500b10 if device address is 0x40 (unknown)
#                       0x0000000000 turns LED off
#                       0x0000001001 turns LED red
#                       0x0000004004 turns LED green
#
#    The Long Message command is used to put a line of text on the display
#        command: 0x04
#        args: 17 bytes
#            byte 0: Line number on display (0-11)
#            bytes 1:16: display text
#            
#    In addition to the basic Aqualink serial commands, it also responds to the following commands:
#
#    Unknown command sent periodically if panel sends 0x0b as the first byte of the Ack message args.
#        command: 0x05
#        args: none
#        
#    Highlight (invert) Display Line
#        command: 0x08 
#        args: 3 bytes
#            byte 0: Line to highlight (0-11) or 255 to clear highlight
#            bytes 1-2: 0x0000 (unknown)
#
#    Clear Display
#        command: 0x09 
#        args: 2 bytes
#            bytes 0:1: samas first 2 bytes of status command (unknown)
#
#    Highlight (invert) Display Characters
#        command: 0x10 
#        args: 4 bytes
#            byte 0: Line to highlight (0-11)
#            byte 1: Starting character to highlight (0-15)
#            byte 2: Ending character to highlight (0-15)
#            byte 3: 1 to set highlight, 0 to clear highlight
#            
########################################################################################################
# commands
cmdProbe = '\x00'
cmdAck = '\x01'
cmdStatus = '\x02'
cmdMsg = '\x03'
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

btnNames = {btnNone: "none",
            btnOne: "one",
            btnTwo: "two",
            btnThree: "three",
            btnSelect: "select",
            btnDown: "down",
            btnUp: "up"}
            
degree = '\x60'

class Panel:
    # constructor
    def __init__(self, theState, thePool):
        self.state = theState
        self.pool = thePool

        # display state
        self.displayLines = ["", "", "", "", "", "", "", "", "", "", "", ""]
        self.hilitedLine = 255
        self.hilitedStart = 0
        self.hilitedEnd = -1
        self.displayMode = ""

        # button state
        self.button = '\x00'

        # command parsing
        self.dtable =  {cmdProbe: Panel.handleProbe,
                        cmdAck: Panel.handleAck,
                        cmdStatus: Panel.handleStatus,
                        cmdMsg: Panel.handleMsg,
                        cmdLongMsg: Panel.handleLongMsg,
                        cmdHilite: Panel.handleHilite,
                        cmdClear: Panel.handleClear,
                        cmdHiField: Panel.handleHiField}
        self.ack = ['\x00\x00']
        self.status = ['\x00\x00\x00\x00\x00']

        # action events
        self.displayEvent = threading.Event()   # a display line has been updated
        self.hiliteEvent = threading.Event()    # a display line has been highlighted
        self.spaOnEvent = threading.Event()     # the spa has been turned on
        self.spaOffEvent = threading.Event()    # the spa has been turned off
        self.actions = [self.displayEvent, self.hiliteEvent, self.spaOnEvent, self.spaOffEvent]

        # button sequences
        self.spaOn = [(btnDown, self.hiliteEvent),
                 (btnSelect, self.hiliteEvent),
                 (btnOne, self.spaOnEvent),
                 (btnSelect, self.hiliteEvent)]
        self.spaOff = [(btnDown, self.hiliteEvent),
                 (btnSelect, self.hiliteEvent),
                 (btnOne, self.spaOffEvent),
                 (btnSelect, self.hiliteEvent)]
        self.main = [(btnSelect, self.hiliteEvent)]
        self.back = [(btnBack, self.hiliteEvent)]

        # start the thread that analyzes the display
        displayThread = DisplayThread(2, self)
        displayThread.start()
    
    # parse a message and perform commands    
    def parseMsg(self, command, args):
        try:
            self.dtable[command](self, args)
        except KeyError:
            if debug: log("unknown", printHex(command), printHex(args))

    # probe command           
    def handleProbe(self, args):
        if debug: log("probe  ")

    # ack command
    def handleAck(self, args):
        if args != self.ack:       # only display changed values
            self.ack = args
            button = args[1]
            if debug: log("ack    ", printHex(args[0]), btnNames[button])

    # status command
    def handleStatus(self, args):
        if args != self.status:    # only display changed values
            self.status = args
            if debug: log("status ", printHex(args))

    # message command
    def handleMsg(self, args):
        msg = "".join(args).lstrip(" ").rstrip(" ")
        if debug: log("msg    ", msg)

    # long message command
    def handleLongMsg(self, args):
        line = struct.unpack("!B", args[0])[0]
        msg = "".join(args[1:]).lstrip(" ").rstrip(" ")
        if debug: log("longMsg", line, msg)
        self.displayLines[line] = msg
        self.displayEvent.set()

    # highlight line command
    def handleHilite(self, args):
        line = struct.unpack("!B", args[0])[0]
        if debug: log("hilite ", line, printHex(args[1:]))
        self.hiliteDisplay(line)
        self.hiliteEvent.set()

    # clear display command
    def handleClear(self, args):
        if debug: log("clear  ", printHex(args))
        self.clearDisplay()

    # highlight display characters command
    def handleHiField(self, args):
        line = struct.unpack("!B", args[0])[0]
        start = struct.unpack("!B", args[1])[0]
        end = struct.unpack("!B", args[2])[0]
        setClr = struct.unpack("!B", args[3])[0]
        if debug: log("hifield", "%d %d:%d" % (line, start, end), "set" if setClr else "clear")
        if setClr:
            self.hiliteDisplay(line, start, end)
        else:
            self.hiliteDisplay(line)

    # determine the mode of the display
    def setDisplayMode(self):
        if debug: log("setting display mode")
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
        if debug: log("display mode:", self.displayMode)
            
    # set the state of the pool
    def setPoolState(self):
        if debug: log("setting pool state")
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
#            spaLast = self.pool.spa
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
#            if self.pool.spa and (not spaLast):    # spa was turned on
#                self.spaOnEvent.set()
#            elif (not self.pool.spa) and spaLast:  # spa was turned off
#                self.spaOffEvent.set()
        elif self.displayMode == "onetouch":
            if self.displayLines[2][-3:] == " ON":
                self.spaOnEvent.set()
            else:
                self.spaOffEvent.set()
        if debug: log(self.pool.printState())

    def clearDisplay(self):
        for i in range(0,len(self.displayLines)):
            self.displayLines[i] = ""
        self.hilitedLine = -1

    def hiliteDisplay(self, line, start=0, end=-1):
        self.hilitedLine = line
        self.hilitedStart = start
        self.hilitedEnd = end

########################################################################################################
# display analysis thread
########################################################################################################
class DisplayThread(threading.Thread):
    # constructor
    def __init__(self, delay, thePanel):
        threading.Thread.__init__(self, target=self.readDisplay)
        self.delay = delay
        self.panel = thePanel

    def readDisplay(self):
        if debug: log("starting display thread")
        while self.panel.state.running:
            self.panel.displayEvent.clear()
            if debug: log("waiting for display update to start")
            self.panel.displayEvent.wait()
            if not self.panel.state.running: break
            if debug: log("waiting for display update to complete")
            time.sleep(self.delay)      # wait for the display to finish updating
            lastMode = self.panel.displayMode
            self.panel.setDisplayMode()
            if (lastMode == "init") and (self.panel.displayMode != "main"): # put the display in main mode if it didn't start there
                actionThread = ActionThread("Main", self.panel.main, self.panel.state, self.panel)
                actionThread.start()
            self.panel.setPoolState()
        if debug: log("display thread completed")

########################################################################################################
# message reading thread
########################################################################################################
class ReadThread(threading.Thread):
    # constructor
    def __init__(self, state, serialDevice, theAddr, thePool, thePanel):
        threading.Thread.__init__(self, target=self.readData)
        self.state = state
        self.pool = thePool
        self.panel = thePanel
        self.interface = Interface(serialDevice)
        self.addr = theAddr
        self.lastDest = '\x00'
        
    # data reading loop
    def readData(self):
        if debug: log("starting read thread")
        while self.state.running:
            if not self.state.running: break
            (dest, command, args) = self.interface.readMsg()
            if (dest == self.addr):# or (self.lastDest == self.addr): # messages that are related to this device
                if not monitorMode:                                 # send ACK if not passively monitoring
                    self.interface.sendMsg(masterAddress, cmdAck, ['\x8b', thePanel.button])
                    thePanel.button = btnNone
                self.panel.parseMsg(command, args)
            self.lastDest = dest
        del(self.interface)
        if debug: log("terminating read thread")

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
        if debug: log("action", self.name, "started")
        for step in self.sequence:
            if not self.state.running: break
            self.panel.button = step[0] # set the button to be sent to start the action
            if debug: log("action", self.name, "button", btnNames[step[0]])
            step[1].clear()
            step[1].wait()              # wait for the event that corresponds to the completion
        if debug: log("action", self.name, "completed")

########################################################################################################
# web server thread
########################################################################################################
class WebThread(threading.Thread):
    # constructor
    def __init__(self, state, httpPort, thePool, thePanel):
        threading.Thread.__init__(self, target=self.webServer)
        self.state = state
        self.httpPort = httpPort
        self.pool = thePool
        self.panel = thePanel

    # web server loop
    def webServer(self):
        if debug: log("starting web thread")
        # open the socket and listen for connections
        if debug: log("opening port", self.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        try:
        self.socket.bind(("", self.httpPort))
        if debug: log("waiting for connections")
        self.socket.listen(5)
        # handle connections
        try:
            while self.state.running:
                inputs, outputs, excepts = select.select([self.socket], [], [], 1)
                if self.socket in inputs:
                    (ns, addr) = self.socket.accept()
                    name = addr[0]+":"+str(addr[1])+" -"
                    if debug: log(name, "connected")
                    self.handleRequest(ns, addr)
        finally:
            self.socket.close()
#        except:
#            if debug: log("unable to open port", httpPort)
        if debug: log("terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        # got a request, parse it
        request = ns.recv(8192)
        if not request: return
        if debugHttp: log("request:\n", request)
        (verb, path, params) = parseRequest(request)
        if debugHttp: log("parsed verb:", verb, "path:", path, "params:", params)
        try:
            if verb == "GET":
                if path == "/":
                    html  = htmlDocument(displayPage([[self.pool.printState("<br>")]]), 
                                          [self.pool.title], 
                                          refreshScript(10))
                    response = httpHeader(self.pool.title, len(html)) + html
                else:
                    if path == "/spaon":
                        sequence = self.panel.spaOn
                        if self.panel.displayMode != "main":
                            sequence = self.panel.main + sequence
                        actionThread = ActionThread("SpaOn", sequence, self.state, self.panel)
                        actionThread.start()
                        response = httpHeader(self.pool.title)
                    elif path == "/spaoff":
                        sequence = self.panel.spaOff
                        if self.panel.displayMode != "main":
                            sequence = self.panel.main + sequence
                        actionThread = ActionThread("SpaOff", sequence, self.state, self.panel)
                        actionThread.start()
                        response = httpHeader(self.pool.title)
                    elif path == "/main":
                        actionThread = ActionThread("Main", self.panel.main, self.state, self.panel)
                        actionThread.start()
                        response = httpHeader(self.pool.title)
                    elif path == "/back":
                        actionThread = ActionThread("Back", self.panel.back, self.state, self.panel)
                        actionThread.start()
                        response = httpHeader(self.pool.title)
                    else:
                        response = httpHeader(self.pool.title, "404 Not Found")                    
                ns.sendall(response)
        finally:
            ns.close()
            if debug: log("disconnected")

########################################################################################################
# program state
########################################################################################################
class State:
    # constructor
    def __init__(self):
        self.running = True         # True until something terminates the program
    
########################################################################################################
# main routine
########################################################################################################
if __name__ == "__main__":
    theState = State()
    try:
        thePool = Pool()
        thePanel = Panel(theState, thePool)
        readThread = ReadThread(theState, serialDevice, panelAddress, thePool, thePanel)
        readThread.start()
        webThread = WebThread(theState, httpPort, thePool, thePanel)
        webThread.start()
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        theState.running = False
        for action in thePanel.actions:
            action.set()
        time.sleep(1)
        sys.exit(0)

