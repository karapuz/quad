'''
repository of the amends to the strtegy that does not affect the model.
'''

import os
from   meadow.lib.logging import logger
import meadow.strategy.util as stratutil

_amends = {
    'CAPITAL_10M' : {
        'CalibParams' : {
            'Capital'           : 10e6,
        },
    },
    'CAPITAL_20M' : {
        'CalibParams' : {
            'Capital'           : 20e6,
        },
    },
    'CAPITAL_10M_Simc_20' : {
        'CalibParams' : {
            'Capital'           : 10e6,
            'SimCapital'        : 20,                         
        },
    },
    'CAPITAL_10M_Simc_15' : {
        'CalibParams' : {
            'Capital'           : 10e6,
            'SimCapital'        : 15,                         
        },
    },
    'CAPITAL_10M_COVTrgr_10' : {
        'CalibParams' : {
            'Capital'           : 10e6,
            'CovRecomputeTrgr'  : ('bizday', 10),
        },
    },      
}

def applyAmend( stratParams, amendName ):
    ''' apply amends '''
    global _amends
    params = stratutil.replicate( stratParams )
    for name, value in _amends[ amendName ].iteritems():
        logger.debug( 'applyAmend %s:%s' % ( amendName, name ) ) 
        stratutil.amend( params=params, name=name, value=value )
    return params

def logAmends( strategyName, stratParams, amendName, amendedParams ):
    ''' log the amends '''
    global _amends
    paramFile = os.path.join( logger.dirName(), 'params.txt' )
    with open( paramFile, 'w' ) as fd:
        fd.write( 'StrategyName : %s\n' % strategyName )
        fd.write( 'StratParams  : %s\n' % str( stratParams ) )        
        if amendName:
            fd.write( 'AmendName    : %s\n' % amendName )
            fd.write( 'AmendParams  : %s\n' % str( _amends[ amendName ] ) )
            fd.write( 'AmendedParams: %s\n' % str( amendedParams ) )
        else:
            fd.write( 'Nothing amended\n' )
