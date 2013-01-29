##################################################################
# configuration
##################################################################
logFileName = "aqualink.log"

debug = False
debugData = False
debugRaw = False
debugAck = False
debugStatus = False
debugAction = True
debugMsg = False
debugHttp = True
debugWeb = False

RS485Device = "/dev/ttyUSB0"        # RS485 serial device to be used
RS232Device = "/dev/ttyUSB1"        # RS232 serial device to be used
oneTouchPanelAddr = '\x41'          # address of One Touch control panel
spaLinkPanelAddr = '\x21'           # address of SpaLink control panel
allButtonPanelAddr = '\x09'         # address of All Button control panel
httpPort = 80                       # web server port
monitorMode = False                 # true if monitoring another panel

