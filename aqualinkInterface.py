#!/usr/bin/python
# coding=utf-8

import serial
import struct
import threading

# ASCII constants
NUL = '\x00'
DLE = '\x10'
STX = '\x02'
ETX = '\x03'

masterAddr = '\x00'          # address of Aqualink controller

class Interface(object):
    """ Aqualink serial interface

    """
    def __init__(self, theName, theContext, thePool):
        """Initialization.
        Open the serial port and find the start of a message."""
        self.name = theName
        self.context = theContext
        self.pool = thePool
        if self.context.debugData: self.context.log(self.name, "opening RS485 port", self.context.RS485Device)
        self.port = serial.Serial(self.context.RS485Device, baudrate=9600, 
                                  bytesize=serial.EIGHTBITS, 
                                  parity=serial.PARITY_NONE, 
                                  stopbits=serial.STOPBITS_ONE)
        self.msg = "\x00\x00"
        self.debugRawMsg = ""
        # skip bytes until synchronized with the start of a message
        while (self.msg[-1] != STX) or (self.msg[-2] != DLE):
            self.msg += self.port.read(1)
            if self.context.debugRaw: self.debugRaw(self.msg[-1])
        self.msg = self.msg[-2:]
        if self.context.debugData: self.context.log(self.name, "synchronized")
        # start up the read thread
        readThread = ReadThread("Read", self.context, self.pool)
        readThread.start()
        self.context.log(self.name, "ready")
          
    def readMsg(self):
        """ Read the next valid message from the serial port.
        Parses and returns the destination address, command, and arguments as a 
        tuple."""
        while True:                                         
            dleFound = False
            # read what is probably the DLE STX
            self.msg += self.port.read(2)                   
            if self.context.debugRaw: 
                self.debugRaw(self.msg[-2])
                self.debugRaw(self.msg[-1])
            while (self.msg[-1] != ETX) or (not dleFound):  
                # read until DLE ETX
                self.msg += self.port.read(1)
                if self.context.debugRaw: self.debugRaw(self.msg[-1])
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
            cmd = self.msg[3:4]
            args = self.msg[4:-3]
            checksum = self.msg[-3:-2]
            dleetx = self.msg[-2:]
            if self.context.debugData: debugMsg = dlestx.encode("hex")+" "+dest.encode("hex")+" "+\
                                     cmd.encode("hex")+" "+args.encode("hex")+" "+\
                                     checksum.encode("hex")+" "+dleetx.encode("hex")
            self.msg = ""
            # stop reading if a message with a valid checksum is read
            if self.checksum(dlestx+dest+cmd+args) == checksum:
                if self.context.debugData: self.context.log(self.name, "-->", debugMsg)
                return (dest, cmd, args)
            else:
                if self.context.debugData: self.context.log(self.name, "-->", debugMsg, 
                                  "*** bad checksum ***")

    def sendMsg(self, (dest, cmd, args)):
        """ Send a message.
        The destination address, command, and arguments are specified as a tuple."""
        msg = DLE+STX+dest+cmd+args
        msg = msg+self.checksum(msg)+DLE+ETX
        for i in range(2,len(msg)-2):                       
            # if a byte in the message has the value \x10 insert a NUL after it
            if msg[i] == DLE:
                msg = msg[0:i+1]+NUL+msg[i+1:]
        if self.context.debugData: self.context.log(self.name, "<--", msg[0:2].encode("hex"), 
                          msg[2:3].encode("hex"), msg[3:4].encode("hex"), 
                          msg[4:-3].encode("hex"), msg[-3:-2].encode("hex"), 
                          msg[-2:].encode("hex"))
        n = self.port.write(msg)

    def checksum(self, msg):
        """ Compute the checksum of a string of bytes."""                
        return struct.pack("!B", reduce(lambda x,y:x+y, map(ord, msg)) % 256)

    def debugRaw(self, byte):
        """ Debug raw serial data."""
        self.debugRawMsg += byte
        if len(self.debugRawMsg) == 16:
            self.context.log(self.name, self.debugRawMsg).encode("hex")
            self.debugRawMsg = ""
            
    def __del__(self):
        """ Clean up."""
        self.port.close()
                
class ReadThread(threading.Thread):
    """ Message reading thread.

    """
    def __init__(self, theName, theContext, thePool):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.readData)
        self.name = theName
        self.context = theContext
        self.pool = thePool
        self.lastDest = 0xff
        
    def readData(self):
        """ Message handling loop.
        Read messages from the interface and if they are addressed to one of the
        panels, send an Ack to the controller and process the command."""
        if self.context.debug: self.context.log(self.name, "starting read thread")
        while self.context.running:
            # read until the program state changes to not running
            if not self.context.running: break
            (dest, cmd, args) = self.pool.interface.readMsg()
            try:                         
                # handle messages that are addressed to these panels
                if not self.context.monitorMode:      
                    # send Ack if not passively monitoring
                    self.pool.interface.sendMsg((masterAddr,) + \
                                                self.pool.panels[dest].getAckMsg())
                self.pool.panels[dest].parseMsg(cmd, args)
                self.lastDest = dest
            except KeyError:                      
                # ignore other messages except...
                if (dest == masterAddr) and \
                        (self.lastDest in self.pool.panels.keys()): 
                    # parse ack messages to master that are from these panels
                    self.pool.master.parseMsg(cmd, args)
        # force all pending panel events to complete
        for panel in self.pool.panels.values():   
            for event in panel.events:
                event.set()
        if self.context.debug: self.context.log(self.name, "terminating read thread")

