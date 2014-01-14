pyaqualink
==========

Jan 14 2014

This project implements the Aqualink pool controller interface in Python 2.  It was developed
on a Raspberry Pi under Arch Linux.

Dependencies
------------

1. pySerial

    Available from http://pyserial.sourceforge.net/

    To install on Arch:
```    
    # wget https://pypi.python.org/packages/source/p/pip/pip-1.3.1.tar.gz
    # tar -xvf pip-1.3.1.tar.gz
    # cd pip-1.3.1
    # python setup.py install
    # cd ..
    # pip install pyserial
```
2. an RS-485 serial interface

Running
-------

You can edit config.py to specify your environment.  Messages are written to the log file 
aqualink.log.  The debug variables control how much is written.

There are two programs included:

### aqualinkRS.py

This emulates the Aqualink RS serial adapter.  This allows you to send commands to the
Aqualink controller from a serial RS-232 interface in human readable form.  The commands are
documented here http://kb.homeauto.com/redirfile.asp?id=203

The program will accept commands from a specified serial port, or stdin.

Most commands are implemented, except for:

* CLEANR
* SPA
* SPAHT

Aux dimmer control is not implemented.

There are a few extra commands added that simulate the navigation buttons on the AllButton panel:

* MENU
* LEFT
* RIGHT
* CANCEL
* ENTER

An EXIT command ends the program.

### aquaserver.py

Don't run this.  It's broken.
