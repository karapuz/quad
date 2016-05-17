import robbie.lib.calendar as cal
import robbie.strategy.util as stratutil
import robbie.strategy.colibri as colibri
import robbie.strategy.repository_util as reputil

def init():
    params = {
              
        'GetData': {
            'SymbolSpace'   : 'COLIBRI_S7',
            'StartDate'     : 20050102,
            
            'Schedule'      : (
                ( 'Calib',  ( 'SOD', '0' ),                     'nxc_lasttrade_930-935' ),
                ( 'Calib',  ( 'SOD', '1' ),                     'nxc_high_935-344'      ),
                ( 'Calib',  ( 'SOD', '2' ),                     'nxc_low_935-344'       ),
                ( 'Calib',  ( 'SOD', '3' ),                     'nxc_lasttrade_930-359' ),
                
                ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_930-935' ),
                ( 'Update', ( ( 'LTS', '1' ), ( 'SOD', '1' ) ), 'nxc_high_935-344'      ),
                ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '2' ) ), 'nxc_low_935-344'       ),
                ( 'Update', ( ( 'LTS', '3' ), ( 'SOD', '3' ) ), 'nxc_lasttrade_930-359' ),
                
                ( 'TradeAndM2MLimits',  ( ( 'LTS', '0' ),                ), 'nxc_lasttrade_930-359' ),

#                ( 'Mrk2Mkt', ( ( 'EOD', '0' ),               ), 'nxc_lasttrade_930-359' ),
                
            ) 
        },
        
        'SpecialProcessing': {
            'RemoveSymbolsRule' : [ 'BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND' ],
            'PatchRule'         : [ 'PATCH_ONEMISSING' ],
            # 'WhenAddNaN'        : 20070103,
            # 'Window'            : 500,
            'Thread'            : 0.05,
        },

        'CalibParams' : {                         
            'Shrinkage'         : 0.05,    # sk -> 0..1; the higher the number the less information is retained.
            'HighLowScale'      : 2.0,
        },
              
        'Run': {
                'CalibOffset'   : 0,
                'CalibWindow'   : 600,
                'InitialOffset' : 20130318, 
                'Slide'         : True,
        },

        'TradeParams' : {
            'BasisPointsTCC'    : 5e-4,
#            'TradeSplitRule'    : 'Uniform_Noupdate_ptl',
#            'TradeSplitRuleArgs': 3,            
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
    
    reputil.setStrategy( 'COLIBRI_V0', colibri.Strategy(), params )

    params = stratutil.replicate( params )
    stratutil.amend( params, 
            'GetData', { 
                'SymbolSpace' : 'COLIBRI_S7', 
            })
    reputil.setStrategy( 'COLIBRI_V1', colibri.Strategy(), params )
