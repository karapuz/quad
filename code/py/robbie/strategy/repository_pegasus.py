'''
global repository
'''

import meadow.strategy.repository_util as reputil

#import meadow.strategy.pegasus_data as pegasus_data
#import meadow.strategy.pegasus_data_restriction as pegasus_data_restriction
#import meadow.strategy.pegasus_data_restriction_build_up as pegasus_restriction_build_up
import meadow.strategy.pegasus_prod as pegasus_prod
import numpy as numpy

def init():

#    params = {
#              
#        'GetData': {
#            'SymbolSpace'   : 'HYUS001',
#            'StartDate'     : 20020114,
#            'FirstTradeDate': 20061228,
#            
#            'Schedule'      : (
#                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
#                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
#                
##                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-351' ),
##                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_352'        ),
##                
##                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
##                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
##                
##                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
##                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
##                
##                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
#                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-359' ),
#                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_lasttrade_930-359' ),
#                
#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),                
#            ) 
#        },
#              
#        'SpecialProcessing': {
#            'RemoveSymbolsRule' : [ 'BADTICKER_VOID'   ],
#            'PatchRule'         : [ 'PATCH_VOID' ],
#            'PostPatchRule'     : [ ( 'logret', 'PATCH_CONVERT_INFS') ],
#        },        
#
#        'CalibParams' : {
#        },
#              
#        'Run': {
#                'CalibWindow'   : 2000,
#                'InitialOffset' : 20070103,
#                'Slide'         : False,
#        },
#
#        'TradeParams' : {
#            'BasisPointsTCC'    : 5e-4,
#            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
#            'TradeSplitRuleArgs': 3,            
#        },
#              
#        'Execution' : {
#            'AllocationSchema'  :   'CASH',
#            'ProductType'       :   'CASH',
#        },
#              
#        'Tweaks' : {
#            'report_useMrk2Mrkt' : 'NaN_case',
#        },
#              
#    }    
#    reputil.setStrategy( 'PEGASUS_Prod_dev', pegasus_data.Strategy(), params )
    

   
#    params = {
#              
#        'GetData': {
#            'SymbolSpace'   : 'HYUS001',
#            'StartDate'     : 20020114,
#            'FirstTradeDate': 20061228,
#            
#            'Schedule'      : (
#                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
#                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
#                              
#    
#                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),
#                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_358'        ),
##                
##                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
##                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
##                
##                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
##                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
##                
##                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
##                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-359' ),
##                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_lasttrade_930-359' ),
#                
#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),                
#            ) 
#        },
#              
#        'SpecialProcessing': {
#            'RemoveSymbolsRule' : [ 'BADTICKER_VOID'   ],
#            'PatchRule'         : [ 'PATCH_VOID' ],
#            'PostPatchRule'     : [ ( 'logret', 'PATCH_CONVERT_INFS') ],
#        },        
#
#        'CalibParams' : {
#        },
#              
#        'Run': {
#                'CalibWindow'   : 2000,
#                'InitialOffset' : 20070103,
#                'Slide'         : False,
#        },
#
#        'TradeParams' : {
#            'BasisPointsTCC'    : 5e-4,
#            'TradeSplitRule'               
#       : '100shares_per_second',
#            'TradeTimes': 3,            
#        },
#              
#        'Execution' : {
#            'AllocationSchema'  :   'CASH',
#            'ProductType'       :   'CASH',
#        },
#              
#        'Tweaks' : {
#            'report_useMrk2Mrkt' : 'NaN_case',
#        },
#              
#    }    
#    reputil.setStrategy( 'PEGASUS_Prod_dev_0357_trade', pegasus_data.Strategy(), params )

#    params = {
#              
#        'GetData': {
#            'SymbolSpace'   : 'HYUS001',
#            'StartDate'     : 20020114,
#            'FirstTradeDate': 20061228,
#            
#            'Schedule'      : (
#                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
#                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359_wYahoo' ),
#                              
#    
#                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),
#                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_358'        ),
##                
##                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
##                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
##                
##                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
##                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
##                
##                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
##                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-359' ),
##                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_lasttrade_930-359' ),
#                
#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),                
#            ) 
#        },
#              
#        'SpecialProcessing': {
#            'RemoveSymbolsRule' : [ 'BADTICKER_VOID'   ],
#            'PatchRule'         : [ 'PATCH_VOID' ],
#            'PostPatchRule'     : [ ( 'logret', 'PATCH_CONVERT_INFS') ],
#        },        
#
#        'CalibParams' : {
#        },
#              
#        'Run': {
#                'CalibWindow'   : 2000,
#                'InitialOffset' : 20070103,
#                'Slide'         : False,
#        },
#
#        'TradeParams' : {
#            'BasisPointsTCC'    : 5e-4,
#            'TradeSplitRule'               
#       : '100shares_per_second',
#            'TradeTimes': 3,            
#        },
#              
#        'Execution' : {
#            'AllocationSchema'  :   'CASH',
#            'ProductType'       :   'CASH',
#        },
#              
#        'Tweaks' : {
#            'report_useMrk2Mrkt' : 'NaN_case',
#        },
#              
#    }    
#    reputil.setStrategy( 'PEGASUS_Prod_dev_0357_trade_with_restriction_list', pegasus_data_restriction.Strategy(), params )

#    params = {
#              
#        'GetData': {
#            'SymbolSpace'   : 'HYUS001',
#            
#            'StartDate'     : 20080102,
#            'FirstTradeDate': 20121231,
#            
#            'Schedule'      : (
#                #( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),               
#                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-359' ),
#                              
#    
#                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),
#                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_avgmin_358'        ),
#                
#                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-355' ),                
#                ( 'Trade',  ( ( 'LTS', '1' ),                ), 'nxc_avgmin_356'        ),
#                
#                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-357' ),                
#                ( 'Trade',  ( ( 'LTS', '2' ),                ), 'nxc_avgmin_358'        ),
#                
#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
#                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-359' ),
#                ( 'Trade',  ( ( 'LTS', '0' ),                ), 'nxc_lasttrade_930-359' ),
#                
#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),                
#            ) 
#        },
#              
#        'SpecialProcessing': {
#            'RemoveSymbolsRule' : [ 'BADTICKER_VOID'   ],
#            'PatchRule'         : [ 'PATCH_VOID' ],
#            'PostPatchRule'     : [ ( 'logret', 'PATCH_CONVERT_INFS') ],
#        },        
#
#        'CalibParams' : {
#            'c'       : 0.5,
#            'd'       : 8.75e-5,
#            'clambda' : 0.1,
#            'tau'     : 0.97,
#            'tail'      : 0.23,
#            'sh'        : 0.01,
#            'hedge_max' : 800,
#            'capital_scalar' : 49.914364989308517,
#            'totalcapital'   : 16e6,
#            'constraintor' : 1,
#            'rbcontroller' : 1,
#            'kickout_price'  : 6,
#            'kickout_volume' : 0.5e6,
#            'letin_price'    : 10,
#            'letin_volume'   : 1e6,
#			'tib_xwindow'    : 250,
#			'tib_k'			 : 2,
#			'poles' 		 : numpy.append(numpy.zeros((1,2)), numpy.cos(numpy.pi * numpy.array(range(1,6, 2))/6)*0.001 + 0.999).reshape((-1,1)),
#			'cov_xwindow'	 : 750,
#			'cov_k'			 : 2,
#			'factor_number'  : 100,
#			'yield_maxflat_lambda'  : 0.97,
#			'yield_maxflat_d': 3,
#			'yield_distribution_window' : 250,
#			'sigmoid_alpha'	 : 200,
#			'holding_constraint' : 0.04,
#			'trading_constraint' : 0.01,
#        },
#              
#        'Run': {
#                'CalibWindow'   : 2000,
#                'InitialOffset' : 20130529,
#                'Slide'         : False,
#        },
#
#        'TradeParams' : {
#            'BasisPointsTCC'    : 5e-4,
#            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
#            'TradeSplitRuleArgs': 3,       
#        },
#              
#        'Execution' : {
#            'AllocationSchema'  :   'CASH',
#            'ProductType'       :   'CASH',
#        },
#              
#        'Tweaks' : {
#            'report_useMrk2Mrkt' : 'NaN_case',
#        },
#              
#    }    
#    reputil.setStrategy( 'PEGASUS_Prod_dev_0357_trade_with_restriction_list_build_up', pegasus_restriction_build_up.Strategy(), params )

    params = {
              
        'GetData': {
            'SymbolSpace'   : 'HYUS001',
            
            'StartDate'     : 20080102,
            'FirstTradeDate': 20130513,
            
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
            'totalcapital'   : 16e6,
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
                'InitialOffset' : 20130610,
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
    reputil.setStrategy( 'PEGASUS_PRODUCTION', pegasus_prod.Strategy(), params )
    
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'HYUS001',
            
            'StartDate'     : 20080102,
            'FirstTradeDate': 20130513,
            
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
                'InitialOffset' : 20130709,
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
    reputil.setStrategy( 'YIELD_EST_V0', pegasus_prod.Strategy(), params )

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
    reputil.setStrategy( 'GOLDEN_mirrow', pegasus_prod.Strategy(), params )
