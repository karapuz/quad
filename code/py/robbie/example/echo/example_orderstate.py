'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.orderstate module
DESCRIPTION : this module contains order state objects
'''

import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate

'''
    MargotRoot   = /margot/ivp
    Domain       = echo         # pretty much a constant. Other domains: risk management?
    Session      = 20160504     # tied to a day
    Activity     = mirror       # is related to echo; mirror, trade, market
'''

def run():
    turf = 'example_turf'
    tweaks  = {
        'run_turf'  : turf,
    }
    logger.debug( 'example_orderstate: turf=%s', turf)
    with twkcx.Tweaks( **tweaks ):
        symbols  = symboldb.currentSymbols()
        symIds   = symboldb.symbol2id(symbols=symbols)
        maxNum   = 1000000
        ordState = orderstate.OrderState( readOnly=False, maxNum=maxNum, symIds=symIds, debug=True )

if __name__ == '__main__':
    run()