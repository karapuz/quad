'''
DESCRIPTION: write-only/read-only database
'''

import os
import getpass
import datetime
import cPickle as pickle
from   robbie.util.logging import logger

class OgmaOptions(object):
    FLUSH_EVERY_OBJECT  = 'FLUSH_EVERY_OBJECT'
    FLUSH_SESSION       = 'FLUSH_SESSION'
    ZIP_NOTHING         = 'ZIP_NOTHING'
    # HEADER_PRESENT      = 'HEADER_PRESENT'

# local obj
FLUSH_EVERY_OBJECT  = OgmaOptions.FLUSH_EVERY_OBJECT
FLUSH_SESSION       = OgmaOptions.FLUSH_SESSION

# zip options
ZIP_NOTHING         = OgmaOptions.ZIP_NOTHING

# header and versions
# HEADER_PRESENT      = OgmaOptions.HEADER_PRESENT

class OgmaValues(object):
    DATA_NOMORE = 'DATA_NOMORE'

_options = ( FLUSH_EVERY_OBJECT, ZIP_NOTHING )

class Ogma(object):
    '''
    Ogma - Irish diety of wisdom (more or less)
    '''
    def __init__(self, dirName, coreName, mode='write', options=_options, buffering=100*1024):
        self._dirName   = dirName
        self._coreName  = coreName
        self._mode      = mode
        self._options   = set( options )
        self._buffering = buffering

        logger.debug('ogma: dirName=%s, coreName=%s, mode=%s', self._dirName, self._coreName, self._mode)
        self._initVals()
        self._init()

    def _whenCreated(self):
        return datetime.datetime.strftime( datetime.datetime.now(), '%Y%m%d-%H%M' )

    def _whoCreated(self):
        return getpass.getuser()

    def _initVals(self):
        self._type       = 'OGMA'
        self._version    =  'V0.1'
        self._dataOffset = 0
        self._dataLen    = 0
        self._flush      = ( FLUSH_EVERY_OBJECT in self._options )

    def _prepareVals(self, obj):
        s = pickle.dumps( obj )
        self._dataLen = len(s)
        return s, self._dataLen

    def _init(self):
        if self._coreName is None:
            raise ValueError('Not implemented coreName acquisition API yet')

        if not os.path.exists( self._dirName ):
            logger.debug('ogma: creating dir=%s', self._dirName)
            os.makedirs(self._dirName)

        self._valpath   = os.path.join ( self._dirName, '%s.ogmv' % self._coreName )
        self._indexpath = os.path.join ( self._dirName, '%s.ogmx' % self._coreName )

        if self._mode == 'write':
            self._valfd     = open( self._valpath, 'w', self._buffering)
            self._indexfd   = open( self._indexpath, 'w', self._buffering)
            self._writeHeader()

        elif self._mode == 'append':
            self._valfd     = open( self._valpath, 'a', self._buffering)
            self._indexfd   = open( self._indexpath, 'a', self._buffering)

            if not os.path.exists( self._valpath ):
                self._writeHeader()

        elif self._mode == 'read':
            self._valfd     = open( self._valpath, 'r', self._buffering)
            self._indexfd   = open( self._indexpath, 'r', self._buffering)
            self._readHeader()

        else:
            raise ValueError('mode=%s is not implemented yet' % self._mode )

    def _readHeader(self):
        header = {}
        for fd in ( self._valfd, self._indexfd ):
            header['type']    = fd.readline()
            header['version'] = fd.readline()
            header['options'] = fd.readline()
            header['whenWho'] = fd.readline()
        logger.debug('ogma: header=%s', str(header))
        return header

    def _writeHeader(self):
        for fd in ( self._valfd, self._indexfd ):
            fd.write('TYPE: %s\n' % self._type)
            fd.write('VERSION: %s\n' % self._version )
            fd.write('OPTIONS: %s\n' % ','.join( self._options ) )
            fd.write('CREATED: %s,%s\n' % ( self._whenCreated(), self._whoCreated() ) )
            fd.flush()

    def read(self, options=None):
        t = self._indexfd.readline()
        if not t:
            return False, OgmaValues.DATA_NOMORE
        dataLen = int(t)
        s = self._valfd.read(dataLen)
        return True, pickle.loads(s)

    # def readmany(self, n, options=None):
    #     offset  = 0
    #     offsets = []
    #     for _ in xrange(n):
    #         t = self._indexfd.readline()
    #         if not t:
    #             break
    #
    #         dataLen = int(t)
    #         offset += dataLen
    #         offsets.append( dataLen )
    #
    #     if not offset:
    #         return False, []
    #
    #     s    = self._valfd.read(offset)
    #     objs    = []
    #     offset  = 0
    #     for dataLen in offsets:
    #         s0    = s[offset:offset+dataLen]
    #         objs += pickle.loads(s0)
    #         offset += dataLen
    #     return True, objs

    def write(self, obj, options=None):
        bin, dataLen = self._prepareVals(obj)
        self._valfd.write(bin)
        self._indexfd.write('%d\n' % dataLen)
        self._finishWrite()

    def _close(self):
        self._valfd.close()
        self._indexfd.close()

    def __del__(self):
        return self._close()

    def flush(self):
        self._valfd.flush()
        self._indexfd.flush()

    def reset(self):
        return self._init()

    def close(self):
        return self._close()

    def _finishWrite(self):
        if self._flush:
            self.flush()

    ### iterator
    def __iter__(self):
        return self

    def next(self):
        cont, val = self.read()
        if not cont:
            raise StopIteration('No More Elements')
        return val

