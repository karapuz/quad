'''
    strategies

'''

import numpy
import tables
import datetime
import functools

import meadow.lib.calendar as cal
import meadow.lib.marketdata as md
import meadow.tweak.value as twkval
import meadow.lib.context as context
import meadow.timeseries.daily as mtd
import meadow.lib.pytables as pytables
from   meadow.lib.logging import logger
import meadow.strategy.schedule as schedule
import meadow.lib.environment as environment
import meadow.lib.errorReporting as errorReporting

def isRealTimeBlock( blockType ):
    return blockType in ( 'Trade', 'Update', 'Mrk2Mkt' )

def sa_getData( modelName, params, debug=False ):
    tagName     = params.get( 'TagName', environment.formTagName( datetime.datetime.now() ) )
    endDate     = params.get( 'EndDate', twkval.getenv('today') )
    space       = params[ 'SymbolSpace' ]
    startDate   = params[ 'StartDate' ]    
    return _getYahooData( space, tagName, startDate, endDate )
    
def _getYahooData( space, tagName, startDate, endDate ):
    root        = environment.getDataRoot( 'yahoo', 'matrix' )
    try:            
        with context.Timer() as t:
            volume      = pytables.readArray( (root, tagName, space, 'volume'    ), ('volume',   'mat' ) )
            adjclos     = pytables.readArray( (root, tagName, space, 'adjclose'  ), ('adjclose', 'mat' ) )
            clos        = pytables.readArray( (root, tagName, space, 'close'     ), ('close',    'mat' ) )
            dividend    = pytables.readArray( (root, tagName, space, 'dividends' ), ('dividends','mat' ) )
            
            symbols     = numpy.array( pytables.readArray( (root, tagName, space, 'day' ), ('symbols', ) ) )
            dates       = pytables.readArray( (root, tagName, space, 'day' ), ('dates', ) )
            canload     = numpy.array( pytables.readArray( (root, tagName, space, 'day' ), ('CANLOAD',  ) ) )
            
    except tables.exceptions.NoSuchNodeError:
        logger.debug('---------------------')        
        logger.debug('root     = %s' % root )
        logger.debug('tagName  = %s' % tagName )
        logger.debug('endDate  = %s' % endDate )
        logger.debug('space    = %s' % space )
        raise
    
    _d, clos    = mtd.cut( clos, dates, startDate, endDate )
    _d, adjclos = mtd.cut( adjclos, dates, startDate, endDate )
    _d, dividend= mtd.cut( dividend, dates, startDate, endDate )
    _d, volume  = mtd.cut( volume, dates, startDate, endDate )

    logger.info( 'tagName = %8s, %5s [ %8s-%8s, %8s-%8s ] ' % (
           tagName, t.elapsed(), startDate, endDate, _d[0], _d[-1]
    ) )
    
    errorReport = errorReporting.ErrorReport( 
        root=root, tagName=tagName, strategy=space )
    
    badSymbols = symbols[ canload == False ]
    
    if len( badSymbols ) :
        logger.info( 'cannotload %s\n%s\n' % ( 'Following symbols are not loadable', '\n'.join( badSymbols ) ) )
    
    symbols    = symbols[ canload == True ]
    
    # Convert to MIDs
    from meadow.lib.symbChangeDB import symbDB
    MIDs = [symbDB.lastGoodMID(symb, int(tagName)) for symb in symbols] #@UndefinedVariable
    
    return { 
        'volume'        : volume, 
        'unadjvolume'   : numpy.zeros(volume.shape),
        'close'         : clos, 
        'adjclose'      : adjclos, 
        'dividend'      : dividend, 
        'dates'         : _d, 
        'symbols'       : MIDs,
        'dataId'        : ( space, tagName ),
        'errorReport'   : errorReport,
        'symbology'     : 'MID'
    }

def _getNxcoreData( space, tagName, startDate, endDate ):
    h5nodeNamesAndDests = {
        'adjvolMat'   : 'volume',
        'priceMat'    : 'close',
        'adjpriceMat' : 'adjclose',
        'volMat'      : 'unadjvolume',
    }
    
    dataDict = {}
    defaultToD = '0930_0359'
    defaultTransform = 'lastprice'
    
    for key,val in h5nodeNamesAndDests.iteritems():
        dates, MIDs, nodeMat = md.getAdjustedData(space, tagName, defaultToD, defaultTransform, key)
        _d, choppedMat = mtd.cut( nodeMat, dates, startDate, endDate )
        dataDict[val] = choppedMat
        
    dataDict['symbols'] = MIDs
    dataDict['dates'] = _d
    
    return dataDict

def _getNxc( ToD, transform, space, tagName, startDate, endDate ):
    h5nodeNamesAndDests = {
        'adjvolMat'   : 'volume',
        'priceMat'    : 'close',
        'adjpriceMat' : 'adjclose',
        'volMat'      : 'unadjvolume',
    }
    
    dataDict = {}
    
    for key,val in h5nodeNamesAndDests.iteritems():
        dates, MIDs, nodeMat = md.getAdjustedData( space=space, tag=tagName, ToD=ToD, transform=transform, node=key )
                
        d, choppedMat = mtd.cut( nodeMat, dates, startDate, endDate )
        if not len( d ):
            if startDate > endDate:
                logger.error( '_getNx: this cuts all data! ( startDate > endDate ) space=%s tagName=%s startDate=%s endDate=%s' % ( space, tagName, startDate, endDate ) )
            else:
                logger.error( '_getNx: this cuts all data! space=%s tagName=%s startDate=%s endDate=%s' % ( space, tagName, startDate, endDate ) )
        dataDict[ val ] = choppedMat
        
    dataDict['symbology'    ] = 'MID'
    dataDict['symbols'      ] = MIDs
    dataDict['dates'        ] = d
    
    return dataDict


sourceRetrievalFcns = {
    'yahoo'         : _getYahooData,
    'nxcore'        : _getNxcoreData,

    'nxc_high_935-357'      : functools.partial( _getNxc, '0935_0357'  , 'high'), 
    'nxc_low_935-357'       : functools.partial( _getNxc, '0935_0357'  , 'low'), 

    'nxc_high_935-344'      : functools.partial( _getNxc, '0935_0344'  , 'high'), 
    'nxc_low_935-344'       : functools.partial( _getNxc, '0935_0344'  , 'low'), 

    'nxc_lastmids_930-351'  : functools.partial( _getNxc, '0930_0351'  , 'lastmid' ), 
    'nxc_lastmids_352'      : functools.partial( _getNxc, '0352'       , 'lastmid' ),
        
    'nxc_lasttrade_930-935' : functools.partial( _getNxc, '0930_0935'  , 'lastprice'), 
    'nxc_lasttrade_930-359' : functools.partial( _getNxc, '0930_0359'  , 'lastprice'), 
    'nxc_lasttrade_930-351' : functools.partial( _getNxc, '0930_0351'  , 'lastprice'), 
    'nxc_lasttrade_930-352' : functools.partial( _getNxc, '0930_0352'  , 'lastprice'),
    'nxc_lasttrade_930-353' : functools.partial( _getNxc, '0930_0353'  , 'lastprice'),
    'nxc_lasttrade_930-354' : functools.partial( _getNxc, '0930_0354'  , 'lastprice'),
    'nxc_lasttrade_930-355' : functools.partial( _getNxc, '0930_0355'  , 'lastprice'),
    'nxc_lasttrade_930-357' : functools.partial( _getNxc, '0930_0357'  , 'lastprice'),
    'nxc_lasttrade_357-359' : functools.partial( _getNxc, '0357_0359'  , 'lastprice'),

    'nxc_lasttrade_351'     : functools.partial( _getNxc, '0351'       , 'lastprice'),
    'nxc_lasttrade_352'     : functools.partial( _getNxc, '0352'       , 'lastprice'),
    'nxc_lasttrade_356'     : functools.partial( _getNxc, '0356'       , 'lastprice'),

    'nxc_avgmin_352'        : functools.partial( _getNxc, '0352'       , 'avgprice'   ),
    'nxc_avgmin_353'        : functools.partial( _getNxc, '0353'       , 'avgprice'   ),
    'nxc_avgmin_354'        : functools.partial( _getNxc, '0354'       , 'avgprice'   ),
    'nxc_avgmin_355'        : functools.partial( _getNxc, '0355'       , 'avgprice'   ),
    'nxc_avgmin_356'        : functools.partial( _getNxc, '0356'       , 'avgprice'   ),
    'nxc_avgmin_358'        : functools.partial( _getNxc, '0358'       , 'avgprice'   ),
}

def sa_getMergedMultiBlock( modelName, params, debug=False, scheduleNames=None, includeDivs=True ):
    ret     = {}
    opMode  = twkval.getenv( 'run_mode' )
    
    for blockType, blockSpecs, schedName in scheduleNames:
        
        skip = False
        
        if opMode == 'sim-seed' and blockType != 'Calib':
            skip = True
        
        if skip:
            logger.debug( '%s does not need %8s. Skipping.' % ( opMode, blockType ) )
            continue
        
        blockName = ( blockType, blockSpecs )
        
        blockVals = sa_getMergedData( 
                blockName   = blockName, 
                modelName   = modelName, 
                params      = params, debug=debug, scheduleName=schedName, 
                includeDivs = includeDivs )
        
        ret[ blockName ] = blockVals        
    return ret

def sa_getMergedData( blockName, modelName, params, debug=False, scheduleName = None, includeDivs = True ):
    '''
    Merges data from multiple sources according to the dataSourceSchedule
    
    dataSourceSchedule is a list of tuples:
    (
    (date, source)
    (date, source)
    ...
    (date, source)
    )
    
    or
    
    (
    (date,(source,tag)) 
    (date,(source,tag)) 
    ...
    (date,(source,tag)) 
    )
    
    defining dates at which each source begins to be used
    (and optional tags)
    
    If dataSourceSchedule is None the default behavior is to use NxCore where
    possible and patch with yahoo.
    
    '''
    global sourceRetrievalFcns
    
    dataSchedule= schedule.getSched( scheduleName )
    space       = params[ 'SymbolSpace' ]

    endDate     = twkval.getenv( 'run_tradeDate' )
    opMode      = twkval.getenv( 'run_mode' )
    ( blockType, _blockSpecs ) = blockName
    
    if opMode in ( 'sim', 'dev' ) :
        if blockType == 'Calib' and opMode == 'sim':
            endDate = cal.bizday( endDate, '-2b' )
        elif blockType == 'Calib' and opMode == 'dev':
            endDate = cal.bizday( endDate, '-3b' )
        else:
            endDate = cal.bizday( endDate, '-1b' )
            
    elif opMode in ( 'sim-seed', 'sim-prod' ):
        if blockType == 'Calib':
            endDate = cal.bizday( endDate, '-1b' )

    elif opMode == 'trade-prod':
        pass
    else:
        raise ValueError( 'Unknown opMode = %s' % opMode )

    startDate   = params[  'FirstTradeDate' ] if isRealTimeBlock( blockType ) else params[ 'StartDate' ]
            
    import meadow.lib.space as sp
    import meadow.lib.cacs as cax
    
    spaceMIDs = sp.getMIDs(space)
    assetDict = dict((n,i) for (i,n) in enumerate(spaceMIDs))
     
    assert dataSchedule[0][0] <= startDate , 'Need a source valid for StartDate'
        
    def getIdxFromSchedule( date ): # Could make this super optimized, but doesn't matter
        if len(dataSchedule) == 1:
            return 0
        for i, pair in enumerate(dataSchedule):
            sDate, _ = pair 
            if date < sDate:
                return i - 1
    
    def resortAndAppend( mat1, colIndexOrder, mat2 ):
        _, cols1 = mat1.shape
        rows2, _ = mat2.shape
        output = numpy.zeros((rows2,cols1))
        output[numpy.ix_(xrange(rows2),colIndexOrder)] = mat2
        return numpy.vstack((mat1,output))
    
    sourceId = scheduleName
     
    # initialize empty data
    zeros = numpy.empty( ( 0, len( spaceMIDs ) ) )
    outputData = { 
        'unadjvolume'   : zeros.copy(),         
        'volume'        : zeros.copy(), 
        'close'         : zeros.copy(), 
        'adjclose'      : zeros.copy(), 
        'dates'         : numpy.empty( (0,) ), 
        'symbols'       : spaceMIDs,
        'dataSourceSchedule' : dataSchedule, 
    }
    curSourceIdx = getIdxFromSchedule(startDate)
    
    tagName     = params[ 'TagName' ]
    if opMode == 'dev':
        outputData[ 'dataId' ] = ( 'dev' , modelName, space, tagName, sourceId )
    else:
        outputData[ 'dataId' ] = ( 'prod', modelName, space, 'noTag', sourceId )

    # Could use for loop, but maybe not starting at beginning making xrange less useful
    while curSourceIdx <= len(dataSchedule) - 1:
        sourceStartDate, source = dataSchedule[ curSourceIdx ]
        sourceStartDate = max(sourceStartDate,startDate)
        
        if isinstance(source, tuple ):
            source, sourceTag = source
        else:
            sourceTag = tagName
            
        if curSourceIdx < len(dataSchedule) - 1:
            sourceEndDate, _ = dataSchedule[ curSourceIdx + 1 ]
            # Once again, we might not get a valid date with the line below,
            # but it should be fine
            sourceEndDate -= 1
        else:
            sourceEndDate = endDate
        
        retriever       = sourceRetrievalFcns[ source ]
        sourceEndDate   = min( sourceEndDate, endDate )
        dataDict        = retriever( space, sourceTag, sourceStartDate, sourceEndDate )
        
        # Data sources might not have symbols in the same order.  Build the transform
        sourceColOrdering = [ assetDict[MID] for MID in dataDict['symbols'] ]
        # Append matrix data
        for dataName in ('unadjvolume','volume', 'close', 'adjclose' ):
            if not len( dataDict[dataName] ):
                logger.error( 'No data for %s->%s. Adjusted prices is incomplete.' % ( str( blockName ), dataName ) )
            outputData[dataName] = resortAndAppend( outputData[dataName], sourceColOrdering, dataDict[dataName] )
        # Append dates
        outputData['dates'] = numpy.hstack( ( outputData['dates'], dataDict['dates'] ) )

        for copyKeys in [ 'symbology' ]:
            outputData[ copyKeys ] = dataDict[ copyKeys ]
            
        if sourceEndDate >= endDate:
            break
        else:
            curSourceIdx += 1
            
    if includeDivs:
        # Get dividends from Bloomberg
        _, divDates, divMat = cax.regularDivMatrix(space)
        assert divDates[-1] >= endDate , 'divDates not current up to endDate'
        # will use last known dataDict
        endDate_    = dataDict[ 'dates' ][-1]
        startDate_  = dataDict[ 'dates' ][0]

        divdates, dividend = mtd.cut( divMat.T, divDates, startDate_, endDate_ )
        outputData['dividend'] = dividend
        outputData['divdates'] = divdates
        
        logger.debug( 'sa_getMergedData: startDate=%s, endDate=%s divDates=(%s,%s) divMat.shape=%s' % ( 
            startDate, endDate, divdates[0], str( divdates[-2:] ), str( divMat.shape ) ) 
        )

        # logger.debug('sa_getMergedData: len( divDates )=%s' % str( len( divDates ) ) )
        # prettyPrint( title='sa_getMergedData', data=outputData )
    return outputData

def prettyPrint( title, data ):
    '''
    '''
    for key, value in data.iteritems():
        try:
            logger.debug('%s: key=%-12s shape=%s' % ( title, key, value.shape ) )
        except:
            try:
                logger.debug('%s: key=%-12s   len=%s' % ( title, key, len( value ) ) )
            except:
                logger.debug('%s: key=%-12s  type=%s' % ( title, key, str( type ( value ) ) ) )
            