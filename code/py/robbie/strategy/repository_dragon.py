'''
global repository
'''

import numpy
import datetime

import meadow.lib.param as libparam
import robbie.strategy.util as stratutil
import meadow.strategy.repository_util as reputil

import meadow.strategy.dragon_MB as dragon_MB
import meadow.strategy.dragon_MB_MP as dragon_MB_MP
import meadow.strategy.dragon_MB_mid as dragon_MB_mid
import meadow.strategy.dragon_MB_MP_C as dragon_MB_MP_C
import meadow.strategy.dragon_MB_MP_shift as dragon_MB_MP_shift

def init():


    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20060705,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),
                
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_358'        ),
                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
#                ( 'Update',( ( 'STS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_356'      ),
#                
#                ( 'Trade', ( ( 'STS', '0' ),                ), 'nxc_lasttrade_356'      ),
                
            ) 
        },
        
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'Average_C'         : 'norm',
            'RampUpCutoff'      : 20110131,
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : datetime.datetime(2011,1,1),
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Once',
            'TradeSplitRuleArgs': 1,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V4', dragon_MB.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20060705,
            'FirstTradeDate': 20101230,
            
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
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20110131,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate',
            'TradeSplitRuleArgs': 3,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V5', dragon_MB.Strategy(), params )
    
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20101230,
            
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
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20110131,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            'TradeSplitRuleArgs': 3,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_Run', dragon_MB.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20130130,
            
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
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20130231,
            'Poles'             : libparam.getParam( locator = 'poles=reduced_count=12_period=2003-2006', allowEmpty=True ),
            'Average_C'         : 'norm',
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20130207,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            'TradeSplitRuleArgs': 3,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_Prod_1', dragon_MB.Strategy(), params )
    
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001_T2118',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20101230,
            #'FirstTradeDate': 20130227,
            
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
            'NeedAddNaN'        : True,
            'NeedDelist'        : (False,0),
            'LogretCheck'       : 20101230,
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
            'RampUpCutoff'      : 20110131,
            #'RampUpCutoff'      : 20130331,
            'Poles'             : libparam.getParam( locator = 'poles=reduced_count=8_period=2007-2010_2161_500_Rm', allowEmpty=True ),
            #'Poles'             : libparam.getParam( locator = 'poles=reduced_count=12_period=2002-2006', allowEmpty=True ),
            'Average_C'         : 'norm',
            #'Average_C'         : 'mean'
            'Rmean'             : True,
            'zshift'            : False,
            'CovCut'            : 1000,
            'Del-rmw'           : True,
            'Rm_price'          : 10,
            'Rm_dolvol'         : 1e6,
            'AlphaEM'           : 0.5,
             
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                #'InitialOffset' : 20130301,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            #'TradeSplitRule'    : 'Once',
            'TradeSplitRuleArgs': 3,            
        },
              
        'Execution' : {
            'AllocationSchema'  :   'CASH',
            'ProductType'       :   'CASH',
        },
              
    }    
    reputil.setStrategy( 'DRAGON_Prod_dev', dragon_MB_MP_C.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001_T2118',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20101230,
            #'FirstTradeDate': 20130227,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
                
#                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-352' ),
#                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_353'        ),
#                
#                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-353' ),
#                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_354'        ),                
                                
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
            'NeedAddNaN'        : True,
            'NeedDelist'        : (False,0),
            'LogretCheck'       : 20101230,
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
            'RampUpCutoff'      : 20110131,
            #'RampUpCutoff'      : 20130331,
            'Poles'             : libparam.getParam( locator = 'poles=reduced_count=8_period=2007-2010_2161_500_Rm', allowEmpty=True ),
            #'Poles'             : libparam.getParam( locator = 'poles=reduced_count=12_period=2002-2006', allowEmpty=True ),
            'Average_C'         : 'norm',
            #'Average_C'         : 'mean'
            'Rmean'             : True,
            'zshift'            : False,
            'CovCut'            : 1000,
            'Del-rmw'           : True,
            'Rm_price'          : 10,
            'Rm_dolvol'         : 1e6,
            'AlphaEM'           : 0.5,
             
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                #'InitialOffset' : 20130301,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
            #'TradeSplitRule'    : 'Once',
            'TradeSplitRuleArgs': 3,            
        },
              
        'Execution' : {
            'AllocationSchema'  :   'CASH',
            'ProductType'       :   'CASH',
        },
              
    }    
    reputil.setStrategy( 'DRAGON_Prod_dev5', dragon_MB_MP_C.Strategy(), params )
    
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20130417,
            
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
            #'NeedDelist'        : (True,20130601), # same value with initial date
            'NeedDelist'        : (False,0),
            'LogretCheck'       : 20130417,
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
            'Del-rmw'           : True,
            'Rm_price'          : 10,
            'Rm_dolvol'         : 1e6,
            'AlphaEM'           : 0.5,
            'Mrk2Mkt_TJ'        : True,
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20130424,
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
    reputil.setStrategy( 'DRAGON_Prod_2', dragon_MB_MP_C.Strategy(), params )
    
    params = stratutil.replicate( params )
    stratutil.amend( params, 
        'CalibParams', {
            'Capital'           : 5e6,
            'Leverage'          : 4,
    })

    stratutil.amend( params, 
        'Execution', {
            'AllocationSchema'  :   'CASH',
            'ProductType'       :   'CASH',
    } )
    reputil.setStrategy( 'EQ_US_CSH', dragon_MB_MP_C.Strategy(), params )

    params = stratutil.replicate( params )
    stratutil.amend( params, 
        'Execution', {
            'AllocationSchema'  :   'SWAP',
            'ProductType'       :   'SWAP',
    } )
    params[ 'CalibParams' ][ 'RampUpCutoff'] = 20130522
    reputil.setStrategy( 'EQ_US_SW_TEST', dragon_MB_MP_C.Strategy(), params )

    params = stratutil.replicate( params )
    stratutil.amend( params, 
        'Execution', {
            'AllocationSchema'  :   'SWAP',
            'ProductType'       :   'SWAP',
    } )
    reputil.setStrategy( 'EQ_US_CFD', dragon_MB_MP_C.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20060705,
            'FirstTradeDate': 20101230,
            
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
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : datetime.datetime(2011,1,1),
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate',
            'TradeSplitRuleArgs': 3,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V9', dragon_MB_mid.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20030102,
            'FirstTradeDate': 20101230,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
                
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
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_16HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 10),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.06,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 25,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Uniform_Noupdate',
            'TradeSplitRuleArgs': 3,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V8', dragon_MB.Strategy(), params )
        
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20101230,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
                
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
#                ( 'Update',( ( 'STS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_356'      ),
#                
#                ( 'Trade', ( ( 'STS', '0' ),                ), 'nxc_lasttrade_356'      ),
                
            ) 
        },
        
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.1,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20110131,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Once',
            'TradeSplitRuleArgs': 1,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V6', dragon_MB_MP.Strategy(), params )
    
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'EQUS001',
            'StartDate'     : 20040102,
            'FirstTradeDate': 20101230,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
                
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
#                ( 'Update',( ( 'STS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_356'      ),
#                
#                ( 'Trade', ( ( 'STS', '0' ),                ), 'nxc_lasttrade_356'      ),
                
            ) 
        },
        
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
        },

        'CalibParams' : {
            'CovRecomputeTrgr'  : ('bizday', 1),
            'TibRecomputeTrgr'  : ('bizday', 5000),
            'Lambda'            : 0.75 + 0.25*numpy.cos( numpy.pi * numpy.array( range(1,2*30,2) ) / (2*30) ),
            'IRLength'          : 100,
            'PolesCount'        : 12, 
            'FactorCount'       : 100, 
            'EMIterCount'       : 500,
            'Shrinkage'         : 0.1,    # this is sk
            'RiskLambda'        : 1,
            'LCost'             : 0.1,
            'QCost'             : 1,
            'CovDis'            : 0,
            'InitWeightFunc'    : reputil.initWithZeros,
            'SimCapital'        : 20,
            'Capital'           : 100e6,
            'Leverage'          : 3,
            'liquidity_TPB'     : 2,
            'Concentrate'       : 0.01,
            'Times'             : 1,
            #'Alpha'             : 0.006,
            'RampUpCutoff'      : 20110131,
            'Average_C'         : 'norm'
            #'Average_C'         : 'mean'
        },
              
        'Run': {
                'CalibWindow'   : 2000,
                'InitialOffset' : 20110103,
                'Slide'         : False,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
            'TradeSplitRule'    : 'Once',
            'TradeSplitRuleArgs': 1,            
        },
              
    }    
    reputil.setStrategy( 'DRAGON_V7', dragon_MB_MP_shift.Strategy(), params )
    
    params = stratutil.replicate( params )
    
    stratutil.amend( params, 
        'GetData', {
            'SymbolSpace'   : 'EQUS001_T1631',
            'StartDate'     : 20060801,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                   'nxc_lasttrade_930-359'   ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),                
                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),

                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
                
                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
                
                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
                
            ) 
        } )
