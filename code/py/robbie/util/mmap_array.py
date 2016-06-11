'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.mmap_array module
'''

import numpy
import robbie.util.margot as margot

'''
Structure
    /MargotRoot/Domain/User/Session/Activity

    MargotRoot   = /margot/ivp
    Domain       = echo         # pretty much a constant. Other domains: risk management?
    User         = user
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
def _new( domain, user, session, activity, shape, initVals=None, dtype='float32', mode='w+' ):
    path = margot.getSessionSlice( domain=domain, user=user, session=session, activity=activity, create=True )
    arr  = numpy.memmap( path, dtype=dtype, mode=mode, shape=shape )
    if initVals != None:
        arr[:] = initVals
    return arr

def newWrite( domain, user, session, activity, shape, dtype='float32'):
    return _new( domain=domain, user=user, session=session, activity=activity, shape=shape, mode='write', dtype=dtype )

def newRead( domain, user, session, activity, shape, dtype='float32'):
    return _new( domain=domain, user=user, session=session, activity=activity, shape=shape, mode='r', dtype=dtype )

def new( domain, user, session, activity, shape, dtype='float32'):
    return _new( domain=domain, user=user, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype )

def zeros( domain, user, session, activity, shape, dtype='float32'):
    return _new( domain=domain, user=user, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype, initVals=0 )
