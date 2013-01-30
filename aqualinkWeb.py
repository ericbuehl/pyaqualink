#!/usr/bin/python
# coding=utf-8

import threading
import socket
import select

from webUtils import *

########################################################################################################
# web UI
########################################################################################################
class WebUI:
    # constructor
    def __init__(self, theName, theContext, thePool):
        self.name = theName
        self.context = theContext
        self.pool = thePool
        webThread = WebThread("Web", self.context, thePool)
        webThread.start()

########################################################################################################
# web server thread
########################################################################################################
class WebThread(threading.Thread):

    # constructor
    def __init__(self, theName, theContext, thePool):
        threading.Thread.__init__(self, target=self.webServer)
        self.name = theName
        self.context = theContext
        self.pool = thePool
        self.server = "aqualink"

        # http verb dispatch table
        self.verbTable = {"GET": WebThread.handleGet,
                         "POST": WebThread.handlePost,
                         "PUT": WebThread.handlePut,
                         "DELETE": WebThread.handleDelete,
                         "HEAD": WebThread.handleHead}

        # web page dispatch table
        self.pageTable = {"/": WebThread.statusPage,
                          "/favicon.ico": WebThread.faviconPage,
                          "/css/phone.css": WebThread.cssPage,
                          "/spatemp": WebThread.spatempPage,
                          }    
    # web server loop
    def webServer(self):
        if self.context.debug: self.context.log(self.name, "starting web thread")
        # open the socket and listen for connections
        if self.context.debugWeb: self.context.log(self.name, "opening port", self.context.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(("", self.context.httpPort))
            if self.context.debugWeb: self.context.log(self.name, "waiting for connections")
            self.context.log(self.name, "ready")
            self.socket.listen(5)
            # handle connections
            try:
                while self.context.running:
                    inputs, outputs, excepts = select.select([self.socket], [], [], 1)
                    if self.socket in inputs:
                        (ns, addr) = self.socket.accept()
                        name = addr[0]+":"+str(addr[1])+" -"
                        if self.context.debugWeb: self.context.log(self.name, name, "connected")
                        self.handleRequest(ns, addr)
            finally:
                self.socket.close()
        except:
            if self.context.debug: self.context.log(self.name, "unable to open port", self.context.httpPort)
        if self.context.debug: self.context.log(self.name, "terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        request = ns.recv(8192)
        if not request: return
        if self.context.debugHttp: self.context.log(self.name, "request:\n", request, "\n")
        (verb, path, params) = parseRequest(request)
        if self.context.debugHttp: self.context.log(self.name, "verb:", verb, "path:", path, "params:", params)
        try:
            try:
                response = self.verbTable[verb](self, path, params)
            except KeyError:
                response = httpHeader(self.server, "400 Bad Request")
            except:
                response = httpHeader(self.server, "500 Internal Server Error")
            if self.context.debugHttp: self.context.log(self.name, "response:\n", self.printHeaders(response), "\n")
            ns.sendall(response)
        finally:
            ns.close()
            if self.context.debugWeb: self.context.log(self.name, "disconnected")

    def printHeaders(self, msg):
        hdrs = ""
        lines = msg.split("\n")
        for line in lines:
            if line == "\r": break
            hdrs += line+"\n"
        return hdrs
        
    def handleGet(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "handleGet")
        try:
            response = self.pageTable[path](self, path, params)
        except KeyError:
            response = httpHeader(self.server, "404 Not Found")                    
        except:
            response = httpHeader(self.server, "500 Internal Server Error")
        return response

    def handlePost(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "handlePost")
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
        return response

    def handlePut(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "handlePut")
        response = httpHeader(self.server, "501 Not Implemented")
        return response

    def handleDelete(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "handleDelete")
        response = httpHeader(self.server, "501 Not Implemented")
        return response

    def handleHead(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "handleHead")
        response = httpHeader(self.server, "501 Not Implemented")
        return response

    def statusPage(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "statusPage")
        html  = htmlHeader([self.pool.title], css="/css/phone.css") #refreshScript(10))
        html += "<body><p>\n"
        html += self.pool.printState(end="<br>\n") 
        html += "</p></body>"
        html += htmlTrailer()
        response = httpHeader(self.server, contentLength=len(html)) + html
        return response

    def readFile(self, path):
        path = path.lstrip("/")
        if self.context.debugHttp: self.context.log(self.name, "reading", path)
        f = open(path)
        body = f.read()
        f.close()
        return body
    
    def faviconPage(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "faviconPage")
        body = self.readFile(path)
        response = httpHeader(self.server, contentType="image/x-icon", contentLength=len(body)) + body
        return response

    def cssPage(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "cssPage")
        body = self.readFile(path)
        response = httpHeader(self.server, contentLength=len(body)) + body
        return response

    def spatempPage(self, path, params):
        if self.context.debugHttp: self.context.log(self.name, "spatempPage")
        html  = htmlHeader([self.pool.title], css="/css/phone.css") #refreshScript(10))
        html += "<body>"
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
        html += "<div class='temp-"+color+"'>"+temp+"</div>"
        html += "</body>"
        html += htmlTrailer()
        response = httpHeader(self.server, contentLength=len(html)) + html
        return response

