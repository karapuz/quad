'''
this module contains relations objects
'''
import os
import numpy
import threading
import meadow.tweak.value as twkval
import meadow.lib.config as libconf
import meadow.tweak.context as twkcx
import meadow.lib.winston as winston
from   meadow.lib.logging import logger
import meadow.lib.mmap_array as mmap_array

MAXNUM = 1000000

def sharedSpaceExists( varName='relation-realized' ):
    turf    = twkval.getenv( 'run_turf' )
    domain  = libconf.get( turf=turf, component='relation', sub='domain' )    
    tweaks  = {}
    if libconf.exists( turf=turf, component='relation', sub='owner' ):
        owner   = libconf.get( turf=turf, component='relation', sub='owner' )
        wnDir   = libconf.get( turf=turf, component='bob', sub='winstonRoot' )[ owner ]
        tweaks[ 'run_winstonRoot'] = wnDir

    instanceName = libconf.get( turf=turf, component='relation', sub='instance' )
    logger.debug( 'sharedSpaceExists: instanceName=%s' % instanceName )
    with twkcx.Tweaks( ** tweaks ):
        path    = winston.getSharedVar( domain=domain, instance=instanceName, varName=varName, create=True )
        return os.path.exists( path )

class OrderState( object ):
    '''
    OrderState tracks status of related orders/exposure objects
    '''
    def __init__(self, readOnly, maxNum, mids, debug=True ):
        ''' the constructor '''
        return self.init( readOnly=readOnly, maxNum=maxNum, mids=mids, debug=debug )

    def init( self, readOnly ,maxNum, mids, debug ):        
        ''' the actual constructor. Pick up the mmap env '''
        turf        = twkval.getenv( 'run_turf' )
        domain      = libconf.get( turf=turf, component='relation', sub='domain' )

        tweaks      = {}
        if libconf.exists( turf=turf, component='relation', sub='owner' ):
            owner   = libconf.get( turf=turf, component='relation', sub='owner' )
            wnDir   = libconf.get( turf=turf, component='bob', sub='winstonRoot' )[ owner ]
            tweaks[ 'run_winstonRoot'] = wnDir

        instanceName = libconf.get( turf=turf, component='relation', sub='instance' )
        
        with twkcx.Tweaks( **tweaks ):
            varPath = winston.getSharedRoot( domain=domain, instance=instanceName, create=True )
            if debug: 
                logger.debug( 'relation sharing varPath=%s' % varPath )
                
            return self._init( readOnly=readOnly, maxNum=maxNum, mids=mids, debug=debug )
    
    def _init( self, readOnly , maxNum, mids, debug=True ):
        '''
        signed
            realized
            
            pendingLong
            pendingShort
            
            rejectedLong
            rejectedShort
            
            canceledLong
            canceledShort
        '''
        self._maxNum        = maxNum
        self._nextNum       = 0
        self._tag2ix        = {}
        self._ix2tag        = {}
        
        shape       = ( self._maxNum,  )        
        turf        = twkval.getenv( 'run_turf' )
        domain      = libconf.get( turf=turf, component='relation', sub='domain' )
        instanceName= libconf.get( turf=turf, component='relation', sub='instance' )
        
        self._bbgVersion= mmap_array.getVersion( domain=domain, instance=instanceName, varName=mmap_array.BbgVersion )
        
        if readOnly:
            self._relationVersion = mmap_array.getVersion( domain=domain, instance=instanceName, varName=mmap_array.RelationVersion, create=True )
            mmapFunc    = mmap_array.newRead
        else:
            self._relationVersion   = mmap_array.incrVersion( domain=domain, instance=instanceName, varName=mmap_array.RelationVersion )
            mmapFunc    = mmap_array.zeros

        if debug:    
            logger.debug('relation: relationVersion=%d' % self._relationVersion )
        
        self._realized      = mmapFunc( domain=domain, instance=instanceName, varName='relation-realized',      shape=shape )
        
        self._pendingLong   = mmapFunc( domain=domain, instance=instanceName, varName='relation-pendingLong',   shape=shape )
        self._pendingShort  = mmapFunc( domain=domain, instance=instanceName, varName='relation-pendingShort',  shape=shape )         
        
        self._canceledLong  = mmapFunc( domain=domain, instance=instanceName, varName='relation-canceledLong',  shape=shape )
        self._canceledShort = mmapFunc( domain=domain, instance=instanceName, varName='relation-canceledShort', shape=shape )
        
        self._rejectedLong  = mmapFunc( domain=domain, instance=instanceName, varName='relation-rejectedLong',  shape=shape )
        self._rejectedShort = mmapFunc( domain=domain, instance=instanceName, varName='relation-rejectedShort', shape=shape )
        
        self._mids          = mmapFunc( domain=domain, instance=instanceName, varName='relation-mids',          shape=shape )
        
        if mids != None and not readOnly:
            self._mids[ :len( mids ) ] = mids

        self._state         = { 
            'realized'      : self._realized,
            
            'pendingLong'   : self._pendingLong,
            'pendingShort'  : self._pendingShort,
            
            'canceledLong'  : self._canceledLong,
            'canceledShort' : self._canceledShort,
            
            'rejectedLong'  : self._rejectedLong,
            'rejectedShort' : self._rejectedShort,
        }
    
        self._lastError = None

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
                'realized'      : self._realized[ix], 
                'pendingLong'   : self._pendingLong[ix], 
                'pendingShort'  : self._pendingShort[ix], 
            }
        else:
            return self._realized[ix], self._pendingLong[ix], self._pendingShort[ix]

    def getPosStateByTag(self, tag, asDict=False ):
        return self.getPosStateByIx(ix=self.getIxByTag(tag), asDict=asDict )

    def getStateByIx(self, name, ix ):
        return self._state[ name ][ ix ]

    def getPendingByIx(self, ix ):
        '''
        return signed pending amount 
        Note: the same order can not have both pending long and short, but aggregates CAN!
        '''
        return self._pendingLong[ ix ] + self._pendingShort[ ix ]

    def getCanceledByIx(self, ix ):
        '''return signed cancelled amount '''
        return self._canceledLong[ ix ] + self._canceledShort[ ix ]

    def getRejectedByIx(self, ix ):
        '''return signed rejected amount '''
        return self._rejectedLong[ ix ] + self._rejectedShort[ ix ]

    def getKilledByIx(self, ix ):
        '''
        return signed rejected and canceled amount 
        Note: the same order can not have both pending long and short
        '''
        return ( 
            self._rejectedLong[ ix ] + self._rejectedShort[ ix ] + 
            self._canceledLong[ ix ] + self._canceledShort[ ix ]
        )

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
        
    def addPendingByIx(self, ix, vals, verbose=False ):
        '''main entry point - adding new pending positions '''
        vals = numpy.array( vals )
        ix   = numpy.array( ix )
        
        posIx = vals > 0
        negIx = vals < 0

        with self._pending_Lock:      
            self._pendingLong [ ix[ posIx ] ] += vals[ posIx ]
            self._pendingShort[ ix[ negIx ] ] += vals[ negIx ]
        
        return True

    def _validKillAddByIx( self, name, posVals, posIx, negVals, negIx, verbose=True ):
        '''check new add for validity '''
        
        if numpy.any( posVals > self._pendingLong[ posIx ] ):
            msg = '[long side] too much %s %s %s' % ( str( posIx ), str( posVals ), str( self._pendingLong[ posIx ] ) )
            if verbose:
                logger.error( msg )
            self.addError(status='INVALID_VALUE', data=( posIx, posVals, self._pendingLong[ posIx ] ), msg=msg )
            return False

        if numpy.any( negVals < self._pendingShort[ negIx ] ):
            msg = '[short side] too much %s %s %s' % ( str( negIx ), str( negVals ), str( self._pendingShort[ negIx ] ) )
            if verbose:
                logger.error( msg )
            self.addError(status='INVALID_VALUE', data=( posIx, negVals, self._pendingShort[ negIx ] ), msg=msg )
            return False
                            
        return True

    def _addByNameByIx(self, name, ix, vals, checked = False, verbose = True ):
        '''return newly cancelled amount '''
        vals = numpy.array( vals )
        ix   = numpy.array( ix )
        
        if not self.validLenIx( ix, vals, verbose = verbose ):
            return False

        posValsIx   = ( vals > 0 )
        negValsIx   = ( vals < 0 )
        
        posVals     = vals[ posValsIx ]
        negVals     = vals[ negValsIx ]
        
        posIx       = ix[ posValsIx ]
        negIx       = ix[ negValsIx ]
        
        if not checked and not self._validKillAddByIx( 
                                    name    = name, 
                                    posVals = posVals, 
                                    posIx   = posIx, 
                                    negVals = negVals, 
                                    negIx   = negIx, verbose=verbose ):
            return False

        if name == 'realized':
            self._realized[ ix ] += vals
        else:
            self._state[ name + 'Long' ][ posIx ] += posVals
            self._state[ name + 'Short'][ negIx ] += negVals

        with self._pending_Lock:        
            self._pendingLong [ posIx ] -= posVals
            self._pendingShort[ negIx ] -= negVals
        
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
