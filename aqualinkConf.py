##################################################################
# configuration
##################################################################
logFileName = "aqualink.log"

debug = False
debugData = False
debugRaw = False
debugAck = False
debugStatus = True
debugAction = True
debugMsg = True
debugHttp = True
debugWeb = False

RS485Device = "/dev/ttyUSB0"        # RS485 serial device to be used
RS232Device = "/dev/stdin"        # RS232 serial device to be used
allButtonPanelAddr = '\x09'         # address of All Button control panel
httpPort = 80                       # web server port
monitorMode = False                 # true if monitoring another panel

