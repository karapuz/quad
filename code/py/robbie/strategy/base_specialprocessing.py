'''
    strategies special processing routines
'''

import numpy
import pprint
import warnings
import meadow.sim.util as simutil
import meadow.lib.calendar as cal
import meadow.lib.pytables as pytables
import meadow.tweak.value as twkval
from   meadow.lib.logging import logger
import meadow.strategy.util as stratutil
import meadow.math.lib.addNaN as addNaN
import meadow.math.scaleestimator.causalclip as cclip
import meadow.math.missing.symbol_selection as ss

def isTradeBlock( blockType ):
    return blockType in ( 'Update', 'Trade' )

def sa_specialProcessing( blockName, params, origData, stratSymbols, debug=False ):
    '''shared special processing'''
    
    dates = origData[ 'dates'     ]
    
    for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' , 'dividend'  ):
        if name not in origData:
            continue 
        origData[ name ][ numpy.isnan( origData[ name   ] ) ] = 0

    blockType   = blockName[0]
    dataId      = origData[ 'dataId'   ]

    opMode      = twkval.getenv( 'run_mode')
    
    if opMode not in ( 'dev', 'sim' ):
        assert( stratSymbols != None )
        
        nOrigData = {}
        origSymbols = numpy.array(origData[ 'symbols' ] )
        targetLen   = len( stratSymbols )
        tix, cix    = simutil.symbolIndex( baseSymbols=stratSymbols, newSymbols=origSymbols )

        shape = ( len( dates ), targetLen )
        
        for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' , 'dividend'  ):
            # realign
            if name not in origData:
                continue 
            nOrigData[ name ] = numpy.zeros( shape )
            nOrigData[ name ][ :, tix ] = origData[ name ][ :, cix ] 
    
        dates       = origData[ 'dates' ]
        origData    = nOrigData
    
        # special, trade block
        origData[ 'symbols'   ] = stratSymbols
        origData[ 'dates'     ] = dates
        
        adj         = origData[ 'adjclose' ]
        clos        = origData[ 'close'    ]
        volume      = origData[ 'volume'   ]
        unadjvolume = origData[ 'unadjvolume'   ]
        
    if blockType == 'Calib':
        if opMode in ( 'dev', 'sim' ):
            '''
            deal with NaN
            '''
            if 'NeedAddNaN' in params and params[ 'NeedAddNaN' ] :
                whenAddNaN  = params[ 'WhenAddNaN' ]
                for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' ):
                    origData[ name ] = addNaN.addNaN( origData[name], dates, whenAddNaN )
                    
            '''
            deal with delist
            '''            
            if 'NeedDelist' in params and params[ 'NeedDelist' ][0]:
                from meadow.lib.symbChangeDB import symbDB
                tradeDate   = twkval.getenv( 'run_tradeDate' )
                mask        = symbDB.flagListed( origData[ 'symbols' ], date=tradeDate )
                delpos      = numpy.where(numpy.array(mask)==False)[0]
                for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' ):
                    origData[name] = addNaN.dealNaN( origData[name], delpos)
                    
            '''
            deal with dont trade one day RNE 05/24/2013
            standard calibration block
            '''       
            adjHoles, badSymbols1, _adj = stratutil.applyBadTickerRules( 
                'adjclose', origData, params[ 'RemoveSymbolsRule'], debug=debug, 
            )
        
            if len( badSymbols1 ):
                logger.info( '\nBadsyms_adjclose %s\n%s\n' % ( 
                    'Following symbols are missing from adjclose', str( badSymbols1 ) ) 
                )
        
            closeHoles, badSymbols2, _clos = stratutil.applyBadTickerRules( 
                'close', origData, params[ 'RemoveSymbolsRule'], debug=debug,
            )
        
            if len( badSymbols2 ):
                logger.info(  '\nBadsyms_adjclose %s\n%s\n' % ( 
                    'Following symbols are missing from close',  str( badSymbols2 ) ) 
                ) 
        
            s1, s2  = set( badSymbols1 ), set( badSymbols2 )
            
            if ( s1 - s2 ) or (s2 - s1):
                logger.debug( 'different holes in adjclose = %d and close = %d' % ( len(s1), len(s2) ) )
                
            holes   = adjHoles * closeHoles
            adj     = numpy.array( origData[ 'adjclose' ] )[:, holes == False ]
            clos    = numpy.array( origData[ 'close'    ] )[:, holes == False ]
            volume  = numpy.array( origData[ 'volume'   ] )[:, holes == False ]
            symbols = numpy.array( origData[ 'symbols' ])[ closeHoles == False ]
            unadjvolume  = numpy.array( origData[ 'unadjvolume'   ] )[:, holes == False ]

        else: # for Trade, Update in sim-seed, sim-prod, trade-prod
            adj         = origData[ 'adjclose' ]
            clos        = origData[ 'close'    ]
            volume      = origData[ 'volume'   ]
            unadjvolume = origData[ 'unadjvolume'   ]
            symbols     = origData[ 'symbols'   ]
            
        _h1, adj = stratutil.applyPatchRules( 
            adj, 'adjclose', origData, params[ 'PatchRule'] 
        )
        
        _h2, clos = stratutil.applyPatchRules( 
            clos, 'close', origData, params[ 'PatchRule'] 
        )
        
        if len( numpy.where(adj[-1,:]==0)[0] ): # deal with zeros in adj and clos in sim-seed. some ticker may not trade for one day. RNE 05242013
            logger.debug( 'have %s zero(s) in yesterday(%s)  close prices' % ( len(numpy.where(adj[-1,:]==0)[0]), int(dates[-1]) ) )
            zero_end = numpy.where(adj[-1,:]==0)[0]
            adj[-1,zero_end]  = adj[-2,zero_end]
            clos[-1,zero_end] = clos[-2,zero_end]
            
    else: # for Trade, Update, etc
        adj         = origData[ 'adjclose' ]
        clos        = origData[ 'close'    ]
        volume      = origData[ 'volume'   ]
        unadjvolume = origData[ 'unadjvolume'   ]
        symbols     = origData[ 'symbols'   ]

    dataId  = stratutil.dataIdParts( 
        dataId, params, ( 'RemoveSymbolsRule', 'PatchRule', 'PostPatchRule' ) 
    )
    dataId          = list( dataId )
    
    #    print 'adj.shape =', adj.shape
    #    print 'adj =', sum( adj[-1,:] == 0 )
                
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logret  = numpy.log( adj[1:,:] ) - numpy.log( adj[:-1,:] )
    
    ''' lr check '''
        
    if opMode in ( 'dev', 'sim' ) and blockType == 'Calib':
        if opMode != 'sim':
            assert( not stratSymbols )
            
        logretcheck = params['LogretCheck']
        thread      = params['Thread']
        #logret, symbols, ix = ss.symbolSelection_zeros(logret, symbols, numpy.ceil( 0.05*logret[dates<20101231,:].shape[0] ) )
        _logret, symbols, ix = ss.symbolSelection_zerosNaN(logret[dates<logretcheck,:], symbols, thread )
        
        logret      = logret     [:, ix ]   
        adj         = adj        [:, ix ]
        clos        = clos       [:, ix ]
        volume      = volume     [:, ix ]
        unadjvolume = unadjvolume[:, ix ]
    
    rets = { 
        'logret'        : logret,
        
        'volume'        : volume        [1:, : ], 
        'dates'         : dates         [1:    ], 
        'close'         : clos          [1:, : ], 
        'adjclose'      : adj           [1:, : ],
        'unadjvolume'   : unadjvolume   [1:, : ],
        
        'symbols'       : symbols,
        'datalen'       : len( adj ),
        'dataId'        : dataId,
    }
        
    if 'dividend' in origData:
        dividend= numpy.array( origData[ 'dividend' ] )[:, holes == False ]
        rets[ 'dividend' ] = dividend  [1:, : ]

    if blockType == 'Calib':
        if 'PostPatchRule' in params:
            for name, ruleName in params[ 'PostPatchRule' ]:
                print 'PostPatchRule->', name
                _h3, rets[ name ] = stratutil.applyPatchRules( 
                    rets[ name ], name, rets, [ ruleName ], 
                )
        logger.debug( 'dataId = %s' % pprint.pformat( dataId ) )

    _mask0_nameTypes = {
         'rowMat'     : (),
         'colMat'     : ( 'volume', 'adjclose', 'close', 'unadjvolume', 'logret' ),
         'nochange'   : ( 'dates',  'dataId' ),
         'simpleList' : ( 'symbols', ),
    }

    from meadow.lib.symbChangeDB import symbDB

    if 'NeedDelist' in params and params[ 'NeedDelist' ][0]:
        tradeDate = cal.bizday( params[ 'NeedDelist' ][1], '-1b')
    else:
        tradeDate = twkval.getenv( 'run_tradeDate' )
    MIDlist     = rets[ 'symbols' ]
    mask        = symbDB.flagListed( MIDlist, date=tradeDate )
    masks       = { 'mask0': mask }
    allNameTypes= { 'mask0':_mask0_nameTypes }
    
    rets        = simutil.delColDictMat( rets=rets, masks=masks, allNameTypes=allNameTypes )
        
    logger.debug( 'block  = %s' % str( blockName ) )
    return rets

def sa3_specialProcessing( blockName, spRets, params, origData, debug=False ):
    '''dragon specific'''

    blockType = blockName[0]
    
    
    if blockType == 'Mrk2Mkt' or isTradeBlock( blockType ):
        return spRets

    opMode = twkval.getenv( 'run_mode')
    
    if opMode not in ('dev', 'sim' ):
        return spRets
        
    logret = spRets[ 'logret' ]
    window = params[ 'Window' ]
    dataId = spRets[ 'dataId' ]+['causalclip',str(spRets['dates'][-1])+'_'+str(spRets['logret'].shape[1])+'_'+str(window)]
    
    ''' save intermediate variables
    import meadow.lib.interm as interm
    i = interm.Intermediate()
    i.sa( 20121010, 'logret', logret )
    '''
    
    with pytables.PyTableMemoize( dataId=dataId, debug=False, compare=False ) as cdbh:
        clippedret = cdbh.cacheArray( 'clippedret', cclip.causalclip_n_m_parallel, X=logret, window=window )

    spRets[ 'clippedret'    ]   = numpy.array( clippedret[0] )
    spRets[ 'clippedret_n'  ]   = numpy.array( clippedret[1] )
    spRets[ 'clipscale'     ]   = numpy.array( clippedret[2] )
        
    return spRets

def reflect_self(x):
    return x



def sa_specialProcessing_pgs1( blockName, params, origData, stratSymbols, debug=False ):
    '''shared special processing'''
    
    dates = origData[ 'dates'     ]
    
    for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' , 'dividend'  ):
        if name not in origData:
            continue 
        origData[ name ][ numpy.isnan( origData[ name   ] ) ] = 0

    blockType   = blockName[0]
    dataId      = origData[ 'dataId'   ]
    
    opMode      = twkval.getenv( 'run_mode')
    
    if opMode not in ( 'dev', 'sim' ):
        assert( stratSymbols != None )
        
        nOrigData = {}
        origSymbols = numpy.array(origData[ 'symbols' ] )
        targetLen   = len( stratSymbols )
        tix, cix    = simutil.symbolIndex( baseSymbols=stratSymbols, newSymbols=origSymbols )

        shape = ( len( dates ), targetLen )
        
        for name in ( 'adjclose', 'close', 'volume', 'unadjvolume' , 'dividend'  ):
            # realign
            if name not in origData:
                continue 
            nOrigData[ name ] = numpy.zeros( shape )
            nOrigData[ name ][ :, tix ] = origData[ name ][ :, cix ] 
    
        dates       = origData[ 'dates' ]
        origData    = nOrigData
    
        # special, trade block
        origData[ 'symbols'   ] = stratSymbols
        origData[ 'dates'     ] = dates
        
        adj         = origData[ 'adjclose' ]
        clos        = origData[ 'close'    ]
        volume      = origData[ 'volume'   ]
        unadjvolume = origData[ 'unadjvolume'   ]
        
    if blockType == 'Calib':
        if opMode in ( 'dev', 'sim' ):
                
            # standard calibration block
            adjHoles, badSymbols1, _adj = stratutil.applyBadTickerRules( 
                'adjclose', origData, params[ 'RemoveSymbolsRule'], debug=debug, 
            )
        
            if len( badSymbols1 ):
                logger.info( '\nBadsyms_adjclose %s\n%s\n' % ( 
                    'Following symbols are missing from adjclose', str( badSymbols1 ) ) 
                )
        
            closeHoles, badSymbols2, _clos = stratutil.applyBadTickerRules( 
                'close', origData, params[ 'RemoveSymbolsRule'], debug=debug,
            )
        
            if len( badSymbols2 ):
                logger.info(  '\nBadsyms_adjclose %s\n%s\n' % ( 
                    'Following symbols are missing from close',  str( badSymbols2 ) ) 
                ) 
        
            s1, s2  = set( badSymbols1 ), set( badSymbols2 )
            
            if ( s1 - s2 ) or (s2 - s1):
                logger.debug( 'different holes in adjclose = %d and close = %d' % ( len(s1), len(s2) ) )
                
            holes   = adjHoles * closeHoles
            adj     = numpy.array( origData[ 'adjclose' ] )[:, holes == False ]
            clos    = numpy.array( origData[ 'close'    ] )[:, holes == False ]
            volume  = numpy.array( origData[ 'volume'   ] )[:, holes == False ]
            symbols = numpy.array( origData[ 'symbols' ])[ closeHoles == False ]
            unadjvolume  = numpy.array( origData[ 'unadjvolume'   ] )[:, holes == False ]

        else: # for Trade, Update in sim-seed, sim-prod, trade-prod
            adj         = origData[ 'adjclose' ]
            clos        = origData[ 'close'    ]
            volume      = origData[ 'volume'   ]
            unadjvolume = origData[ 'unadjvolume'   ]
            symbols     = origData[ 'symbols'   ]
            
        _h1, adj = stratutil.applyPatchRules( 
            adj, 'adjclose', origData, params[ 'PatchRule'] 
        )
    
        _h2, clos = stratutil.applyPatchRules( 
            clos, 'close', origData, params[ 'PatchRule'] 
        )
            
    else: # for Trade, Update, etc
        adj         = origData[ 'adjclose' ]
        clos        = origData[ 'close'    ]
        volume      = origData[ 'volume'   ]
        unadjvolume = origData[ 'unadjvolume'   ]
        symbols     = origData[ 'symbols'   ]

    dataId  = stratutil.dataIdParts( 
        dataId, params, ( 'RemoveSymbolsRule', 'PatchRule', 'PostPatchRule' ) 
    )
    dataId          = list( dataId )
    
    #    print 'adj.shape =', adj.shape
    #    print 'adj =', sum( adj[-1,:] == 0 )
                
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logret  = numpy.log( adj[1:,:] ) - numpy.log( adj[:-1,:] )
        logret  = numpy.vstack((numpy.empty((1,adj.shape[1])) * numpy.nan, logret))
    
    ''' lr check '''
        
    if opMode in ( 'dev', 'sim' ) and blockType == 'Calib':
        assert( not stratSymbols )

    rets = { 
        'logret'        : logret,
        
        'volume'        : volume        [:, : ], 
        'dates'         : dates         [:    ], 
        'close'         : clos          [:, : ], 
        'adjclose'      : adj           [:, : ],
        'unadjvolume'   : unadjvolume   [:, : ],
        
        'symbols'       : symbols,
        'datalen'       : len( adj ),
        'dataId'        : dataId,
    }
        
    if 'dividend' in origData:
        #dividend= numpy.array( origData[ 'dividend' ] )[:, holes == False ]   # This might be a potential problem.
        dividend= numpy.array( origData[ 'dividend' ] )
        rets[ 'dividend' ] = dividend  [:, : ]

    if blockType == 'Calib':
        if 'PostPatchRule' in params:
            for name, ruleName in params[ 'PostPatchRule' ]:
                print 'PostPatchRule->', name
                _h3, rets[ name ] = stratutil.applyPatchRules( 
                    rets[ name ], name, rets, [ ruleName ], 
                )
        logger.debug( 'dataId = %s' % pprint.pformat( dataId ) )

    logger.debug( 'block  = %s' % str( blockName ) )
    return rets


def sa_specialProcessing_pgs2( blockName, spRets, params, origData, debug=False):
    '''pegasus specific'''
            
    return spRets

