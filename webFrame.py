#!/usr/bin/python
# coding=utf-8

import threading
import socket
import select
import time

########################################################################################################
# web server thread
########################################################################################################
class WebFrame(threading.Thread):

    # constructor
    def __init__(self, theName, theContext, theResources):
        threading.Thread.__init__(self, target=self.webServer)
        self.name = theName
        self.context = theContext
        self.resources = theResources
        self.server = socket.gethostname()

    def block(self):
        while True:
            time.sleep(1)
            
    # web server loop
    def webServer(self):
        if self.context.debug: self.context.log(self.name, "starting web thread")
        # open the socket and listen for connections
        if self.context.debugWeb: self.context.log(self.name, "opening port", self.context.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        try:
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
#        except:
#            if self.context.debug: self.context.log(self.name, "unable to open port", self.context.httpPort)
        if self.context.debug: self.context.log(self.name, "terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        request = ns.recv(8192)
        if not request: return
        if self.context.debugHttp: self.context.log(self.name, "request:\n", request, "\n")
        (self.verb, self.path, self.query, self.headers, self.body) = parseRequest(request)
        if self.context.debugHttp: self.context.log(self.name, "verb:", self.verb, "path:", self.path, "query:", self.query, "headers:", self.headers, "body:", self.body)
        params = self.query
        params.update(self.body)
        try:
            try:
                (content, contentType) = self.resources[self.path](**params)
                response = httpHeader(self.server, "200 OK", contentType=contentType) + content
            except KeyError:
                response = httpHeader(self.server, "404 Not Found")
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
        
##################################################################
# http routines
##################################################################
def parseRequest(request):
    verb = ""
    path = ""
    query = {}
    headers = {}
    body = {}
#    try:
    reqLines = request.split("\n")
    # first line
    reqItems = reqLines[0].split(" ")
    verb = reqItems[0]
    pathItems = reqItems[1].split("?")
    path = pathItems[0]
    if len(pathItems) > 1:
        query = parseUrlEnc(pathItems[1])
    # headers
    inHeaders = True
    if len(reqLines) > 1:
        for line in reqLines[1:]:
            line = line.strip("\r")
            if line != "":
                if inHeaders:
                    part = line.split(":")
                    headers[part[0]] = part[1].strip()
                else:
                    body.update(parseUrlEnc(line))
            else:
                inHeaders = False
#    except:
#        pass
    return (verb, path, query, headers, body)

def parseUrlEnc(query):
    params = {}
    queryItems = query.split("&")
    for item in queryItems:
        part = item.split("=")
        if len(part) > 1:
            params[part[0]] = part[1]
    return params

def httpHeader(server, responseCode="200 OK", contentType="text/html; charset=UTF-8", contentLength=0):
    response  = "HTTP/1.0 "+responseCode+"\n"
    response += "Server: "+server+"\n"
    response += "Connection: close\n"
    if contentLength != 0:
        response += "Content-length: "+str(contentLength)+"\n"
        response += "Content-Type: "+contentType+"\n"
    response += "\r\n"
    return response

def url(scheme="http", host="", port="", path="", query=[]):
    response = ""
    if scheme != "":
        response += scheme+"://"
    if host != "":
        response += host
        if port != "":
            response += ":"+port
        response += "/"
    if path != "":
        response += path
    if query != []:
        delimiter = "?"
        for item in query:
            response += delimiter+item[0]+"="+item[1]
            delimiter = "&"
    return response

def selfUrl(query):
    return url("", "", "", "index.php", query)

