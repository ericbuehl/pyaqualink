#!/usr/bin/python
# coding=utf-8

import serial
import struct
import threading

from debugUtils import *
from aqualinkConf import *

# ASCII constants
NUL = '\x00'
DLE = '\x10'
STX = '\x02'
ETX = '\x03'

masterAddr = '\x00'          # address of Aqualink controller

class Interface:
    """ Aqualink serial interface

    """
    def __init__(self, theName, theState, serialDevice, thePool):
        """Initialization.
        Open the serial port and find the start of a message."""
        self.name = theName
        self.state = theState
        self.pool = thePool
        if debugData: log(self.name, "opening serial port", serialDevice)
        self.port = serial.Serial(serialDevice, baudrate=9600, 
                                  bytesize=serial.EIGHTBITS, 
                                  parity=serial.PARITY_NONE, 
                                  stopbits=serial.STOPBITS_ONE)
        self.msg = "\x00\x00"
        self.debugRawMsg = ""
        # skip bytes until synchronized with the start of a message
        while (self.msg[-1] != STX) or (self.msg[-2] != DLE):
            self.msg += self.port.read(1)
            if debugRaw: self.debugRaw(self.msg[-1])
        self.msg = self.msg[-2:]
        if debugData: log(self.name, "synchronized")
        # start up the read thread
        readThread = ReadThread("Read:    ", self.state, self.pool)
        readThread.start()
          
    def readMsg(self):
        """ Read the next valid message from the serial port.
        Parses and returns the destination address, command, and arguments as a 
        tuple."""
        while True:                                         
            dleFound = False
            # read what is probably the DLE STX
            self.msg += self.port.read(2)                   
            if debugRaw: 
                self.debugRaw(self.msg[-2])
                self.debugRaw(self.msg[-1])
            while (self.msg[-1] != ETX) or (not dleFound):  
                # read until DLE ETX
                self.msg += self.port.read(1)
                if debugRaw: self.debugRaw(self.msg[-1])
                if self.msg[-1] == DLE:                     
                    # \x10 read, tentatively is a DLE
                    dleFound = True
                if (self.msg[-2] == DLE) and (self.msg[-1] == NUL) and dleFound: 
                    # skip a NUL following a DLE
                    self.msg = self.msg[:-1]
                    # it wasn't a DLE after all
                    dleFound = False                        
            # skip any NULs between messages
            self.msg = self.msg.lstrip('\x00')
            # parse the elements of the message              
            dlestx = self.msg[0:2]
            dest = self.msg[2:3]
            command = self.msg[3:4]
            args = self.msg[4:-3]
            checksum = self.msg[-3:-2]
            dleetx = self.msg[-2:]
            if debugData: debugMsg = printHex(dlestx)+" "+printHex(dest)+" "+\
                                     printHex(command)+" "+printHex(args)+" "+\
                                     printHex(checksum)+" "+printHex(dleetx)
            self.msg = ""
            # stop reading if a message with a valid checksum is read
            if self.checksum(dlestx+dest+command+args) == checksum:
                if debugData: log(self.name, "-->", debugMsg)
                return (dest, command, args)
            else:
                if debugData: log(self.name, "-->", debugMsg, 
                                  "*** bad checksum ***")

    def sendMsg(self, (dest, command, args)):
        """ Send a message.
        The destination address, command, and arguments are specified as a tuple."""
        msg = DLE+STX+dest+command+args
        msg = msg+self.checksum(msg)+DLE+ETX
        for i in range(2,len(msg)-2):                       
            # if a byte in the message has the value \x10 insert a NUL after it
            if msg[i] == DLE:
                msg = msg[0:i+1]+NUL+msg[i+1:]
        if debugData: log(self.name, "<--", printHex(msg[0:2]), 
                          printHex(msg[2:3]), printHex(msg[3:4]), 
                          printHex(msg[4:-3]), printHex(msg[-3:-2]), 
                          printHex(msg[-2:]))
        n = self.port.write(msg)

    def checksum(self, msg):
        """ Compute the checksum of a string of bytes."""                
        return struct.pack("!B", reduce(lambda x,y:x+y, map(ord, msg)) % 256)

    def debugRaw(self, byte):
        """ Debug raw serial data."""
        self.debugRawMsg += byte
        if len(self.debugRawMsg) == 16:
            log(self.name, printHex(self.debugRawMsg))
            self.debugRawMsg = ""
            
    def __del__(self):
        """ Clean up."""
        self.port.close()
                
class ReadThread(threading.Thread):
    """ Message reading thread.

    """
    def __init__(self, theName, theState, thePool):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.state = theState
        self.pool = thePool
        self.lastDest = '\xff'
        
    def readData(self):
        """ Message handling loop.
        Read messages from the interface and if they are addressed to one of the
        panels, send an Ack to the controller and process the command."""
        if debug: log(self.name, "starting read thread")
        while self.state.running:
            # read until the program state changes to not running
            if not self.state.running: break
            (dest, command, args) = self.pool.interface.readMsg()
            try:                         
                # handle messages that are addressed to these panels
                if not monitorMode:      
                    # send Ack if not passively monitoring
                    self.pool.interface.sendMsg((masterAddr,) + \
                                                self.pool.panels[dest].getAckMsg())
                self.pool.panels[dest].parseMsg(command, args)
                self.lastDest = dest
            except KeyError:                      
                # ignore other messages except...
                if (dest == masterAddr) and \
                        (self.lastDest in self.pool.panels.keys()): 
                    # parse ack messages to master that are from these panels
                    self.pool.master.parseMsg(command, args)
        # force all pending panel events to complete
        for panel in self.pool.panels.values():   
            for event in panel.events:
                event.set()
        if debug: log(self.name, "terminating read thread")

