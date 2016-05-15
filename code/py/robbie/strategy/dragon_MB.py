import numpy
import scipy.stats

import meadow.lib.digest as digest
import meadow.tweak.value as twkval
import meadow.math.hankel.tib as tib
import meadow.lib.pytables as pytables
import meadow.strategy.util as stratutil
import meadow.strategy.base as strat_base
import meadow.math.cvxprog.bqpfhdit as bqp
import meadow.strategy.base_util as base_util
import meadow.strategy.base_trade as base_trade
import meadow.math.missing.fftreduce as fftreduce
import meadow.math.factor.expectedmax as expectedmax
import meadow.math.shrinkage.oracleshrink as oracleshrink

from   meadow.lib.logging import logger
import meadow.math.missing.symbol_selection as ss
import meadow.math.scaleestimator.causalclip as cclip

class Strategy( strat_base.BaseStrategyMultiBlock ):

    log_oneday_er   = 'oneday_expected_returns'
    log_twoday_er   = 'twoday_expected_returns'
    log_rmw         = 'close_position_ticker'
    log_Dynamic     = 'Dynamic_lcost_risklambda'
    log_origShares  = 'daily_origShares'
    log_tradeShares = 'daily_tradeShares'

    def initialize( self, opMode, specProcData, cachedCalib ):
        ''' '''
        calibName   = base_util.checkDatesAndSymbols( targetType='Calib', specProcData=specProcData )
        # dates       = specProcData[ calibName ][ 'dates'    ]
        symbols     = specProcData[ calibName ][ 'symbols'  ]
        typ         = specProcData[ calibName ][ 'symbology']
        #dates       = specProcData[ calibName ]['dates'][specProcData[ calibName ]['dates']>=20110101].tolist()
        if opMode in ( 'sim', 'dev' ):
            key = 'CheckCapital'
            if key not in cachedCalib:
                cachedCalib[ 'CheckCapital' ]  = 0

        if opMode == 'sim-seed':
            return
        
        from meadow.lib.symbChangeDB import symbDB
        
        tradeDate   = twkval.getenv( 'run_tradeDate' )
        if typ == 'MID':
            symbols = [ symbDB.MID2symb( MID, date=tradeDate ) for MID in symbols ]
        else:
            raise ValueError( 'Unknown symbology=%s' % typ )

        #symbols = specProcData[ 'symbols' ]
        logger.customHeader( self.log_rmw,['close_position_ticker']  )
        logger.customHeader( self.log_Dynamic, ['ntrades','lcost','risklambda','CheckCapital','firstUpdateBlock','SIM_CAP','SIMC'] )
        logger.customHeader( self.log_oneday_er, symbols )
        logger.customHeader( self.log_twoday_er, symbols )
        logger.customHeader( self.log_origShares, symbols )
        logger.customHeader( self.log_tradeShares, symbols )

    def modeConversion( self, strategyName, cachedCalib, modeFrom, modeTo ):
        ''' will be used to create the zero-day trade-prod cachedCalib '''

        if modeFrom != 'sim' or modeTo != 'zero-trade-prod':
            raise ValueError( 'Cannot handle %s' % str( ( modeFrom, modeTo ) ) )

#        cachedCalib['RiskLambda'] = 0.5
#        cachedCalib['LCost']      = 0.06
        import copy
        return copy.deepcopy( cachedCalib )

    def getData( self, modelName, params ):
        ''' '''
        
        import meadow.strategy.base_getdata as base_getdata 
        scheduleNames = params['Schedule']
                
        ret = base_getdata.sa_getMergedMultiBlock(
            modelName     = modelName, 
            params        = params, 
            debug         = False, 
            scheduleNames = scheduleNames, 
            includeDivs   = False)
                
        ret[ 'Schedule' ] = scheduleNames
        return ret 

    def specialProcessing( self, modelName, params, origData, stratSymbols ):
        ''' '''
        
        import meadow.strategy.base_specialprocessing as base_sp
         
        debug   = False
        spData  = {}
                
        for blockName, blockVals in origData.iteritems():
            blockType = blockName[0]
            if blockType in ( 'Calib', 'Trade', 'Update', 'Mrk2Mkt' ): 

                spRets = base_sp.sa_specialProcessing( 
                                        blockName    = blockName, 
                                        params       = params, 
                                        origData     = blockVals, 
                                        stratSymbols = stratSymbols )
                
                spData[ blockName ] = base_sp.sa3_specialProcessing( 
                                                blockName       = blockName, 
                                                spRets          = spRets, 
                                                params          = params, 
                                                origData        = blockVals, 
                                                debug           = debug )

                spData[ blockName ][ 'symbology' ] = blockVals[ 'symbology' ]
            else:
                logger.debug( '%s is not special-processed' % str( blockName ) )

        spData[ 'Schedule' ] = origData[ 'Schedule' ]
        return spData

    def incrSpecialProcessing( self, blockName, params, calibData, cachedCalib ):
        ''' default incremental special processing '''
        window          = params[ 'Window' ]
        clips           = 'clips'
        origSpecs       = cachedCalib[ 'OriginSpec'][0]
        
        calibBlockName  = stratutil.findBlock( keys=calibData.keys(), typ='Calib' )

        if origSpecs =='sim':
            logret = calibData[ blockName ][ 'logret'   ]
                        
            incr, incr2    = {}, {}
            incr['clippedret'], incr['clippedret_n'], incr['clipscale']    = cclip.causalclip_n_Incr_m( X=logret[:-1,:], window=window )
            incr2['clippedret'], incr2['clippedret_n'], incr2['clipscale'] = cclip.causalclip_n_Incr_m( X=logret, window=window )
            
            for name in  ( 'clippedret',  'clippedret_n', 'clipscale' ):
                cachedCalib[ clips ][ name ]   = numpy.concatenate( 
                                                    ( cachedCalib[ clips ][ name ], incr[ name ][None,:], incr2[ name ][None,:]) )
                
                calibData[ calibBlockName ][ name ] = cachedCalib[ clips ][ name ]
                
        elif origSpecs in ( 'trade-prod', 'sim-prod' ):                        
            logret      = calibData[ blockName ][ 'logret'   ]
            incr        = {}
            incr['clippedret'], incr['clippedret_n'], incr['clipscale'] = cclip.causalclip_n_Incr_m( X=logret, window=window )
             
            for name in  ( 'clippedret',  'clippedret_n', 'clipscale' ):
                cachedCalib[ clips ][ name ]   = numpy.concatenate( (cachedCalib[ clips ][ name ], incr[ name ][None,:]) )
                calibData[ calibBlockName ][ name ] = cachedCalib[ clips ][ name ]

        else:
            raise ValueError( 'Unknown origSpecs=%s' % origSpecs )
        
        return  cachedCalib

    def updateCachedCalibsForIncrSpecialProcessing(self, params, calibData, cachedCalib ): 
        ''' update data for the incremental special processing '''
        clips = 'clips'
        for ( blockType,  _blockSpecs ), val in calibData.iteritems():
            if blockType == 'Calib':
                cachedCalib[ clips ] = {}
                for name in  ( 'clippedret',  'clippedret_n', 'clipscale' ):
                    cachedCalib[ clips ][ name ] = val[ name ]
        # verify
        if clips not in cachedCalib:
            raise ValueError( 'no clips!' )
         
        for name in  ( 'clippedret',  'clippedret_n', 'clipscale' ):
            if name not in cachedCalib[ clips ]:
                raise ValueError( 'no %s in clips!' % name )

        return  cachedCalib
    
    def calibrate( self, blockName, params, spparams, calibData, cachedCalib, auxParams, tradeParams, systemState ):
        '''
        returns amount traded
        '''
        blockType, _blockSpecs = blockName
        
        if blockType == 'Calib':
            return self.calibrateSOD( 
                            blockName   = blockName, 
                            params      = params,
                            spparams    = spparams, 
                            calibData   = calibData, 
                            cachedCalib = cachedCalib, 
                            auxParams   = auxParams, 
                            tradeParams = tradeParams,
                            systemState = systemState, )
        
        elif blockType == 'Update':
            return self.calibrateUpdate( 
                            blockName   = blockName, 
                            params      = params, 
                            calibData   = calibData, 
                            cachedCalib = cachedCalib, 
                            auxParams   = auxParams, 
                            tradeParams = tradeParams,
                            systemState = systemState, )

        else:
            raise ValueError( 'Unknown blockType = %s' % str( blockType ) )
        
    def calibrateSOD( self, blockName, params, calibData, cachedCalib, auxParams, tradeParams, systemState ): 

        compareCached   = params.get( 'CompareCached', False )
        # TagName           = params[ 'TagName' ]
        
        blockData       = calibData[ blockName ]

        logret          = blockData[ 'logret'   ]
        clippedret_n_all= blockData[ 'clippedret_n'   ]
        dates           = blockData[ 'dates'    ]
        volume_all      = blockData[ 'volume'   ]
        unadjvolume_all = blockData[ 'unadjvolume'   ]
        cprice_all      = blockData[ 'close'    ]
        adjclose        = blockData[ 'adjclose' ]
        symbols         = blockData[ 'symbols'  ]
        
        ioffset         = params[ 'InitialOffset' ]
        pos             = cachedCalib.get( 'pos',       [] )
        pos_zero        = cachedCalib.get( 'pos_zero',  [] )
        
        selectionDateIx = stratutil.calendarCount( params[ 'CovRecomputeTrgr' ], dates, ioffset, 'date' )  
        selectionDataId = blockData[ 'dataId' ] + [ 'selection',str(selectionDateIx) ] 
        with pytables.PyTableMemoize( dataId=selectionDataId, debug=False, compare=compareCached ) as cdbh:    
            pos,pos_zero = cdbh.cacheTuple(  
                            stratutil.conv2D( ('pos','pos_zero') ), 
                            ss.symbolSelection_dolvol, p0=pos, s0=pos_zero, dates=dates, 
                            symbols=symbols, price=cprice_all, volume=unadjvolume_all, 
                            logret=clippedret_n_all, thread=0.02, cp=10, adv=5e6, days=90, flag=True )
        ps = pos_zero

        clippedret_n = clippedret_n_all[:,ps]
        cprice       = cprice_all[:,ps]
        unadjvolume  = unadjvolume_all[:,ps]
        
        #lastCalibDate = str(dates[-1])
        covDateIx     = stratutil.calendarCount( params[ 'CovRecomputeTrgr' ], dates, ioffset, 'date' )        
        covDataId     = blockData[ 'dataId' ] + [ 'covMat' , str(covDateIx) + '_' + str(len(ps)) ]
                    
        with pytables.PyTableMemoize( dataId=covDataId, debug=False, compare=compareCached ) as cdbh:
            covMat, _a  = cdbh.cacheTuple( stratutil.conv2D( ( 'covMat', 'a' ) ), oracleshrink.oracleShrink, x=clippedret_n.T )

        factorCount = params[ 'FactorCount' ]
        emiterCount = params[ 'EMIterCount' ]
        shrinkage   = params[ 'Shrinkage'   ]
        
        factorEMId   = blockData[ 'dataId' ] + [ 'emic_' + str(emiterCount) + '_factors_' + str(factorCount)+'_sk_' + str(shrinkage), str(covDateIx) + '_' + str(len(ps)) ]
        #factorEMId   = blockData[ 'dataId' ] + [ 'emic_' + str(emiterCount), 'factors_' + str(factorCount),'sk_' + str(shrinkage), str(covDateIx) + '_' + str(len(p)) ]
        with pytables.PyTableMemoize( dataId=factorEMId, debug=False, compare=compareCached ) as cdbh:
            D0,V0   = expectedmax.guesser_n( C=covMat, d=factorCount )
            '''
            import meadow.lib.interm as interm
            i = interm.Intermediate()
            i.sa( lastCalibDate, 'D0', D0 )
            i.sa( lastCalibDate, 'V0', V0 )
            i.sa( lastCalibDate, 'covMat', covMat )
            '''
            D1,V1   = cdbh.cacheTuple( stratutil.conv2D( ( 'D1', 'V1' ) ), expectedmax.factorEM, D=D0, V=V0, C=covMat, nit=emiterCount, sk=shrinkage )
        
        lambd       = params[ 'Lambda'      ]
        irLen       = params[ 'IRLength'    ]
        polesCount  = params[ 'PolesCount'  ]
        adv     = numpy.mean(cprice[-90:] * unadjvolume[-90:], 0 )
        ap      = numpy.mean(cprice[-90:],0)
        rmw = numpy.zeros([len(ps),1])
        rmw[adv < 1e6  ] = 1
        rmw[ap  < 10   ] = 1

        if cachedCalib[ 'FirstTime' ] == True:
            pos1, _pos_zero1 = ss.symbolSelection_dolvol( 
                                    p0=[], s0=[], 
                                    dates=dates, symbols=symbols, price=cprice_all, volume=unadjvolume_all, 
                                    logret=clippedret_n_all, thread=0.02, cp=10, adv=1e6, days=90, flag=True )
        
            # this is our static data. will be pre-computed 
            tibDateIx   = 'static'
            tibDataId   = blockData[ 'dataId' ] + [ 'tib_results_hrls', 'lambd=%s' % digest.digest( lambd, 'md5str' ), str( tibDateIx ) ]
            with pytables.PyTableMemoize( dataId=tibDataId, debug=False, compare=compareCached ) as cdbh:            
                tibCA, tibhA = cdbh.cacheTuple( ( ( 'tibCA', ) , (  'tibhA', ) ), 
                    tib.computeTibRmParallel, lambd=lambd, logret=clippedret_n_all[numpy.where(dates<=20061231)[0][:,None],pos1], irLen=irLen )
                
            _C, h = numpy.mean( tibCA, 0), numpy.mean( tibhA, 0 )
                
            reduceId   = blockData[ 'dataId' ] + [ 'reduce_lambda_polesCount_%s' % polesCount, str(tibDateIx) ]
            with pytables.PyTableMemoize( dataId=reduceId, debug=False, compare=compareCached ) as cdbh:
                reducedLambda = cdbh.cacheArray( 'reducedLambda' , 
                    fftreduce.fftreduce, h=h, num=polesCount )

        rmwix = ( rmw==0 ) # only those explogret0 and explogret1 will be calculate
        
        if cachedCalib[ 'FirstTime' ] == True:
            risklambda  =  params[ 'RiskLambda' ]
            lcost       =  params[ 'LCost'      ]             
            zDataId     = blockData[ 'dataId' ] + [ 'tibrls_z_mat_kernel','reducedlambd=%s' % digest.digest( reducedLambda, 'md5str' ), str(tibDateIx) +'_'+ str(len(ps)) ]
            
            with pytables.PyTableMemoize( dataId=zDataId, debug=False, compare=compareCached ) as cdbh:
                
                # parallelized version of tibrls_z_mat_kernel_rmw
                _explogret0, _C0, z0, _yhat0, _h0, _v0, p0, R0, M0, N0, U0 = cdbh.cacheTuple( 
                                stratutil.conv2D( ( 'explogret0', 'C0', 'z0', 'yhat0', 'h0', 'v0', 'p0', 'R0', 'M0', 'N0', 'U0' ) ), 
                                tib.tibrls_zRm_mat_rmw_par, 
                                    reducedLambda=reducedLambda, logret=clippedret_n_all, irLen=irLen, rmwix=rmwix, average=params[ 'Average_C'  ], pos = ps )
                
                M0, N0, U0 = tib.dense2sparse_mat( M0 ), tib.dense2sparse_mat( N0 ), tib.dense2sparse_mat( U0 )
                
            cachedCalib[ 'TibRls'       ] = ( z0, p0, R0, M0, N0, U0 )
            cachedCalib[ 'RiskLambda' ]  = risklambda
            cachedCalib[ 'LCost'      ]  = lcost
        else:
            try:
                if cachedCalib[ 'OriginSpec'][0]=='sim':
                    args, _explogret0 = tib.incr2TibUpdate( cachedCalib=cachedCalib, clippedret_n=clippedret_n_all, rmwix=rmwix, params=params, pos=ps )
                    cachedCalib[ 'TibRls'       ] = args
                elif  cachedCalib[ 'OriginSpec'][0]=='sim-seed':   
                    args, _explogret0 = tib.incrTibUpdate( cachedCalib=cachedCalib, clippedret_n=clippedret_n_all, rmwix=rmwix, params=params, pos=ps )
                    cachedCalib[ 'TibRls'       ] = args 
            except :
                args, _explogret0 = tib.incrTibUpdate( cachedCalib=cachedCalib, clippedret_n=clippedret_n_all, rmwix=rmwix, params=params, pos=ps )
                cachedCalib[ 'TibRls'       ] = args            
        
        shares = None
        sharesInfo = { 
            'TradeSymbols'  : symbols,
            'TradeShares'   : shares,
        }
        
        cachedCalib[ 'rmwix'    ] = rmwix
        cachedCalib[ 'rmw'      ] = rmw  
        cachedCalib[ 'pos'      ] = pos
        cachedCalib[ 'pos_zero' ] = pos_zero
        cachedCalib[ 'adv'      ] = adv
        cachedCalib[ 'ap'       ] = ap 
        cachedCalib[ 'D1,V1'    ] = D1,V1
        
        return cachedCalib, sharesInfo

    def calibrateUpdate( self, blockName, params, calibData, cachedCalib, auxParams, tradeParams, systemState ): 
        # ( 'Update',( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_352'      ), 
        compareCached = params.get( 'CompareCached', False )
        
        _blockType,   blockSpecs = blockName
        _updateSpecs, calibSpecs = blockSpecs

        opMode        = twkval.getenv( 'run_mode')
        oldCalibData  = calibData[ ( 'Calib', calibSpecs ) ]        
        
        if opMode in ('sim-prod', 'trade-prod'):
            symbols       = cachedCalib[ 'symbols' ]
            oldClipScale  = cachedCalib[ 'clips' ][ 'clipscale'     ] 
            clippedret_n  = cachedCalib[ 'clips' ][ 'clippedret_n'  ]
        else:
            symbols       = oldCalibData[ 'symbols'     ]
            oldClipScale  = oldCalibData[ 'clipscale'   ]             
            clippedret_n  = oldCalibData[ 'clippedret_n']
        
        blockData     = calibData[ blockName        ]
        dates         = auxParams[ 'dates'          ]
                
        adjclose    = blockData[ 'adjclose' ].copy()
        zeroix      = ( adjclose[-1,:] == 0 )
        adjclose[-1, zeroix ] = adjclose[-2, zeroix ]
        
        newzeroix   = ( adjclose[-1,:] == 0 )
        if numpy.any( newzeroix  ) and numpy.sum( newzeroix  ):
            msg = 'still have holes!!! %s' % numpy.sum( newzeroix )
            logger.error( msg )
            raise ValueError( msg )
        
        norm_975 = scipy.stats.norm.ppf(0.975,0,1)
        new_logret  = numpy.diff(numpy.log(adjclose[-2:,:]),axis=0)/oldClipScale[-1,:]
        new_logret[numpy.where(new_logret>norm_975)] = norm_975
        new_logret[numpy.where(new_logret<-norm_975)] = -norm_975
        
        clippedret_n_all= numpy.concatenate( ( clippedret_n, new_logret ) )
        
        rmwix       = cachedCalib[ 'rmwix'    ]   
        pos_zero    = cachedCalib[ 'pos_zero' ]
        _args, explogret0 = tib.incrTibUpdate( cachedCalib=cachedCalib, clippedret_n=clippedret_n_all, rmwix=rmwix, params=params, pos=pos_zero )
            
        currPort    = cachedCalib[ 'SODPort'    ]
        risklambda  = cachedCalib[ 'RiskLambda' ]
        lcost       = cachedCalib[ 'LCost'      ]     

        qcost       = params[ 'QCost'      ]
        initweight_all  = currPort
        simc        = params['SimCapital']
        capital     = params['Capital']
        leverage    = params['Leverage']
        n           = len( explogret0 )
        tpb         = params['liquidity_TPB']
        tubCp       = params['Concentrate']
        times       = params['Times']
        rampUpCutoff= params[ 'RampUpCutoff' ]

        initweight  = initweight_all[pos_zero] * adjclose[-1,pos_zero] / (( leverage * capital ) / simc)
        adv         = cachedCalib[ 'adv' ]
        tub     = adv * 0.01 * tpb * simc / ( leverage * capital )
        
        pub     =  4 * tub - initweight
        plb     = -4 * tub - initweight
        
        # if all(dates<=20110131) :
        if all( numpy.array(dates) <= rampUpCutoff ):
            ub      = numpy.minimum(pub, tub)
            lb      = numpy.maximum(plb,-tub)
        else:
            ub      = numpy.minimum( numpy.minimum(pub, tub), 
                                     tubCp*numpy.sum(numpy.absolute(initweight))*numpy.ones(n)- initweight)
            lb      = numpy.maximum( numpy.maximum(plb,-tub),
                                    -tubCp*numpy.sum(numpy.absolute(initweight))*numpy.ones(n)- initweight)
        
        check = cachedCalib['Check'] 

        D1,V1 = cachedCalib[ 'D1,V1' ]
        rmw   = cachedCalib[ 'rmw' ]
        digArgs = digest.digest( 
                ( initweight, D1, V1, risklambda, numpy.round(explogret0,8), lcost, qcost, lb, ub, 1, rmw, simc ), 
                'md5str' )
        
        #%logger.debug( '-> digArgs %s %s' % ( exploegret0_digest, exploegret1_digest ) )
                      
        bqpDataId   = oldCalibData[ 'dataId' ] + [ 'bqp_results', str(dates[-1]),'input=%s' % digArgs  ]
        with pytables.PyTableMemoize( dataId=bqpDataId, debug=False, compare=compareCached ) as cdbh:            
            w_bqp,error,count,trades,ntrades,weight,cap,check,lcost,risklambda  = cdbh.cacheTuple( 
                stratutil.conv2D( ( 'w_bqp', 'error', 'count', 'trades', 'ntrades', 
                                    'weight', 'cap', 'check', 'lcost', 'risklambda', ) ), 
                bqp.bqpfhditSDynamic_rmw, initweight=initweight, D1=D1, V1=V1, risklambda=risklambda, explogret0=explogret0,
                 lcost=lcost, qcost=qcost, lb=lb, ub=ub, s=1, rmw=rmw, n=n, check=check, simc=simc, dates=dates)
        
        #logger.debug( 'DONE -> digArgs' )
        
        #cachedCalib[ 'CurrPort'   ]  = weight[:,0]/adjclose[-1]
        cachedCalib[ 'Check'      ]  = check
        cachedCalib[ 'RiskLambda' ]  = risklambda
        cachedCalib[ 'LCost'      ]  = lcost
        tradeShares     = numpy.zeros( len( symbols ) )
        tradeShares[ pos_zero ]= trades.flatten()/adjclose[-1,pos_zero] * ( leverage * capital ) / simc        
        tradeShares[ pos_zero ]= base_trade.roundShares(tradeShares[pos_zero])
        
        tradeShares     = base_trade.splitShares( tradeParams , blockName, shares = tradeShares, cachedCalib=cachedCalib )
        
        sharesInfo= { 
         'TradeShares' : tradeShares,
         'TradeSymbols': symbols,
         }
        
        #logger.customWrite( self.log_simcap, dates[-1], numpy.array([cap, simc]))       
        logger.customWrite( self.log_Dynamic, dates[-1], numpy.array([ntrades,lcost, risklambda,check,cap,simc]))          
        logger.customWrite( self.log_oneday_er, dates[-1], explogret0)
                
        return cachedCalib, sharesInfo

    def removeDelistedSymbols( self, tradeDate, cachedCalib ):
        from   meadow.lib.symbChangeDB import symbDB
        import meadow.sim.util as simutil

        _mask0_nameTypes = {

             'rowMat'     : ( ),
             'colMat'     : ( 'clippedret','clipscale','clippedret_n'),
             'nochange'   : ( 'adv', 'D1,V1', 
                              'FirstTime', 'LCost', 'RiskLambda', 'ap', 'rmwix', 
                              'Check', 'OriginSpec', 
                              'TradeIndex', 'rmw', 
                              'ModelSignature',
                              'restricted-notrade','restricted-noshort','restricted-freeze' ),
             'simpleVec'  : ( 'symbols', 'PortSymbols', 'CurrPort', 'SODPort' ),
             'dict'       : ( 'clips',      ),
             'tuple'      : ( 'TibRls','TibRlsLead'    ),
             'empty'      : ( ),
             'vecCompress': ( ),
             'tradeIx'    : ( 'pos', 'pos_zero' ),
        }

        _mask1_nameTypes = {
             'vecCompress'   : ( 'pos', ),
        }

        _mask2_nameTypes = {
             'vecCompress'   : ( 'pos_zero', ),
             '2DCompress'    : ( 'rmw', ),
        }
        
        allNameTypes = {
            'mask0':_mask0_nameTypes,
            'mask1':_mask1_nameTypes,
            'mask2':_mask2_nameTypes,
        }
        
        MIDlist         = cachedCalib['symbols']
        mask            = symbDB.flagListed( MIDlist, date=tradeDate )
#        mask[0]=False
#        mask[1]=False

#        rmMIDlist_All   = [ 5776, 1796, 3427, 5521, 1859, 5831, 4735, 5163, 3747, 5902, 2500, 5705, 1291, 3684, 1795, 4259, 2948, 2597, 3402 ] 
#        # MIDs (CEF) need to be remove from the universe
#        rmMIDlist       = numpy.intersect1d( MIDlist, rmMIDlist_All )
#        for k in range(len(rmMIDlist)):
#            mask[ numpy.where(MIDlist == rmMIDlist[k])[0] ] = False
        
        mask_arr        = numpy.array( mask )        
        pos             = cachedCalib['pos']
        pos_zero        = cachedCalib['pos_zero']
        mask_pos        = mask_arr[ pos ]
        mask_pos_zero   = mask_arr[ pos_zero ]
        if mask_arr.shape[0] == sum(mask_arr):
            logger.debug('No delist today %s' % str(tradeDate))
        else:
            if mask_pos_zero.shape[0] == sum(mask_pos_zero):
                logger.debug('Delisted non-tradable symbol(s) today %s' % str(tradeDate))
            else:
                logger.debug('Delisted tradable symbol(s) today %s' % str(tradeDate))
        masks = {
            'mask0': mask,
            'mask1': mask_pos,
            'mask2': mask_pos_zero,
        }
        
        cachedCalib = simutil.delColDictMat( rets=cachedCalib, masks=masks, allNameTypes=allNameTypes, handleUnknown=True, debug=False )

        return cachedCalib
    
    def removeDelistedSymbolsCD( self, tradeDate, calibData ):
        from   meadow.lib.symbChangeDB import symbDB
        import meadow.sim.util as simutil

        _mask0_nameTypes = {

             'rowMat'     : ( ),
             'colMat'     : ( 'clippedret','clipscale','clippedret_n','volume','unadjvolume','close','adjclose','logret'),
             'nochange'   : ( 'dataId', 'datalen', 'dates', 'symbology'),
             'simpleVec'  : ( 'symbols'),
             'dict'       : ( ),
             'tuple'      : ( ),
             'empty'      : ( ),
             'vecCompress': ( ),
             'tradeIx'    : ( ),
        }
        
        allNameTypes = {
            'mask0':_mask0_nameTypes,
        }
        
        MIDlist         = calibData['symbols']
        mask            = symbDB.flagListed( MIDlist, date=tradeDate )
        mask_arr        = numpy.array( mask )        


        masks = {
            'mask0': mask,
        }
        
        calibData = simutil.delColDictMat( rets=calibData, masks=masks, allNameTypes=allNameTypes, handleUnknown=True, debug=False )

        return calibData