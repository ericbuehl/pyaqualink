#!/usr/bin/python
# coding=utf-8

import sys, time, threading, socket, select

from debugUtils import *
from webUtils import *
from aqualinkConf import *

########################################################################################################
# web server thread
########################################################################################################
class WebThread(threading.Thread):
    # constructor
    def __init__(self, state, httpPort, thePool):
        threading.Thread.__init__(self, target=self.webServer)
        self.state = state
        self.httpPort = httpPort
        self.pool = thePool

    # web server loop
    def webServer(self):
        if debug: log("starting web thread")
        # open the socket and listen for connections
        if debug: log("opening port", self.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        try:
        self.socket.bind(("", self.httpPort))
        if debug: log("waiting for connections")
        self.socket.listen(5)
        # handle connections
        try:
            while self.state.running:
                inputs, outputs, excepts = select.select([self.socket], [], [], 1)
                if self.socket in inputs:
                    (ns, addr) = self.socket.accept()
                    name = addr[0]+":"+str(addr[1])+" -"
                    if debug: log(name, "connected")
                    self.handleRequest(ns, addr)
        finally:
            self.socket.close()
#        except:
#            if debug: log("unable to open port", httpPort)
        if debug: log("terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        # got a request, parse it
        request = ns.recv(8192)
        if not request: return
        if debugHttp: log("request:\n", request)
        (verb, path, params) = parseRequest(request)
        if debugHttp: log("parsed verb:", verb, "path:", path, "params:", params)
        try:
            if verb == "GET":
                if path == "/":
                    html  = htmlDocument(displayPage([[self.pool.printState("<br>")]]), 
                                          [self.pool.title], 
                                          refreshScript(10))
                    response = httpHeader(self.pool.title, len(html)) + html
                else:
                    if path == "/spaon":
                        self.pool.spaOn()
                        response = httpHeader(self.pool.title)
                    elif path == "/spaoff":
                        self.pool.spaOff()
                        response = httpHeader(self.pool.title)
#                    elif path == "/main":
#                        actionThread = ActionThread("Main", self.panel.main, self.state, self.panel)
#                        actionThread.start()
#                        response = httpHeader(self.pool.title)
#                    elif path == "/back":
#                        actionThread = ActionThread("Back", self.panel.back, self.state, self.panel)
#                        actionThread.start()
#                        response = httpHeader(self.pool.title)
                    else:
                        response = httpHeader(self.pool.title, "404 Not Found")                    
                ns.sendall(response)
        finally:
            ns.close()
            if debug: log("disconnected")


