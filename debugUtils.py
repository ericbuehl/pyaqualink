import inspect
import struct
import time

from aqualinkConf import *
######################################################################################
# utility functions
######################################################################################

# print the class, object name, and arguments upon entry to a function
def debugClass(objRef, argList=[]):
    caller = inspect.stack()[1]
    print "\n" + objRef.__class__.__name__ + ":" + objRef.name + "." + caller[3] + inspect.formatargvalues(*inspect.getargvalues(caller[0]))

# print a hex value   
def printHex(bytes):
    out = ""
    for i in range(0,len(bytes)):
        out += "%02x" % struct.unpack("!B", bytes[i])
    return out

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

# logging
class LogFile:
    def __init__(self, fileName):
        if debug: print "logFile:", fileName
        self.fileName = fileName

    def log(*args):
        if logging:
            message = ""
            for arg in args:
                message += arg.__str__()+" "
            message = message.strip(" ")
            logFile = open(self.FileName, "a")
            logFile.write(timestamp()+" - "+message+"\n")
            logFile.close()

def log(*args):
    if logFileName != "":
        message = "%-16s: "%args[0]
        for arg in args[1:]:
            message += arg.__str__()+" "
#        message = message.strip(" ")
        logFile = open(logFileName, "a")
        logFile.write(timestamp()+" - "+message+"\n")
        logFile.close()
                
