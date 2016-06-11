'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.mmap_array module
'''

import os
import time
import numpy
import robbie.util.margot as margot

from   robbie.util.logging import logger

#import meadow.lib.config as libconf
#import meadow.tweak.value as twkval
#import meadow.lib.space as libspace
import robbie.tweak.context as twkcx

'''
Structure
    /MargotRoot/Domain/Session/Activity

    MargotRoot   = /margot/ivp
    Domain       = echo         # pretty much a constant. Other domains: risk management?
    Session      = 20160504     # tied to a day
    Activity     = mirror       # is related to echo; mirror, trade, market
                    instrument_index
                        str:int { IBM: 1, MSFT: 2, ... }
                    instrument_exposure
                        float 1xN (N = 10,000)
                    order_new
                        float KxM (K=100, M = 500,000, K x M = 50MB)

    Activity    = trade
                    instrument_index
                        str:int { IBM: 1, MSFT: 2, ... }
                    instrument_exposure
                        float 1xN (N = 10,000)
                    order_new
                        float KxM (K=100, M = 500,000, K x M = 50MB)

    Activity    = market
                    book_top
                        float 3xN (N = 10,000) (bid, ask, qty)

'''
def _new( activity, shape, mode='w+', dtype='float32', initVals=None, domain=None, session=None  ):
    path = margot.getSessionSlice( domain=domain, session=session, activity=activity, create=True )
    arr  = numpy.memmap( path, dtype=dtype, mode=mode, shape=shape )
    if initVals != None:
        arr[:] = initVals
    return arr

def newWrite( activity, shape, dtype='float32', session=None, domain=None  ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='write', dtype=dtype )

def newRead( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='r', dtype=dtype )

def new( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype )

def zeros( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype, initVals=0 )
