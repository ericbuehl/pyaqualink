#!/usr/bin/env python
# coding=utf-8

import sys
import time

from aqualink.pool import *
from aqualink.web import *
from aqualink.serial import *
import config

########################################################################################################
# main routine
########################################################################################################

class M(object):
    """ mock object """
    def __init__(self, d):
        self.d = d
    def __getattribute__(self, k):
        return object.__getattribute__(self, "d")[k]

if __name__ == "__main__":
    thePool = M({"airTemp": 70,
                 "poolTemp": 60,
                 "spaTemp": 80,
                 "title": "Mock Pool",
                 "spa": M({
                     "state": "ON",
                     }),
                 "heater": M({
                     "state": "ON",
                     }),
                 "aux4": M({
                     "state": False,
                     }),
                 "aux5": M({
                     "state": False,
                     }),
                 })
    #thePool = Pool("Pool", config)
    #serialUI = SerialUI("SerialUI", config, thePool)
    webUI = WebUI("WebUI", config, thePool)
    webUI.block()

