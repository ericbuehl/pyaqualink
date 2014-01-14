#!/usr/bin/env python
# coding=utf-8

from aqualink.pool import *
from aqualink.serialUI import *
from BTUtils import *

########################################################################################################
# main routine
########################################################################################################

if __name__ == "__main__":
    app = BTApp("config.py", "aqualink.log", {})
    thePool = Pool("Pool", app)
    serialUI = SerialUI("SerialUI", app, thePool)

