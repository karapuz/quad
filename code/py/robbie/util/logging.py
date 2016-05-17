'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.logging module
'''

import datetime

STD_TIMESTAMP_FORMAT = '%Y%m%d-%H:%M:%S'
class Logger(object):

    def __init__(self,l=STD_TIMESTAMP_FORMAT):
        self._l = l
        self._d = datetime.datetime

    def _timesign(self):
        return self._d.now().strftime(self._l)

    def debug(self,s,*args):
        print self._timesign(), 'DEBUG', s % args

    def error(self,s,*args):
        print self._timesign(), 'ERROR', s % args

logger = Logger()
