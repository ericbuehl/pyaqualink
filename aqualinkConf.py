##################################################################
# configuration
##################################################################
logFileName = "aqualink.log"
debug = True
debugData = False
debugRaw = False
debugHttp = False

serialDevice = "/dev/ttyUSB0"       # serial device to be used
oneTouchPanelAddr = '\x41'          # address of Aqualink control panel
spaLinkPanelAddr = '\x21'           # address of Aqualink control panel
httpPort = 80                       # web server port
monitorMode = False                 # true if monitoring another panel

