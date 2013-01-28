#!/usr/bin/python
# coding=utf-8

import threading
import socket
import select

from debugUtils import *
from webUtils import *
from aqualinkConf import *

########################################################################################################
# web UI
########################################################################################################
class WebUI:
    # constructor
    def __init__(self, theName, theState, thePool):
        self.name = theName
        self.state = theState
        self.pool = thePool
        webThread = WebThread("Web", theState, httpPort, thePool)
        webThread.start()

########################################################################################################
# web server thread
########################################################################################################
class WebThread(threading.Thread):

    # constructor
    def __init__(self, theName, state, httpPort, thePool):
        threading.Thread.__init__(self, target=self.webServer)
        self.name = theName
        self.state = state
        self.httpPort = httpPort
        self.pool = thePool
        self.server = "aqualink"

        self.verbTable = {"GET": WebThread.handleGet,
                         "POST": WebThread.handlePost,
                         "PUT": WebThread.handlePut,
                         "DELETE": WebThread.handleDelete,
                         "HEAD": WebThread.handleHead}
    
    # web server loop
    def webServer(self):
        if debug: log(self.name, "starting web thread")
        # open the socket and listen for connections
        if debugWeb: log(self.name, "opening port", self.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(("", self.httpPort))
            if debugWeb: log(self.name, "waiting for connections")
            log(self.name, "ready")
            self.socket.listen(5)
            # handle connections
            try:
                while self.state.running:
                    inputs, outputs, excepts = select.select([self.socket], [], [], 1)
                    if self.socket in inputs:
                        (ns, addr) = self.socket.accept()
                        name = addr[0]+":"+str(addr[1])+" -"
                        if debugWeb: log(self.name, name, "connected")
                        self.handleRequest(ns, addr)
            finally:
                self.socket.close()
        except:
            if debug: log(self.name, "unable to open port", httpPort)
        if debug: log(self.name, "terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        # got a request, parse it
        request = ns.recv(8192)
        if not request: return
        if debugHttp: log(self.name, "request:\n", request)
        (verb, path, params) = parseRequest(request)
        if debugHttp: log(self.name, "parsed verb:", verb, "path:", path, "params:", params)
        try:
            if verb == "GET":
                if path == "/":
                    html  = htmlDocument(displayPage([[self.pool.printState("<br>")]]), 
                                          [self.server], 
                                          refreshScript(10))
                    response = httpHeader(self.server, len(html)) + html
                else:
                    if path == "/cleanon":
                        self.pool.cleanMode.changeState(True)
                        response = httpHeader(self.server)
                    elif path == "/cleanoff":
                        self.pool.cleanMode.changeState(False)
                        response = httpHeader(self.server)
                    elif path == "/spaon":
                        self.pool.spaMode.changeState(True)
                        response = httpHeader(self.server)
                    elif path == "/spaoff":
                        self.pool.spaMode.changeState(False)
                        response = httpHeader(self.server)
                    elif path == "/lightson":
                        self.pool.lightsMode.changeState(True)
                        response = httpHeader(self.server)
                    elif path == "/lightsoff":
                        self.pool.lightsMode.changeState(False)
                        response = httpHeader(self.server)
                    elif path == "/spatemp":
                        html  = htmlHeader([self.server], refreshScript(10))
                        html += "<body bgcolor=#424242>"
                        spaState = self.pool.spa.printState()
                        heaterState = self.pool.heater.printState()
                        if spaState == "ON":
                            temp = "%3d"%self.pool.spaTemp                      
                            if heaterState == "ON":
                                color = "red"
                            else:
                                color = "green"
                        else:
                            temp = "OFF"
                            color = "white"
                        html += "<font size='512' face='Helvetica' color='"+color+"'>"
                        html += "<bold>"+temp+"</bold>"
                        html += "</font>"
                        html += "</body>"
                        html += htmlTrailer()
                        response = httpHeader(self.server, len(html)) + html
                    else:
                        response = httpHeader(self.server, "404 Not Found")                    
                ns.sendall(response)
        finally:
            ns.close()
            if debugWeb: log(self.name, "disconnected")

    def handleGet(self, path, params, body):
        response = httpHeader(self.server, "501 Not mplemented")
        return response

    def handlePost(self, path, params, body):
        response = httpHeader(self.server, "501 Not mplemented")
        return response

    def handlePut(self, path, params, body):
        response = httpHeader(self.server, "501 Not mplemented")
        return response

    def handleDelete(self, path, params, body):
        response = httpHeader(self.server, "501 Not mplemented")
        return response

    def handleHead(self, path, params, body):
        response = httpHeader(self.server, "501 Not mplemented")
        return response

