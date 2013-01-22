#!/usr/bin/python
# coding=utf-8

import serial
import struct

from debugUtils import *
from aqualinkConf import *

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
    def __init__(self, theName, serialDevice):
        self.name = theName
        self.port = serial.Serial(serialDevice, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.msg = "\x00\x00"
        self.debugRawMsg = ""
        # skip bytes until synchronized with the start of a message
        while (self.msg[-1] != STX) or (self.msg[-2] != DLE):
            self.msg += self.port.read(1)
            if debugRaw: self.debugRaw(self.msg[-1])
        self.msg = self.msg[-2:]
          
    # read the next message
    def readMsg(self):
        while True: # keep reading until a message with a valid checksum is read
            # read bytes until the end of message
            dleFound = False
            self.msg += self.port.read(2)   # read the next 2 bytes
            if debugRaw: 
                self.debugRaw(self.msg[-2])
                self.debugRaw(self.msg[-1])
            while (self.msg[-1] != ETX) or (not dleFound):
                self.msg += self.port.read(1)
                if debugRaw: self.debugRaw(self.msg[-1])
                if self.msg[-1] == DLE:
                    dleFound = True
                if (self.msg[-2] == DLE) and (self.msg[-1] == NUL) and dleFound: # skip a NUL following a DLE
                    self.msg = self.msg[:-1]
                    dleFound = False
            self.msg = self.msg.lstrip('\x00')  # skip any NULs between messages
            dlestx = self.msg[0:2]
            dest = self.msg[2:3]
            command = self.msg[3:4]
            args = self.msg[4:-3]
            checksum = self.msg[-3:-2]
            dleetx = self.msg[-2:]
            if debugData: debugMsg = printHex(dlestx)+" "+printHex(dest)+" "+printHex(command)+" "+printHex(args)+" "+printHex(checksum)+" "+printHex(dleetx)
            self.msg = ""
            if self.checksum(dlestx+dest+command+args) == checksum:
                if debugData: log(self.name, "-->", debugMsg)
                return (dest, command, args)
            else:
                if debugData: log(self.name, "-->", debugMsg, "*** bad checksum ***")

    # send a message
    def sendMsg(self, (dest, command, args)):
        msg = DLE+STX+dest+command+args
        msg = msg+self.checksum(msg)+DLE+ETX
        for i in range(2,len(msg)-2):   # if a byte in the message has the value of DLE, add a NUL after it to escape it
            if msg[i] == DLE:
                msg = msg[0:i+1]+NUL+msg[i+1:]
        if debugData: log(self.name, "<--", printHex(msg[0:2]), printHex(msg[2:3]), printHex(msg[3:4]), printHex(msg[4:-3]), printHex(msg[-3:-2]), printHex(msg[-2:]))
        n = self.port.write(msg)

    # compute checksum                
    def checksum(self, msg):
        return struct.pack("!B", reduce(lambda x,y:x+y, map(ord, msg)) % 256)

    # debug raw serial data
    def debugRaw(self, byte):
        self.debugRawMsg += byte
        if len(self.debugRawMsg) == 16:
            log(self.name, printHex(self.debugRawMsg))
            self.debugRawMsg = ""
            
    # destructor
    def __del__(self):
        self.port.close()
                

