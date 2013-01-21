##################################################################
# configuration
##################################################################
logging = True
logFileName = "aqualink.log"
debug = True
debugData = False
debugHttp = False

serialDevice = "/dev/ttyUSB0"   # serial device to be used
masterAddress = '\x00'          # address of Aqualink controller
panelAddress = '\x41'           # address of Aqualink control panel
httpPort = 80                   # web server port
monitorMode = False              # true if monitoring another panel

