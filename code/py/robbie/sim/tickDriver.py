import numpy
import pylab

from   optparse import OptionParser
import meadow.tweak.value as twkval
import meadow.allocation.util as alut
import meadow.lib.logging  as logging
import meadow.order.manager as manager
import meadow.lib.tickdata as tickdata
from   meadow.lib.logging import logger
import meadow.order.relation as relation
import meadow.sim.guiutil as guiutil
import meadow.lib.fetch as libfetch

import meadow.order.twap_2LR_LGCL_MV as twapMv
import meadow.order.twap_2LR_LGCL_MV_TE as twapMvTe

import meadow.sim.tickEngine as tickEngine

def midPrice( bidPriceSize, askPriceSize ):
    instrIx     = 0    
    priceArrIx, _cumSizeIx, sizeArrIx   = 0, 1, 2

    bid = bidPriceSize[ :, priceArrIx, instrIx ]
    ask = askPriceSize[ :, priceArrIx, instrIx ]

    bidsize = bidPriceSize[ :, sizeArrIx, instrIx ]
    asksize = askPriceSize[ :, sizeArrIx, instrIx ]

    nSkip = 100
    good = ( ask != 0 ) * ( bid != 0 ) * numpy.array( [ ( b % nSkip == 0 ) for b in xrange( len( ask ) ) ] )
    mids = .5 * ( bid[ good ] + ask[ good ] )
    vols = .5 * ( bidsize[ good ] + asksize[ good ] )
    return mids, vols, ( ask[ good ] - bid[ good ] )/mids * 10000

def run( execSchema, symbols, shares, bids, asks, times, 
         targetTime, targetStep, targetWorst, levelShift, 
         maxQueue, minQueue, skipSpikes, maxSpike,  
         twapModule ):
    
    instrMap = dict( ( name, i ) for ( i, name ) in enumerate( symbols ) )
    syms, expNames, amounts = alut.allocNameSymShare( execSchema=execSchema, symbols=symbols, shares=shares )

    relNames    = symbols + tuple( expNames  )
    twkval.setval( 'run_turf', 'TEST-1' )

    mids        = numpy.array( range( 4000 ) )
    relObj      = relation.OrderState( readOnly=False, maxNum=40000, mids=mids, debug=False )
    relObj.addTags( relNames )
            
    iExp = numpy.array( [ 0 ] * len( relNames ) )
    
    assert( len( times ) == len( asks ) )
    assert( len( bids  ) == len( asks ) )
    
    startTime   = times[0]    
    linkObj     = tickEngine.ExecLink( startTime, instrMap )    
    ordMan      = manager.OrderManager( 
                    relObj          = relObj, 
                    linkObj         = linkObj, 
                    initialExposure = iExp )
    
    stratName   = 'TestStrategy0'
    targetShares= ( ( sym, expName, stratName, amount ) for ( sym, expName, amount ) in zip ( syms, expNames, amounts ) )
    
    currentTime = startTime
    
    twap0 = twapModule.TWAP( 
                relObj          = relObj, 
                orderExecLink   = ordMan, 
                targetShares    = targetShares, 
                targetTime      = targetTime, 
                targetStep      = targetStep  )

    twap0.setTargetWorst( targetWorst )
    twap0.setLevelShift( levelShift )
    
    if hasattr( twap0, 'setMaxQueue'):    
        twap0.setMaxQueue( maxQueue )
    if hasattr( twap0, 'setMinRemove'):    
        twap0.setMinRemove( minQueue )
    
    # skipSpikes, maxSpike = True, 2.
    twap0.setSkipSpikes( skipSpikes )
    twap0.setMaxSpike( maxSpike )

    twap0.start( startTime=startTime )
    prevTime    = 0
    
    instrIx     = 0    
    priceArrIx, _cumSizeIx, _sizeArrIx   = 0, 1, 2
    for ( bidPriceSize, askPriceSize, currentTime ) in zip( bids, asks, times ):
        bid = bidPriceSize[ priceArrIx ][ instrIx ]
        ask = askPriceSize[ priceArrIx ][ instrIx ]
        
        linkObj._spread.append( ( bid, ask ) )
        
        if currentTime - prevTime > targetStep:
            twap0.cycle( currentTime, bidPriceSize, askPriceSize )
            prevTime = currentTime
            
        linkObj.marketMoves( bidPriceSize=bidPriceSize, askPriceSize=askPriceSize )
        if twap0.status() != 'normal':
            break
        
    realized = twap0.getRealized( symbols )
    assert( len( realized ) == 1)
    return linkObj, realized[0]

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-b', '--instarbucks',  action='store_true', default=None, dest='instarbucks')
    parser.add_option('-d', '--date',  action='store', default=None, dest='date')
    parser.add_option('-s', '--symbol',  action='store', default=None, dest='symbol')
    parser.add_option('-t', '--targettime',  action='store', default=None, dest='targettime')
    parser.add_option('-q', '--qty',  action='store', default=None, dest='qty')
    parser.add_option('-c', '--scale',  action='store', default=1.0, dest='scale')
    parser.add_option('-y', '--twaptype',  action='store', default='MV_TE', dest='twaptype')
    parser.add_option('-x', '--maxqueue',  action='store', default=3, dest='maxqueue')
    parser.add_option('-z', '--minqueue',  action='store', default=0, dest='minqueue')
    parser.add_option('-k', '--maxspike',  action='store', default=0, dest='maxspike')

    (options, args) = parser.parse_args()

    twkval.setval( 'run_env', 'unittest' ) # create a single threaded trades logger
    
    logging.toFile('tickDriver_', mode='p' )
    logger.disable()
    # procTime    = options.time
    procDate    = options.date
    symbol      = options.symbol

    twapType    = options.twaptype
    
    if twapType == 'MV':
        twapModule = twapMv
    elif twapType == 'MV_TE':
        twapModule = twapMvTe
    else:
        raise ValueError( 'Unknown twapType=%s' % twapType )
    
    hour        = 15
    shares      = float( options.qty )
    scale       = float( options.scale )
    targetTime  = int( options.targettime )

    twkval.setval( 'env_inStarbucks', options.instarbucks )
    
    times_, bids_, asks_ = tickdata.getQuotesForSim( date=procDate, symbol=symbol )

    execSchema      = 'CASH'
    results         = []    

    resultShifts    = { '1_3'   : [ .01, .02, .03 ] }
    targetSteps     = { '1_10'  : numpy.arange( 1, 10, 1) }
    targetWorsts    = { '2c_10c': numpy.arange( .02, .10, .02 ) }
    maxQueue        = int( options.maxqueue )
    minQueue        = int( options.minqueue )
    
    if options.maxspike:
        maxSpike    = float( options.maxspike )    
        skipSpikes  = True  
    else:
        maxSpike    = 0    
        skipSpikes  = False  

    resultShiftName = '1_3'
    targetStepName  = '1_10'
    targetWorstName = '2c_10c'

    resutlName = ( 
        ( 'resultShift',    resultShiftName     ), 
        ( 'targetStep',     targetStepName      ), 
        ( 'targetWorst',    targetWorstName     ), 
        ( 'date',           procDate            ),
        ( 'symbol',         symbol              ),
        ( 'qty',            shares              ),
        ( 'twapType',       twapType            ), 
        ( 'maxQueue',       maxQueue            ),
        ( 'minQueue',       minQueue            ),
        ( 'scale',          scale               ),
        ( 'skipSpikes',     skipSpikes          ), 
        ( 'maxSpike',       maxSpike            ),
    )

    if not libfetch.exists(name=resutlName ):
        for minute in [ 50, 51, 52, 53, 54, 55 ]:
            times, bids, asks = tickdata.cut( hour=hour, minute=minute, times=times_, bids=bids_, asks=asks_, endMinute=minute+1 )
            for levelShift in scale * ( numpy.array( resultShifts[ resultShiftName ] ) ):
                for targetStep in targetSteps[ targetStepName ]:
                    for targetWorst in scale * targetWorsts[ targetWorstName ]:
                        linkObj, realized = run( 
                                    execSchema  = execSchema, 
                                    symbols     = ( symbol, ), 
                                    shares      = ( shares, ), 
                                    bids        = bids, 
                                    asks        = asks, 
                                    times       = times, 
                                    targetTime  = targetTime, 
                                    targetStep  = targetStep, 
                                    targetWorst = targetWorst,
                                    levelShift  = levelShift,
                                    maxQueue    = maxQueue,
                                    minQueue    = minQueue,
                                    maxSpike    = maxSpike,  
                                    skipSpikes  = skipSpikes,                                    
                                    twapModule  = twapModule )
                        
                        r = linkObj.analyse()
                        if r == None:
                            logger.debug( 'Bad: levelShift=%5.2f, targetStep=%5.2f, targetWorst=%5.2f' % ( levelShift, targetStep, targetWorst ) )
                        results.append( ( minute, targetStep, targetWorst, levelShift, realized, r ) )
    
        libfetch.dump( name=resutlName, obj=results)
    else:
        results = libfetch.retrieve( name=resutlName )
        group       = {}
        for groupName in ( 'targetStep', 'targetWorst', 'levelShift' ):
            group[ groupName ] = [ {}, {} ]

        sign = numpy.sign( shares )
        for ( minute, targetStep, targetWorst, levelShift, realized, r ) in results:
            if r:            
                firstPrice, mu, mu1, sigma, dm1, ds1 = r
                targetPrice = firstPrice
                cost        = ( mu - targetPrice ) / firstPrice * 10000 * numpy.sign( realized )
            else:
                cost        = 0
                realized    = 0
            
            if targetStep not in group[ 'targetStep' ][0]:
                group[ 'targetStep'][0][ targetStep ] = []
                group[ 'targetStep'][1][ targetStep ] = []
                
            if targetWorst not in group[ 'targetWorst' ][0]:
                group[ 'targetWorst'][0][ targetWorst ] = []
                group[ 'targetWorst'][1][ targetWorst ] = []

            if levelShift not in group[ 'levelShift' ][0]:
                group[ 'levelShift'][0][ levelShift ] = []
                group[ 'levelShift'][1][ levelShift ] = []
    
            group[ 'targetStep' ][0][ targetStep  ].append( cost )
            group[ 'targetStep' ][1][ targetStep  ].append( realized )
            group[ 'targetWorst'][0][ targetWorst ].append( cost )
            group[ 'targetWorst'][1][ targetWorst ].append( realized )
            group[ 'levelShift' ][0][ levelShift  ].append( cost )
            group[ 'levelShift' ][1][ levelShift  ].append( realized )

        times, bids, asks = tickdata.cut( hour=hour, minute=50, times=times_, bids=bids_, asks=asks_, endMinute=55 )
        
        line = ( twapType, round( bids[0].tolist()[0][0] ), 'x=%d' % maxQueue, 'z=%d' % minQueue )
        guiutil.plots(group[ 'targetStep' ], 'TargetStep  cost %s' % str( ( symbol, shares, line )))
        guiutil.plots(group[ 'targetWorst'], 'TargetWorst cost %s' % str( ( symbol, shares, line )))
        guiutil.plots(group[ 'levelShift' ], 'LevelShift  cost %s' % str( ( symbol, shares, line )))
        
        mids, vols, spread = midPrice( bidPriceSize=bids, askPriceSize=asks )

        guiutil.simpleplot( ( 'Price', 'Vols', 'Spread' ), ( mids, vols, spread ) )
        
        pylab.show()

    print results[0]