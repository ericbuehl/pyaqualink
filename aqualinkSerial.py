#!/usr/bin/python
# coding=utf-8

import sys
import serial
import threading
import struct

# configuration
unitId = 0
RS232Baud = 9600

class SerialUI(object):
    """ Aqualink RS232 serial interface

    """
    def __init__(self, theName, theContext, thePool):
        """Initialization.
        Open the serial port and start the read thread."""
        self.name = theName
        self.context = theContext
        self.pool = thePool
        if self.context.RS232Device == "/dev/stdin":
            self.context.log(self.name, "using stdin", self.context.RS232Device)
            inPort = sys.stdin
            outPort = sys.stdout
        else:
            try:
                self.context.log(self.name, "opening RS232 port", self.context.RS232Device)
                inPort = outPort = serial.Serial(self.context.RS232Device, baudrate=RS232Baud, 
                                          bytesize=serial.EIGHTBITS, 
                                          parity=serial.PARITY_NONE, 
                                          stopbits=serial.STOPBITS_ONE)
            except:
                self.context.log(self.name, "unable to open serial port")
                return
        readRS232Thread = RS232Thread("RS232", self.context, inPort, outPort, self.pool)
        readRS232Thread.start()
        self.context.log(self.name, "ready")

class RS232Thread(threading.Thread):
    """ Message reading thread.
    """
    def __init__(self, theName, theContext, inPort, outPort, thePool):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.context = theContext
        self.inPort = inPort
        self.outPort = outPort
        self.pool = thePool

        self.product = "Pool Controller Serial Adapter Emulator"
        self.version = "A01"

        # command dispatch table        
        self.cmdTable = {"ECHO": RS232Thread.echoCmd,
                        "RSPFMT": RS232Thread.rspfmtCmd,
                        "RST": RS232Thread.rstCmd,
                        "VERS": RS232Thread.versCmd,
                        "DIAG": RS232Thread.diagCmd,
                        "S1": RS232Thread.s1Cmd,
                        "CMDCHR": RS232Thread.cmdchrCmd,
                        "NRMCHR": RS232Thread.nrmchrCmd,
                        "ERRCHR": RS232Thread.errchrCmd,
                        "MODEL": RS232Thread.modelCmd,
                        "OPMODE": RS232Thread.opmodeCmd,
                        "OPTIONS": RS232Thread.optionsCmd,
                        "VBAT": RS232Thread.vbatCmd,
                        "LEDS": RS232Thread.ledsCmd,
                        "PUMPLO": RS232Thread.pumploCmd,
                        "PUMP": RS232Thread.equipCmd,
                        "CLEANR": RS232Thread.equipCmd,
                        "WFALL": RS232Thread.wfallCmd,
                        "SPA": RS232Thread.equipCmd,
                        "UNITS": RS232Thread.unitsCmd,
                        "POOLHT": RS232Thread.poolhtCmd,
                        "SPAHT": RS232Thread.equipCmd,
                        "SOLHT": RS232Thread.solhtCmd,
                        "POOLSP": RS232Thread.poolspCmd,
                        "POOLSP2": RS232Thread.poolsp2Cmd,
                        "SPASP": RS232Thread.spaspCmd,
                        "POOLTMP": RS232Thread.pooltmpCmd,
                        "SPATMP": RS232Thread.spatmpCmd,
                        "AIRTMP": RS232Thread.airtmpCmd,
                        "SOLTMP": RS232Thread.soltmpCmd,
                        # explicit aux commands
                        "AUX1": RS232Thread.equipCmd,
                        "AUX2": RS232Thread.equipCmd,
                        "AUX3": RS232Thread.equipCmd,
                        "AUX4": RS232Thread.equipCmd,
                        "AUX5": RS232Thread.equipCmd,
                        "AUX6": RS232Thread.equipCmd,
                        "AUX7": RS232Thread.equipCmd,
                        # additional key commands
                        "MENU": RS232Thread.menuCmd,
                        "LEFT": RS232Thread.leftCmd,
                        "RIGHT": RS232Thread.rightCmd,
                        "CANCEL": RS232Thread.cancelCmd,
                        "ENTER": RS232Thread.enterCmd
                        }

        # error messages
        self.errMsg = {1: "INVALID COMMAND",
                       2: "BAD COMMAND FORM",
                       3: "BAD CHAR PAST COMMAND",
                       4: "BAD START COMMAND CHAR",
                       5: "BAD COMMAND ARG",
                       6: "SERIAL ADAPTER IS OFFLINE",
                       7: "CTRL OPERATION FAILED",
                       8: "SETPT OPERATION FAILED",
                       9: "485 PROTOCOL ERROR",
                      10: "485 POLL TIME-OUT",
                      11: "485 SETVALUE TIME-OUT",
                      12: "485 GETVALUE TIME-OUT",
                      13: "232 BFR OVERFLOW",
                      14: "CHECKSUM ERROR",
                      15: "SIO LPBK ERROR",
                      16: "EEPROM R/W TEST ERROR",
                      17: "INTERNAL ERROR",
                      18: "VALUE IS UNAVAILABLE",
                      19: "SENSOR IS OPEN",
                      20: "SENSOR IS SHORTED",
                      21: "AUX NOT ASSIGNED TO DIMMER",
                      22: "AUX OFF: DIMMER CTL IGNORED",
                      23: "OPTION SWITCH NOT SET",
                      24: "OPTION SWITCH IS SET",
                      25: "FUNCTION IS LOCKED OUT",
                      26: "PUMP HIGH NOT ON",
                      27: "NOT WHEN SPILLOVER ACTIVE",
                      28: "NOT WHEN FREEZE IS ON",
                      29: "NOT WHEN SPA IS ON",
                      30: "SERVICE MODE IS ACTIVE",
                      31: "TIMEOUT MODE IS ACTIVE",
                      32: "SOLAR SENSOR OPEN OR NOT INSTALLED",
                      99: "UNEXPECTED CMD STATUS"}
                    
        # baud rate table
        self.baudTable = {57600:0, 38400:1, 19200:2, 9600:3, 
                     4800:4, 2400:5, 1200:6, 600:6, 300:7}
                     
        # different allowable forms of boolean values
        self.true = ["ON", "Y", "T", "TRUE", "YES", "1"]
        self.false = ["OFF", "N", "F", "FALSE", "NO", "0"] 

        # Initialize the state
        self.adapterState = AdapterState()

        # equipment dispatch table
        self.equipTable = {"PUMP": self.pool.pump,
                           "SPA": self.pool.spa,
                           "CLEANR": self.pool.aux1,
                           "AUX1": self.pool.aux1,
                           "AUX2": self.pool.aux2,
                           "AUX3": self.pool.aux3,
                           "AUX4": self.pool.aux4,
                           "AUX5": self.pool.aux5,
                           "AUX6": self.pool.aux6,
                           "AUX7": self.pool.aux7,
                           "SPAHT": self.pool.heater,
                           }

    def readData(self):
        """ Message handling loop.
        Read messages from the interface and process the command."""
        if self.context.debug: self.context.log(self.name, "starting RS232 read thread")
        while self.context.running:
            # read until the program state changes to not running
            if not self.context.running: break
            msg = self.readMsg()
            if self.adapterState.echo:
                self.sendMsg(msg)
            self.sendMsg(self.parseMsg(msg))
        if self.context.debug: self.context.log(self.name, "terminating RS232 read thread")

    def readMsg(self):
        """ Read the next message from the serial port."""
        return self.inPort.readline().strip("\n")
                               
    def sendMsg(self, msg):
        n = self.outPort.write(msg+"\n")
        
    # parse a message and perform commands    
    def parseMsg(self, msg):
        # parse the message
        if msg[0] != self.adapterState.cmdChr:
            return self.error(4)
        try:
            oper = ""
            value = ""
            if msg[-1] in ["?", "+"]:      # query or step
                cmd = msg[1:-1]
                oper = msg[-1]
            else:
                equal = msg.find("=")
                if equal > 0:       # set
                    cmd = msg[1:equal]
                    oper = "="
                    value = msg[equal+1:]
                else:               # action
                    cmd = msg[1:]
            cmd = cmd.upper()
        except:
            return self.error(2)
        try:
            if self.context.debug: self.context.log(self.name, cmd, oper, value)
            response = self.cmdTable[cmd](self, cmd, oper, value)
        except KeyError:
            if cmd[0:3] == "AUX":
                auxDev = int(cmd[3:])
                cmd = cmd[0:3]
                if self.context.debug: self.context.log(self.name, cmd, oper, value)
                response = self.auxCmd(cmd, auxdev, oper, value)
            else:
                if self.context.debug: self.context.log(self.name, "unknown", cmd)
                response = self.error(1)
        return response

    def response(self, cmd="", oper="", value=""):
        # build a response message
        return self.adapterState.nrmChr+"00"+(cmd+oper if self.adapterState.respFmt == 0 else "")+value
        
    def error(self, code):
        # build an error message
        return self.adapterState.errChr+"%02d"%code+(self.errMsg[code] if self.adapterState.respFmt == 0 else "")
                    
    def setBoolean(self, value, true, false):
        # set a boolean value according to the specified value choices
        if value in self.true:
            return 1
        else:
            return 0
        
    def setChr(self, value):
        # set a character to the specified ASCII value
        if int(value) in range(33, 126):
            return struct.pack("!B", int(value))
        else:
            return 0

    def equipState(self, state):
        # consider any non zero state to be on
        return "0" if state == 0 else "1"

    # command handling
                    
    def echoCmd(self, cmd, oper="", value=""):
        if oper == "=":
            self.adapterState.echo = self.setBoolean(value, True, False)
        return self.response(cmd, "=", str(self.adapterState.echo))

    def rspfmtCmd(self, cmd, oper, value):
        if oper == "=":
            self.adapterState.respFmt = self.setBoolean(value, "1", "0")
        return self.response(cmd, "=", str(self.adapterState.respFmt))

    def rstCmd(self, cmd, oper, value):
        # set state to default values and return the product name and version
        del(self.adapterState)
        self.adapterState = AdapterState()
        return self.response(self.product+", Rev "+self.version)

    def versCmd(self, cmd, oper, value):
        return self.response(cmd, "=", self.version)

    def diagCmd(self, cmd, oper, value):
        return self.response("OK")

    def s1Cmd(self, cmd, oper, value):
        return self.response("%02d"%(8*unitId+baudTable[RS232Baud]))

    def cmdchrCmd(self, cmd, oper, value):
        if oper == "=":
            chr = self.setChr(value)
            if chr != 0:
                self.adapterState.cmdChr = chr
            else:
                return self.error(5)
        return self.response(cmd, "=", str(struct.unpack("!B", self.adapterState.cmdChr)[0]))

    def nrmchrCmd(self, cmd, oper, value):
        if oper == "=":
            chr = self.setChr(value)
            if chr != 0:
                self.adapterState.nrmChr = chr
            else:
                return self.error(5)
        return self.response(cmd, "=", str(struct.unpack("!B", self.adapterState.nrmChr)[0]))

    def errchrCmd(self, cmd, oper, value):
        if oper == "=":
            chr = self.setChr(value)
            if chr != 0:
                self.adapterState.errChr = chr
            else:
                return self.error(5)
        return self.response(cmd, "=", str(struct.unpack("!B", self.adapterState.errChr)[0]))

    def modelCmd(self, cmd, oper, value):
        return self.response(cmd, "=", self.pool.model)

    def opmodeCmd(self, cmd, oper, value):
        return self.response(cmd, "=", self.pool.opMode)

    def optionsCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.options))

    def vbatCmd(self, cmd, oper, value):
        return self.error(18)

    def ledsCmd(self, cmd, oper, value):
        return self.response(cmd, "=", "%d "*5 % struct.unpack("!BBBBB", struct.pack("!Q", self.pool.panel.lastStatus)[3:]))

    def pumploCmd(self, cmd, oper, value):
        return self.error(23)

    def equipCmd(self, cmd, oper, value):
        if oper == "=":
            if int(value) in range(0,2):
                self.equipTable[cmd].changeState(int(value), wait=True)
            else:
                return self.error(5)
        elif oper == "+":
            if cmd[0:3] == "AUX":
                return self.error(21)
            else:
                return self.error(3)
        return self.response(cmd, "=", self.equipState(self.equipTable[cmd].state))

#    def cleanrCmd(self, cmd, oper, value):
#        return self.error(23)

    def wfallCmd(self, cmd, oper, value):
        return self.error(23)

#    def spaCmd(self, cmd, oper, value):
#        if oper == "=":
#            if int(value) in range(0,2):
#                self.pool.spa.changeState(int(value), wait=True)
#            else:
#                return self.error(5)
#        return self.response(cmd, "=", self.equipState(self.pool.spa.state))

    def unitsCmd(self, cmd, oper, value):
        if oper == "=":
            if value in ["C", "F"]:
                self.pool.tempScale = value
            else:
                return self.error(5)
        return self.response(cmd, "=", self.pool.tempScale)

    def poolhtCmd(self, cmd, oper, value):
        self.spahtCmd(self, cmd, oper, value)

#    def spahtCmd(self, cmd, oper, value):
#        if oper == "=":
#            if int(value) in range(0,2):
#                self.pool.heater.changeState(int(value), wait=True)
#            else:
#                return self.error(5)
#        return self.response(cmd, "=", self.equipState(self.pool.heater.state))

    def solhtCmd(self, cmd, oper, value):
        return self.error(32)

    def poolspCmd(self, cmd, oper, value):
        return self.error(18)

    def poolsp2Cmd(self, cmd, oper, value):
        return self.error(18)

    def spaspCmd(self, cmd, oper, value):
        return self.error(18)

    def pooltmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.poolTemp)+self.pool.tempScale)

    def spatmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.spaTemp)+self.pool.tempScale)

    def airtmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.airTemp)+self.pool.tempScale)

    def soltmpCmd(self, cmd, oper, value):
        return self.error(18)

    def auxCmd(self, cmd, auxDev, oper, value):
        pass

    # additional commands added to be able to send buttons to controller
           
    def menuCmd(self, cmd, oper, value):
        self.pool.panel.menu()
        return self.response()
        
    def leftCmd(self, cmd, oper, value):
        self.pool.panel.left()
        return self.response()
        
    def rightCmd(self, cmd, oper, value):
        self.pool.panel.right()
        return self.response()
        
    def cancelCmd(self, cmd, oper, value):
        self.pool.checkTime()
        return self.response()
        
    def enterCmd(self, cmd, oper, value):
        self.pool.panel.enter()
        return self.response()
        
class AdapterState(object):
    def __init__(self):
        # default state
        self.echo = 0
        self.respFmt = 0
        self.cmdChr = "#"
        self.nrmChr = "!"
        self.errChr = "?"


