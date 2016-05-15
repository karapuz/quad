import meadow.lib.calendar as cal

import numpy
import meadow.tweak.value as twkval
import meadow.lib.config as libconf
import meadow.lib.winston as winston
import meadow.allocation.util as alut
import meadow.argus.taskenv as taskenv
from   meadow.lib.logging import logger
import meadow.order.relation as relation
import meadow.lib.mmap_array as mmap_array
from   meadow.lib.symbChangeDB import symbDB

def crateMMap( readOnly, name ):
    ''' initialize initial exposure '''    
    maxNum      = relation.MAXNUM
    shape       = ( maxNum, )
    turf        = twkval.getenv( 'run_turf' )
    domain      = libconf.get( turf=turf, component='relation', sub='domain' )
    instanceName= libconf.get( turf=turf, component='relation', sub='instance' )
    
    varPath     = winston.getSharedRoot( domain=domain, instance=instanceName, create=True )    
    logger.debug( '%s: sharing varPath=%s' % ( name, varPath ) )
    
    mmapFunc    = mmap_array.newRead if readOnly else mmap_array.zeros    
    value       = mmapFunc( domain=domain, instance=instanceName, varName='relation-%s' % name, shape=shape )
    return value

def newInitialExposure( readOnly ):
    return crateMMap( readOnly=readOnly, name='initialexposure' )

def newInitialPrice( readOnly ):
    return crateMMap( readOnly=readOnly, name='initialprice' )

def initExposureObj( relObj, asComponent=True, asMMap=True ):
    ''' load exposure from the proper file, and populate memory '''        
    tradeDate   = int( twkval.getenv( 'run_tradeDate' ) ) or cal.today()

    # (('SWAP', 'BARC'), 1000, 2788.0)
    if asMMap:
        iExp_ = newInitialExposure( readOnly=False )
    else:        
        iExp_ = numpy.zeros( relation.MAXNUM )
        
    iExp = winston.loadInitialExposure( debug=True )
    
    iExp2array( iExp_, iExp, relObj, tradeDate )
    
    if asComponent:
        taskenv.setObj('env', 'initialExposure', iExp_ )

def iExp2array( iExp_, iExp, relObj, tradeDate ):    
    for ( ( secType, execVenue ), mid, qty ) in iExp:
        symbol  = symbDB.MID2symb( MID=mid, date=tradeDate )
        expName = alut.formPhysExp( symbol=symbol, secType=secType, execVenue=execVenue )        
        instrIx, expIx    = relObj.addTags( ( symbol, expName ) )
        iExp_[ expIx ]    = qty
        iExp_[ instrIx ] += qty
        
    return iExp_

def computeExposure( iExpMap, relObj, isNetted=False ):
    ''' compute exposure from the proper file, and populate memory '''

    tradeDate   = int( twkval.getenv( 'run_tradeDate' ) ) or cal.today()    
    iExp_       = numpy.zeros( relation.MAXNUM )

    for ( ( secType, execVenue ), mid, qty ) in iExpMap:
        symbol  = symbDB.MID2symb( MID=mid, date=tradeDate )
        expName = alut.formPhysExp( symbol=symbol, secType=secType, execVenue=execVenue )
        
        instrIx, expIx    = relObj.addTags( ( symbol, expName ) )
        iExp_[ expIx ]    = qty
        if isNetted:
            iExp_[ instrIx ] += qty
        else:        
            iExp_[ instrIx ] += abs( qty )
    
    return iExp_

def loadInitValsSeparateStrats( relObj ):
    ''' load exposure from the proper file, and populate memory '''
        
    tradeDate   = int( twkval.getenv( 'run_tradeDate' ) ) or cal.today()
    
    # (('SWAP', 'BARC'), 1000, 2788.0)
    iexp    = numpy.array( )
    iExp    = winston.loadInitialExposure( debug=True )
    
    for ( ( secType, execVenue ), mid, qty ) in iExp:
        symbol  = symbDB.MID2symb( MID=mid, date=tradeDate )
        expName = alut.formPhysExp( symbol=symbol, secType=secType, execVenue=execVenue )
        
        _instrIx, expIx    = relObj.addTags( ( symbol, expName ) )
        iexp[ expIx ]    = qty
    

def initPriceObj( relObj, asComponent=True, asMMap=True  ):
    ''' load prev day price from the proper file, and populate memory '''

    tradeDate   = int( twkval.getenv( 'run_tradeDate' ) ) or cal.today()
    # relObj      = taskenv.getObj('env', 'relations' )

    if asMMap:
        newPriceObj = newInitialPrice( readOnly=False )
    else:        
        newPriceObj = numpy.zeros( relation.MAXNUM )
        
    storedPrice = winston.loadInitialPrice( debug=True )
    mids        = numpy.zeros( newPriceObj.shape )
    iPrice2array( storedPrice, tradeDate, relObj, newPriceObj, mids )
        
    if asComponent:
        taskenv.setObj('env', 'initialPrice', newPriceObj )
    
    return newPriceObj

def iPrice2array( storedPrice, tradeDate, relObj, newPriceObj, mids ):    
    for mid, price in storedPrice.iteritems():
        symbol  = symbDB.MID2symb( MID=mid, date=tradeDate )
        instrIx = relObj.addTag( symbol )
        newPriceObj[ instrIx ] = price
        mids[ instrIx ] = mid
        
        # print 'iPrice', symbol, price
    return newPriceObj
