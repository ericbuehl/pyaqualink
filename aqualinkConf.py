##################################################################
# configuration
##################################################################
logFileName = "aqualink.log"
debug = True
debugData = False
debugHttp = False

serialDevice = "/dev/ttyUSB0"   # serial device to be used
masterAddr = '\x00'          # address of Aqualink controller
panelAddr = '\x41'           # address of Aqualink control panel
httpPort = 80                   # web server port
monitorMode = False              # true if monitoring another panel

