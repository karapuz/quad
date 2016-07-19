'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.pricestrip module
DESCRIPTION : this module contains price strip object definition
'''

import numpy
import threading
import robbie.tweak.value as twkval
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.util.mmap_array as mmap_array

MAXNUM      = 1000000
POS_MAXNUM  = 0

center = [ 'TRADE', 'ASK', 'BID', 'SYMBOL', 'CUM_TRADE', 'TRADE_QUOTE_COUNT', 'LAST_EVENT_TIME' ]

class PriceStrip( object ):
    '''
        PriceStrip tracks prices
        MargotRoot   = /margot/ivp
        Domain       = echo         # pretty much a constant. Other domains: risk management?
        Session      = 20160504     # tied to a day
        Activity     = mirror       # is related to echo; mirror, trade, market
    '''
    def __init__(self, readOnly, symbols, debug=True ):
        ''' the constructor '''
        return self.init( readOnly=readOnly, symbols=symbols, debug=debug )

    def init( self, readOnly, symbols, debug ):
        '''
            realized
            pending_long
            pending_short
            rejected
            canceled
        '''
        self._nextNum   = 0
        self._tag2ix    = {}
        self._ix2tag    = {}
        self._symbols   = symbols

        turf            = twkval.getenv('run_turf')
        domain          = twkval.getenv('run_domain')
        session         = twkval.getenv('run_session')
        user            = twkval.getenv('env_userName')
        shape           = ( len(symbols), )
        symIds          = symboldb.symbol2id(self._symbols)
        if readOnly:
            mmapFunc    = mmap_array.newRead
        else:
            mmapFunc    = mmap_array.zeros

        vars = dict( domain=domain, user=user, session=session, shape=shape )
        self._strip = {}

        for c in center:
            for i in xrange(3):
                activity = '%s-%d.mmap' % (c,i)
                self._strip[ activity ] = mmapFunc( activity=activity, **vars )
                # logger.debug('pricestrip: init activity=%s', activity)

        self._support = mmapFunc( activity='orderstate-support', **vars )
        self._symids  = mmapFunc( activity='symids', **vars )

        if symIds != None and not readOnly:
            self._symids[ :len( symIds ) ] = symIds

        self._lastError     = None
        self._addTagLock    = threading.Lock()
        self.addTags( symbols, readOnly=readOnly )

    def getInstantPriceByName(self, priceType, symbol, val=None ):
        ''' get a slice of all data for the type '''
        instant  = 1
        activity = '%s-%d.mmap' % (priceType, instant)
        arr      = self._strip[ activity ]
        ix       = self.getIxByTag( symbol )
        if val is not None:
            arr[ ix ] = val
        return arr[ ix ]

    # def asTable(self, header=None):
    #     mat = []
    #     if header:
    #         mat.append(header)
    #
    #     nextNum = self._support[ POS_MAXNUM ]
    #     for k,v in self._state.iteritems():
    #         row = [ k ]
    #         row.extend( v[ : nextNum ].tolist() )
    #         mat.append( row )
    #     return mat
    #
    # def dump(self, fd, frmt='multiLine' ):
    #     nextNum = self._support[ POS_MAXNUM ]
    #
    #     if frmt == 'multiLine':
    #         fd.write( frmt + ':\n' )
    #         for k,v in self._state.iteritems():
    #             fd.write( str( k ) + ':\n' )
    #             fd.write( ','.join( v[ : nextNum ].tolist() ) + '\n' )
    #         fd.write( 'tag2ix' + ':\n' )
    #         fd.write( str( self._tag2ix ) + '\n' )
    #     else:
    #         raise ValueError( 'Unknown frmt=%s' % str( frmt ) )
        
    def addError(self, status, data, msg):
        self._lastError     = ( status, data, msg )
    
    def clearError(self):
        self._lastError = None

    def getLastError(self):
        return self._lastError

    def checkExistTag( self, tag ):
        return tag in self._tag2ix

    def _addTag( self, tag, readOnly=False ):
        if tag in self._tag2ix:
            return self._tag2ix[ tag ]
        c = self._nextNum
        self._tag2ix[ tag ] = c
        self._ix2tag[ c   ] = tag
        self._nextNum += 1
        if not readOnly:
            self._support[ POS_MAXNUM ] = self._nextNum
        return c

    def addTag( self, tag, readOnly=False ):
        return self._addTag( tag, readOnly=readOnly )

    def addTags( self, tag, readOnly=False, asDict=False ):
        if asDict:
            return dict( ( t , self._addTag( t, readOnly=readOnly ) ) for t in tag )
        else:
            return [ self._addTag( t, readOnly=readOnly ) for t in tag ]

    def getTagByIx(self, ix):
        if isinstance( ix, ( numpy.ndarray, tuple, list ) ):
            return [ self._ix2tag[ t ] for t in ix ]
        else:
            return self._ix2tag[ ix ]

    def getIxByTag(self, tag):
        if isinstance( tag, ( numpy.ndarray, tuple, list ) ):
            return [ self._tag2ix[ t ] for t in tag ]
        else:
            return self._tag2ix[ tag ]
