#!/usr/bin/python
# coding=utf-8

import struct
import time
import threading

from debugUtils import *
from aqualinkConf import *
from aqualinkPanel import *

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
    """ 
    Aqualink SpaLink Control Panel

    The SpaLink control panel has a 3 digit 7 segment LED display,  9 buttons, and 3 LEDs.

    The buttons are:

       1-8. turn equipment on and off
       9.   cycle display (local function)

    The 7 segment display shows 3 temperatures: water, air, and spa target.  The display button cycles through
    these when pressed.  The 3 LEDs are associated with buttons 1-3.

    The device address for Aqualink serial interface is 0x20-0x22. The address is set by tying a 5th wire
    in the serial interface low (0x20), high (0x21), or open (0x22).
    
    The following basic Aqualink serial commands are supported:

    Probe
        command: 0x00
        args: none
        
    Ack
        command: 0x01
        args: 2 bytes
            byte 0: 0x00
            byte 1: button number that was pressed
                btn1 = 0x09
                btn2 = 0x06
                btn3 = 0x03
                btn4 = 0x08
                btn5 = 0x02
                btn6 = 0x07
                btn7 = 0x04
                btn8 = 0x01
            
    Status
        command: 0x02
        args: 5 bytes
            bytes 0-4:  (unknown)


    Message
        command: 0x03
        args: 17 bytes
            bytes 0-16: (unknown)
    """
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
        self.poolLightSeq = [(btn6, self.statusEvent)]
        self.spaLightSeq = [(btn7, self.statusEvent)]
        self.lightsSeq = [(btn6, self.statusEvent),
                          (btn7, self.statusEvent)]
        self.spaModeSeq = [(btn1, self.statusEvent),
                           (btn2, self.statusEvent),
                           (btn6, self.statusEvent),
                           (btn7, self.statusEvent)]
        self.blowerSeq = [(btn4, self.statusEvent)]

    def poolLight(self):
        actionThread = ActionThread("PoolLight", self.poolLightSeq, self.state, self)
        actionThread.start()

    def spaLight(self):
        actionThread = ActionThread("SpaLight", self.spaLightSeq, self.state, self)
        actionThread.start()

    def Lights(self):
        actionThread = ActionThread("Lights", self.lightsSeq, self.state, self)
        actionThread.start()

    def spaMode(self):
        actionThread = ActionThread("SpaMode", self.spaModeSeq, self.state, self)
        actionThread.start()

    def blower(self):
        actionThread = ActionThread("Blower", self.blowerSeq, self.state, self)
        actionThread.start()


