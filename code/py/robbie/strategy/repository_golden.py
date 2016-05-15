import numpy

import meadow.lib.calendar as cal
import meadow.lib.param as libparam
import meadow.strategy.util as stratutil
import meadow.strategy.repository_util as reputil
import meadow.strategy.pegasus_prod as pegasus_prod
import meadow.strategy.dragon_MB_MP_C as dragon_MB_MP_C

def init():
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
                
                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
                
                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
                
            ) 
        },
        
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
            'WhenAddNaN'        : 20070103,
            'NeedAddNaN'        : False,
            'NeedDelist'        : (False,0),
            # 'LogretCheck'       : 20130417,
            'Thread'            : 0.05,
            'Window'            : 500,
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 50,
            'PolesCount'        : 8, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 0.5,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 5e6,
            'Leverage'          : 4,
            'liquidity_TPB'     : 0.2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20130331,
            'Poles'             : libparam.getParam( locator = 'poles=reduced_count=8_period=2007-2010_500', allowEmpty=True ),
            #'Poles'             : libparam.getParam( locator = 'poles=reduced_count=12_period=2002-2006', allowEmpty=True ),
            'Average_C'         : 'norm',
            #'Average_C'         : 'mean'
            'Rmean'             : True,
            'zshift'            : False,
            'CovCut'            : 1000,
            'Del-rmw'           : False,
            'Rm_price'          : 10,
            'Rm_dolvol'         : 1e6,
            'AlphaEM'           : -1,
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20130318, 
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            'TradeSplitRuleArgs': 3,            
        },
              
        'Execution' : {
            'AllocationSchema'  :   'CASH',
            'ProductType'       :   'CASH',
        },
              
    }
    stratutil.amend( params, 
            'GetData', { 
                'FirstTradeDate' : cal.bizday( params[ 'Run' ][ 'InitialOffset' ], '-5b' ), 
            })

    stratutil.amend( params, 
        'SpecialProcessing', {
                'LogretCheck' : cal.bizday( params[ 'Run' ][ 'InitialOffset' ], '-1b' ), 
            })
    
    stratutil.amend( params, 
            'CalibParams',  {
                'RampUpCutoff' : cal.bizday( params[ 'Run' ][ 'InitialOffset' ], '+20b' ), 
            })    
    reputil.setStrategy( 'GOLDEN_0', dragon_MB_MP_C.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'HYUS001',
            
            'StartDate'     : 20080102,
            'FirstTradeDate': 20130313,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),

                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
                
                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
                
                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
                                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),                
            ) 
        },
              
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_VOID'   ],
            'PatchRule'         : [ 'PATCH_VOID' ],
            'PostPatchRule'     : [ ( 'logret', 'PATCH_CONVERT_INFS') ],
            'NeedDelist'        : (False,0),
        },        

        'CalibParams' : {
            'c'       : 0.5,
            'd'       : 8.75e-5,
            'clambda' : 0.1,
            'tau'     : 0.97,
            'tail'      : 0.23,
            'sh'        : 0.01,
            'hedge_max' : 800,
            'capital_scalar' : 49.914364989308517,
            'totalcapital'   : 13.5e6,
            'constraintor' : 1,
            'rbcontroller' : 1,
            'kickout_price'  : 6,
            'kickout_volume' : 0.5e6,
            'letin_price'    : 10,
            'letin_volume'   : 1e6,
            'tib_xwindow'    : 250,
            'tib_k'             : 2,
            'poles'          : numpy.append(numpy.zeros((1,2)), numpy.cos(numpy.pi * numpy.array(range(1,6, 2))/6)*0.001 + 0.999).reshape((-1,1)),
            'cov_xwindow'     : 750,
            'cov_k'             : 2,
            'factor_number'  : 100,
            'yield_maxflat_lambda'  : 0.97,
            'yield_maxflat_d': 3,
            'yield_distribution_window' : 250,
            'sigmoid_alpha'     : 200,
            'holding_constraint' : 0.04,
            'trading_constraint' : 0.01,
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20130320,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            'TradeSplitRuleArgs': 3,       
        },
              
        'Execution' : {
            'AllocationSchema'  :   'CASH',
            'ProductType'       :   'CASH',
        },
              
        'Tweaks' : {
            'report_useMrk2Mrkt' : 'NaN_case',
        },
              
    }    
    reputil.setStrategy( 'GOLDEN_1', pegasus_prod.Strategy(), params )
