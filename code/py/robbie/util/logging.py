'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.logging module
'''

import os
import datetime

class LoggingModes(object):
    SCREEN = 'SCREEN'
    FILE   = 'FILE'

STD_TIMESTAMP_FORMAT = '%Y%m%d-%H:%M:%S'

class ScreenLogger(object):

    def __init__(self,stampFormat=STD_TIMESTAMP_FORMAT):
        self._l         = stampFormat
        self._d         = datetime.datetime

    def _timesign(self):
        return self._d.now().strftime(self._l)

    def debug(self,s,*args):
        print self._timesign(), 'DEBUG', s % args

    def error(self,s,*args):
        print self._timesign(), 'ERROR', s % args

    def info(self,s,*args):
        print self._timesign(), 'INFO ', s % args

class FileLogger(object):

    def __init__(self,path, stampFormat=STD_TIMESTAMP_FORMAT, buffering=0):
        self._l         = stampFormat
        self._d         = datetime.datetime
        self._path      = path
        self._root, _   = os.path.split(path)
        if not os.path.exists(self._root):
            os.makedirs(self._root)
        self._fd        = open(path, 'w', buffering)

    def _timesign(self):
        return self._d.now().strftime(self._l)

    def debug(self,s,*args):
        a = [ self._timesign(), 'DEBUG', s % args, '\n' ]
        s = ''.join( a )
        self._fd.write(s)

    def error(self,s,*args):
        a = [ self._timesign(), 'ERROR', s % args, '\n' ]
        s = ''.join( a )
        self._fd.write(s)

    def info(self,s,*args):
        a = [ self._timesign(), 'INFO ', s % args, '\n' ]
        s = ''.join( a )
        self._fd.write(s)

    def __del__(self):
        self._fd.close()

class Logger(object):

    def __init__(self, stampFormat=STD_TIMESTAMP_FORMAT, mode=LoggingModes.SCREEN, modeData=None):
        self._l = stampFormat
        self.setMode(mode=mode, data=modeData)

    def debug(self,s,*args):
        self._logger.debug(s,*args)

    def error(self,s,*args):
        self._logger.error(s,*args)

    def info(self,s,*args):
        self._logger.info(s,*args)

    def setMode(self, mode, data):
        self._mode      = mode
        self._modeData  = data
        if mode == LoggingModes.SCREEN:
            self._logger    = ScreenLogger(stampFormat=self._l)
        elif mode == LoggingModes.FILE:
            self._logger    = FileLogger(stampFormat=self._l, path=data)
        else:
            raise ValueError('Unknown mode=%s' % mode)

logger = Logger()
