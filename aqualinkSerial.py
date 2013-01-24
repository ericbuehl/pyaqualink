#!/usr/bin/python
# coding=utf-8

import sys
import serial
import threading

from debugUtils import *
from aqualinkConf import *

# configuration
unitId = 0
RS232Baud = 9600

class SerialUI:
    """ Aqualink RS232 serial interface

    """
    def __init__(self, theName, theState, serialDevice, thePool):
        """Initialization.
        Open the serial port and find the start of a message."""
        self.name = theName
        self.state = theState
        self.pool = thePool
        # start up the read thread
        try:
            if debugData: log(self.name, "opening serial port", serialDevice)
            thePort = serial.Serial(serialDevice, baudrate=RS232Baud, 
                                      bytesize=serial.EIGHTBITS, 
                                      parity=serial.PARITY_NONE, 
                                      stopbits=serial.STOPBITS_ONE)
            readRS232Thread = RS232Thread("RS232:   ", self.state, thePort, self.pool)
            readRS232Thread.start()
        except:
            if debugData: log(self.name, "unable to open serial port")

class RS232Thread(threading.Thread):
    """ Message reading thread.

    """
    def __init__(self, theName, theState, thePort, thePool):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.state = theState
        self.port = thePort
        self.pool = thePool

        self.product = "Serial Adapter Emulator"
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
                    "PUMP": RS232Thread.pumpCmd,
                    "CLEANR": RS232Thread.cleanrCmd,
                    "WFALL": RS232Thread.wfallCmd,
                    "SPA": RS232Thread.spaCmd,
                    "POOLHT": RS232Thread.poolhtCmd,
                    "SPAHT": RS232Thread.spahtCmd,
                    "SOLHT": RS232Thread.solhtCmd,
                    "POOLSP": RS232Thread.poolspCmd,
                    "POOLSP2": RS232Thread.poolsp2Cmd,
                    "SPASP": RS232Thread.spaspCmd,
                    "POOLTMP": RS232Thread.pooltmpCmd,
                    "SPATMP": RS232Thread.spatmpCmd,
                    "AIRTMP": RS232Thread.airtmpCmd,
                    "SOLTMP": RS232Thread.soltmpCmd,}

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

        self.adapterState = AdapterState()
            

    def readData(self):
        """ Message handling loop.
        Read messages from the interface and process the command."""
        if debug: log(self.name, "starting RS232 read thread")
        while self.state.running:
            # read until the program state changes to not running
            if not self.state.running: break
            msg = self.readMsg()
            if self.adapterState.echo:
                self.sendMsg(msg)
            self.sendMsg(self.parseMsg(msg))
        if debug: log(self.name, "terminating RS232 read thread")

    def readMsg(self):
        """ Read the next message from the serial port."""
#        return self.port.readline().strip("\n")
        return sys.stdin.readline().strip("\n")
                               
    def sendMsg(self, msg):
#        n = self.port.write(msg+"\n")
        n = sys.stdout.write(msg+"\n")
        
    # parse a message and perform commands    
    def parseMsg(self, msg):
        # parse the message
        if msg[0] != self.adapterState.cmdChr:
            return self.error(4)
        try:
            oper = ""
            value = ""
            if msg[-1] == "?":      # query
                cmd = msg[1:-1]
                oper = "?"
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
            if debug: log(self.name, cmd, oper, value)
            response = self.cmdTable[cmd](self, cmd, oper, value)
        except KeyError:
            if cmd[0:3] == "AUX":
                auxDev = int(cmd[3:])
                cmd = cmd[0:3]
                if debug: log(self.name, cmd, oper, value)
                response = self.auxCmd(cmd, auxdev, oper, value)
            else:
                if debug: log(self.name, "unknown", cmd)
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
        return self.response(cmd, "=", self.pool.options)

    def optionsCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.options))

    def vbatCmd(self, cmd, oper, value):
        pass

    def ledsCmd(self, cmd, oper, value):
        pass

    def pumploCmd(self, cmd, oper, value):
        pass

    def pumpCmd(self, cmd, oper, value):
        pass

    def cleanrCmd(self, cmd, oper, value):
        pass

    def wfallCmd(self, cmd, oper, value):
        pass

    def spaCmd(self, cmd, oper, value):
        pass

    def poolhtCmd(self, cmd, oper, value):
        pass

    def spahtCmd(self, cmd, oper, value):
        pass

    def solhtCmd(self, cmd, oper, value):
        pass

    def poolspCmd(self, cmd, oper, value):
        pass

    def poolsp2Cmd(self, cmd, oper, value):
        pass

    def spaspCmd(self, cmd, oper, value):
        pass

    def pooltmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.poolTemp))

    def spatmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.spaTemp))

    def airtmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.airTemp))

    def soltmpCmd(self, cmd, oper, value):
        return self.response(cmd, "=", str(self.pool.solarTemp))

    def auxCmd(self, cmd, auxDev, oper, value):
        pass
        
class AdapterState:
    def __init__(self):
        # default state
        self.echo = 0
        self.respFmt = 0
        self.cmdChr = "#"
        self.nrmChr = "!"
        self.errChr = "?"


