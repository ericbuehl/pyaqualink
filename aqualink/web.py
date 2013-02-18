#!/usr/bin/env python
# coding=utf-8

import os
import cherrypy
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class WebUI(object):
    # constructor
    def __init__(self, theName, theContext, thePool):
        self.name = theName
        self.context = theContext
        self.pool = thePool

        globalConfig = {
            'server.socket_port': 8080,
            'server.socket_host': "0.0.0.0",
            }
        appConfig = {
            '/css': {
                'tools.staticdir.on': True,
                'tools.staticdir.root': os.path.join(BASE_DIR, "../static"),
                'tools.staticdir.dir': "css",
            },
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': os.path.join(BASE_DIR, "../static/favicon.ico"),
            },
        }    
        cherrypy.config.update(globalConfig)
        root = WebRoot(self.name, self.context, self.pool)
        cherrypy.tree.mount(root, "/", appConfig)

    def block(self):
        cherrypy.engine.start()
        cherrypy.engine.block()

class WebRoot(object):
    def __init__(self, theName, theContext, thePool):
        self.name = theName
        self.context = theContext
        self.pool = thePool
        self.env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, '../templates')))

        # mode dispatch table
        self.modeTable = {"Lights": WebRoot.lightsMode,
                          "Spa": WebRoot.spaMode,
                          "Clean": WebRoot.cleanMode,
                          }    

    @cherrypy.expose
    def statusPage(self):
        return self.pool.printState(), 

    @cherrypy.expose
    def pool(self, mode=None):
        if mode != None:
            self.modeTable[mode](self)
        t = self.env.get_template("index.html")
        return t.render(pool=self.pool)

    index = pool

    def lightsMode(self):
        self.pool.lightsMode.changeState()

    def spaMode(self):
        self.pool.spaMode.changeState()

    def cleanMode(self):
        self.pool.cleanMode.changeState()
        
