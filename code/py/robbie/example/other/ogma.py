'''
DESCRIPTION: write-only/read-only database
'''

import os
import cPickle as pickle
from   robbie.util.logging import logger

class OgmaOptions(object):
    FLUSH_EVERY_OBJECT  = 'FLUSH_EVERY_OBJECT'
    FLUSH_SESSION       = 'FLUSH_SESSION'

# local obj
FLUSH_EVERY_OBJECT  = OgmaOptions.FLUSH_EVERY_OBJECT
FLUSH_SESSION       = OgmaOptions.FLUSH_SESSION

class OgmaValues(object):
    DATA_NOMORE = 'DATA_NOMORE'

class Ogma(object):
    '''
    Ogma - Irish diety of wisdom (more or less)
    '''
    def __init__(self, dirName, coreName, mode='write', options=('FLUSH_EVERY_OBJECT',), buffering=100*1024):
        self._dirName   = dirName
        self._coreName  = coreName
        self._mode      = mode
        self._options   = set( options )
        self._buffering = buffering

        self._init()
        self._initVals()

    def _initVals(self):
        self._dataOffset = 0
        self._dataLen    = 0

    def _prepareVals(self, obj):
        s = pickle.dumps( obj )
        self._dataLen     = len(s)
        return s, (self._dataOffset, self._dataLen)

    def _adjustOffset(self):
        self._dataOffset += self._dataLen

    def _init(self):
        if self._coreName is None:
            raise ValueError('Not implemented coreName acquisition API yet')

        if not os.path.exists( self._dirName ):
            logger.debug('ogma: creating dir=%s', self._dirName)
            os.makedirs(self._dirName)

        self._valpath = os.path.join ( self._dirName, '%s.ogmv' % self._coreName )
        self._indexpath = os.path.join ( self._dirName, '%s.ogmx' % self._coreName )

        if self._mode == 'write':
            self._valfd = open( self._valpath, 'w', self._buffering)
            self._indexfd = open( self._indexpath, 'w')
        elif self._mode == 'read':
            self._valfd = open( self._valpath, 'r')
            self._indexfd = open( self._indexpath, 'r')
        else:
            raise ValueError('mode=%s is not implemented yet' % self._mode )

    def read(self, options=None):
        t = self._indexfd.readline()
        if not t:
            return False, OgmaValues.DATA_NOMORE

        dataOffset, dataLen = t.split(',')
        dataOffset, dataLen = int(dataOffset), int(dataLen)

        s = self._valfd.read(dataLen)
        return True, pickle.loads(s)

    def write(self, obj, options=None):
        bin, (dataOffset, dataLen) = self._prepareVals(obj)

        self._valfd.write(bin)
        self._indexfd.write('%d,%d\n' % (dataOffset, dataLen))
        self._finishWrite()

        self._adjustOffset()

    def _close(self):
        self._valfd.close()
        self._indexfd.close()

    def __del__(self):
        return self._close()

    def flush(self):
        self._valfd.flush()
        self._indexfd.flush()

    def close(self):
        return self._close()

    def _finishWrite(self):
        if FLUSH_EVERY_OBJECT in self._options:
            self.flush()
