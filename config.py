##################################################################
# configuration
##################################################################
logFileName = "aqualink.log"

debug = True                        # general debug messages
debugData = False                   # show parsed aqualink messages
debugRaw = False                    # show all raw RS485 data
debugAck = True                     # show ack messages
debugStatus = True                  # show status messages received from controller
debugAction = True                  # show action messages sent to to controller
debugMsg = False                    # show text messages received from controller
debugHttp = False
debugWeb = False

RS485Device = "/dev/ttyUSB0"        # RS485 serial device to be used
RS232Device = "/dev/stdin"          # RS232 serial device to be used
allButtonPanelAddr = '\x09'         # address of All Button control panel
httpPort = 80                       # web server port
monitorMode = False                 # true if monitoring another panel

