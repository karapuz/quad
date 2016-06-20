'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.orderstate module
DESCRIPTION : this module contains order state objects
'''
import os
import numpy
import threading
import robbie.util.margot as margot
import robbie.tweak.value as twkval
import robbie.turf.util as turfutil
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.util.mmap_array as mmap_array

MAXNUM = 1000000

class OrderState( object ):
    '''
    OrderState tracks status of related orders/exposure objects
    MargotRoot   = /margot/ivp
    Domain       = echo         # pretty much a constant. Other domains: risk management?
    Session      = 20160504     # tied to a day
    Activity     = mirror       # is related to echo; mirror, trade, market
    '''
    def __init__(self, readOnly, maxNum, symIds, debug=True ):
        ''' the constructor '''
        return self.init( readOnly=readOnly, maxNum=maxNum, symIds=symIds, debug=debug )

    def init( self, readOnly ,maxNum, symIds, debug ):
        '''
            realized
            pending
            rejected
            canceled
        '''

        self._maxNum    = maxNum
        self._nextNum   = 0
        self._tag2ix    = {}
        self._ix2tag    = {}

        turf            = twkval.getenv( 'run_turf' )
        domain          = turfutil.get(turf=turf, component='shared_location', sub='domain' )
        session         = twkval.getenv('run_session')
        user            = twkval.getenv('env_userName' )
        shape           = ( self._maxNum,  )

        if readOnly:
            mmapFunc    = mmap_array.newRead
        else:
            mmapFunc    = mmap_array.zeros

        vars = dict( domain=domain, user=user, session=session, shape=shape )
        self._realized  = mmapFunc( activity='orderstate-realized', **vars )
        self._pending   = mmapFunc( activity='orderstate-pending',  **vars )
        self._canceled  = mmapFunc( activity='orderstate-canceled', **vars )
        self._rejected  = mmapFunc( activity='orderstate-rejected', **vars )
        self._symids    = mmapFunc( activity='orderstate-symids',   **vars )
        
        if symIds != None and not readOnly:
            self._symids[ :len( symIds ) ] = symIds

        self._state         = { 
            'realized'      : self._realized,
            'pending'       : self._pending,
            'canceled'      : self._canceled,
            'rejected'      : self._rejected,
        }
    
        self._lastError     = None
        self._addTagLock    = threading.Lock()
        self._pending_Lock  = threading.Lock()
        
    def getFullByType(self, posType, maxLen ):
        ''' get a slice of all data for the type '''
        return self._state[ posType ][: maxLen]
    
    def dump(self, fd, frmt='multiLine' ):
        if frmt == 'multiLine':
            fd.write( frmt + ':\n' )
            for k,v in self._state.iteritems():
                fd.write( str( k ) + ':\n' )
                fd.write( str( v[ : self._nextNum ].tolist() ) + '\n' )
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
        with self._addTagLock:
            if tag in self._tag2ix:
                return self._tag2ix[ tag ]
            c = self._nextNum
            self._tag2ix[ tag ] = c
            self._ix2tag[ c   ] = tag        
            self._nextNum += 1        
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
                'realized'  : self._realized[ix],
                'pending'   : self._pending[ix],
            }
        else:
            return self._realized[ix], self._pending[ix]

    def getPosStateByTag(self, tag, asDict=False ):
        return self.getPosStateByIx(ix=self.getIxByTag(tag), asDict=asDict )

    def getStateByIx(self, name, ix ):
        return self._state[ name ][ ix ]

    def getPendingByIx(self, ix ):
        '''
        return signed pending amount 
        Note: the same order can not have both pending long and short, but aggregates CAN!
        '''
        return self._pending[ ix ]

    def getCanceledByIx(self, ix ):
        '''return signed cancelled amount '''
        return self._canceled[ ix ]

    def getRejectedByIx(self, ix ):
        '''return signed rejected amount '''
        return self._rejected[ ix ]

    def getKilledByIx(self, ix ):
        '''
        return signed rejected and canceled amount 
        Note: the same order can not have both pending long and short
        '''
        return self._rejected[ ix ] + self._canceled[ ix ]

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

        pending = self._pending[ ix ]

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
        else:
            self._state[ name  ][ ix ] += vals

        with self._pending_Lock:        
            self._pending[ ix ] += vals

        return True

    def addRejectedByIx(self, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        return self._addByNameByIx(
            name='rejected', ix=ix, vals=vals, checked=checked, verbose=verbose )

    def addCanceledByIx(self, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        return self._addByNameByIx(
            name='canceled', ix=ix, vals=vals, checked=checked, verbose=verbose )

    def addRealizedByIx(self, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        return self._addByNameByIx(
            name='realized', ix=ix, vals=vals, checked=checked, verbose=verbose )

    def addPendingByIx(self, ix, vals, verbose=False ):
        '''main entry point - adding new pending positions '''
        vals = numpy.array( vals )
        ix   = numpy.array( ix )
        with self._pending_Lock:
            self._pending[ ix ] += vals
        return True
