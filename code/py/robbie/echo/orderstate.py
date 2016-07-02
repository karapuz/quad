'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.orderstate module
DESCRIPTION : this module contains order state objects
'''
import os
import numpy
import threading
import robbie.tweak.value as twkval
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.util.mmap_array as mmap_array

MAXNUM      = 1000000
POS_MAXNUM  = 0

class OrderState( object ):
    '''
        OrderState tracks status of related orders/exposure objects
        MargotRoot   = /margot/ivp
        Domain       = echo         # pretty much a constant. Other domains: risk management?
        Session      = 20160504     # tied to a day
        Activity     = mirror       # is related to echo; mirror, trade, market
    '''
    def __init__(self, readOnly, maxNum, symbols, debug=True ):
        ''' the constructor '''
        return self.init( readOnly=readOnly, maxNum=maxNum, symbols=symbols, debug=debug )

    def init( self, readOnly, maxNum, symbols, debug ):
        '''
            realized
            pending_long
            pending_short
            rejected
            canceled
        '''
        self._maxNum    = maxNum
        self._nextNum   = 0
        self._tag2ix    = {}
        self._ix2tag    = {}
        self._symbols   = symbols

        turf            = twkval.getenv('run_turf')
        domain          = twkval.getenv('run_domain')
        session         = twkval.getenv('run_session')
        user            = twkval.getenv('env_userName')
        shape           = ( self._maxNum, )
        symIds          = symboldb.symbol2id(self._symbols)
        if readOnly:
            mmapFunc    = mmap_array.newRead
        else:
            mmapFunc    = mmap_array.zeros

        vars = dict( domain=domain, user=user, session=session, shape=shape )
        self._support       = mmapFunc( activity='orderstate-support',      **vars )
        self._realized      = mmapFunc( activity='orderstate-realized',     **vars )
        self._pending_long  = mmapFunc( activity='orderstate-pndng_l',      **vars )
        self._pending_short = mmapFunc( activity='orderstate-pndng_s',      **vars )
        self._canceled      = mmapFunc( activity='orderstate-canceled',     **vars )
        self._symids        = mmapFunc( activity='orderstate-symids',       **vars )
        # self._rejected    = mmapFunc( activity='orderstate-rejected',     **vars )

        if symIds != None and not readOnly:
            self._symids[ :len( symIds ) ] = symIds

        self._state         = { 
            'realized'      : self._realized,
            'pending_long'  : self._pending_long,
            'pending_short' : self._pending_short,
            'canceled'      : self._canceled,
            # 'rejected'      : self._rejected,
        }
    
        self._lastError     = None
        self._addTagLock    = threading.Lock()
        self._pending_Lock  = threading.Lock()
        self.addTags( symbols )

    def getFullByType(self, posType, maxLen ):
        ''' get a slice of all data for the type '''
        if posType == 'pending':
            return self._state[ 'pending_long' ][: maxLen] + self._state[ 'pending_short' ][: maxLen]
        else:
            return self._state[ posType ][: maxLen]

    def asTable(self, header=None):
        mat = []
        if header:
            mat.append(header)

        nextNum = self._support[ POS_MAXNUM ]
        for k,v in self._state.iteritems():
            row = [ k ]
            row.extend( v[ : nextNum ].tolist() )
            mat.append( row )
        return mat

    def dump(self, fd, frmt='multiLine' ):
        nextNum = self._support[ POS_MAXNUM ]

        if frmt == 'multiLine':
            fd.write( frmt + ':\n' )
            for k,v in self._state.iteritems():
                fd.write( str( k ) + ':\n' )
                fd.write( ','.join( v[ : nextNum ].tolist() ) + '\n' )
            fd.write( 'tag2ix' + ':\n' )
            fd.write( str( self._tag2ix ) + '\n' )
        else:
            raise ValueError( 'Unknown frmt=%s' % str( frmt ) )
        
    def addError(self, status, data, msg):
        self._lastError     = ( status, data, msg )
    
    def clearError(self):
        self._lastError = None

    def getLastError(self):
        return self._lastError

    def checkExistTag( self, tag ):
        return tag in self._tag2ix

    def _addTag( self, tag ):        
        #with self._addTagLock:
        if tag in self._tag2ix:
            return self._tag2ix[ tag ]
        c = self._nextNum
        self._tag2ix[ tag ] = c
        self._ix2tag[ c   ] = tag
        self._nextNum += 1
        self._support[ POS_MAXNUM ] = self._nextNum
        return c

    def addTag( self, tag ):
        return self._addTag( tag )

    def addTags( self, tag, asDict=False ):
        if asDict:
            return dict( ( t , self._addTag( t ) ) for t in tag )
        else:
            return [ self._addTag( t ) for t in tag ]

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

    def getPosStateByIx(self, ix, typ='dict' ):
        if typ == 'dict':
            return { 
                'realized' : self._realized[ix],
                'pending'  : self.pending_long[ix] + self.pending_short[ix],
            }
        else:
            return self._realized[ix], self.pending_long[ix] + self.pending_short[ix]

    def getPosStateByTag(self, tag, asDict=False ):
        return self.getPosStateByIx(ix=self.getIxByTag(tag), asDict=asDict )

    def getStateByIx(self, name, ix ):
        if name == 'pending':
            return self._state[ 'pending_long' ][ ix ] + self._state[ 'pending_short' ][ ix ]
        else:
            return self._state[ name ][ ix ]

    def getPendingByIx(self, ix ):
        '''
        return signed pending amount 
        '''
        return self._pending_long[ ix ] + self._pending_short[ ix ]

    def getCurrentState(self, where='all', which='pending', how='pandas'):
        '''
        return signed pending amount
        '''

        if where == 'symbols':
            bx      = 0
            ex      = len( self._symbols)
        elif where == 'all':
            bx      = 0
            ex      = self._nextNum
        elif where == 'orders':
            bx      = self._nextNum - 1
            ex      = len( self._symbols)
        else:
            raise ValueError('Unknown where=%s' % where )

        names   = [ self._ix2tag[i] for i in xrange(bx,ex) ]

        if which == 'pending':
            qty     = self._pending_long[ bx:ex ] + self._pending_short[ bx:ex ]
        elif which == 'canceled':
            qty     = self._canceled[ bx:ex ]
        elif which == 'realized':
            qty     = self._realized[ bx:ex ]
        elif which == 'all':
            realized     = self._realized[ bx:ex ]
            canceled     = self._canceled[ bx:ex ]
            pending    = self._pending_long[ bx:ex ] + self._pending_short[ bx:ex ]
            import pandas
            return pandas.DataFrame( [pending, realized, canceled], columns=names )
        else:
            raise ValueError('Unknown which=%s' % which )

        if how == 'raw':
            return names, qty
        elif how == 'dict':
            return dict( (n,q) for (n,q) in zip(names, qty))
        elif how == 'table':
            return dict( (n,q) for (n,q) in zip(names, qty))
        elif how == 'pandas':
            import pandas
            return pandas.DataFrame( [qty], columns=names )

        else:
            raise ValueError('Unknown how=%s' % how )

    def getCanceledByIx(self, ix ):
        '''return signed cancelled amount '''
        return self._canceled[ ix ]

    def getRealizedByIx(self, ix ):
        '''return signed realized amount '''
        return self._realized[ ix ]

    def validLenIx(self, ix, vals, verbose = True ):
        l0, l1 = len(ix), len(vals)
        if l0 != l1:
            msg = 'Wrong sizes for ix=%s and vals=%s' % ( str( l0 ), str( l1 ) )
            if verbose:
                logger.error( msg )
            self.addError(status='INVALID_LEN', data=(l0, l1), msg=msg )
            return False
        return True
        
    def _validKillAddByIx( self, name, vals, ix, verbose=True ):
        '''check new add for validity '''

        pending = self._pending_long[ ix ] + self._pending_short[ ix ]

        if numpy.any( vals * pending < 0 ):
            msg = 'wrong sign %s %s %s' % ( str( ix ), str( vals ), str( pending ) )
            if verbose:
                logger.error( msg )
            self.addError(status='INVALID_VALUE', data=( ix, vals, pending ), msg=msg )
            return False

        if numpy.any( abs(vals) > abs(pending) ):
            msg = 'wrong size %s %s %s' % ( str( ix ), str( vals ), str( pending ) )
            if verbose:
                logger.error( msg )
            self.addError(status='INVALID_VALUE', data=( ix, vals, pending ), msg=msg )
            return False

        return True

    def _adjustPending(self, ix, vals):
        with self._pending_Lock:
            if vals[0] > 0:
                self._pending_long[ ix ] -= vals
            else:
                self._pending_short[ ix ] -= vals

    def _addByNameByIx(self, name, ix, vals, checked=False, verbose=True ):
        '''return newly cancelled amount '''
        vals = numpy.array( vals )
        ix   = numpy.array( ix )
        
        if not self.validLenIx( ix, vals, verbose = verbose ):
            return False

        if not checked and not self._validKillAddByIx( name=name, vals=vals, ix=ix, verbose=verbose ):
            return False

        if name == 'realized':
            self._realized[ ix ] += vals
            self._adjustPending(ix=ix, vals=vals)

        elif name == 'canceled':
            self._canceled[ ix ] += vals
            self._adjustPending(ix=ix, vals=vals)

        elif name == 'pending':
            with self._pending_Lock:
                if vals[0] > 0:
                    self._pending_long[ ix ] += vals
                else:
                    self._pending_short[ ix ] += vals
        else:
            raise ValueError('Unknown name=%s', name)
        return True

    def addCanceledByIx(self, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        return self._addByNameByIx(
            name='canceled', ix=ix, vals=vals, checked=checked, verbose=verbose )

    def addRealizedByIx(self, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        return self._addByNameByIx(
            name='realized', ix=ix, vals=vals, checked=checked, verbose=verbose )

    def addPendingByIx(self, ix, vals, checked=True, verbose=False ):
        '''main entry point - adding new pending positions '''
        logger.debug('addPendingByIx: ix=%s vals=%s', ix, vals)
        return self._addByNameByIx(
            name='pending', ix=ix, vals=vals, checked=checked, verbose=verbose )
