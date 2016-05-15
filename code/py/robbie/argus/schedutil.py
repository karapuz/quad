import threading
import functools
import datetime

import meadow.argus.util as argus_util
import meadow.lib.datetime_util as dut
from   meadow.lib.logging import logger

import meadow.lib.calendar as cal
import meadow.tweak.value as twkval 

def nowFuncSec():
    dt = datetime.datetime.now()
    return dt.hour * 60 * 60 + dt.minute * 60 + dt.second + dt.microsecond / 1e6

def scheduleRepeatAfter( delay, cycleFunc, finishFunc, args, logger, firstExec=False, flag=None, maxTime=None, debug=False ):

    cycleFuncName   = cycleFunc.func_name
    finishFuncName  = finishFunc.func_name
    
    def _wrapped( thisExec, prevTime ):
          
        if flag and not flag.cont:
            logger.debug( 'scheduleRepeat: stopping %s' % cycleFuncName)
            return

        now = nowFuncSec()

        if thisExec:
            if args:
                _r = cycleFunc( **args )
            else:
                _r = cycleFunc()

        if now > maxTime:
            logger.debug( 'scheduleRepeat: finishing %s' % finishFuncName)
            return finishFunc()                

        then = nowFuncSec()

        rtDelay = max( delay/10., delay - ( then - now ) )
        # rtDelay = delay

        if debug:
            logger.debug( 'scheduleRepeatAfter rtDelay=%8.2f delay=%8.2f now=%8.2f prevTime=%8.2f' % ( rtDelay, delay, now, prevTime ) )
            
        nextExec = True
        timer = threading.Timer( rtDelay, functools.partial( _wrapped, nextExec, now ) )
        timer.start()
        
    now = nowFuncSec()        
    _wrapped( firstExec, now-delay )

def scheduleRepeatSimple( delay, func, args, flag=None ):

    def _wrapped():
        if not flag.cont:
            logger.debug( 'stopping %s( %s )' % ( func.func_name, str( args ) ) )
            return
        
        t = threading.Timer( delay, _wrapped )
        t.start()
        
        logger.debug( 'invoking %s( %s )' % ( func.func_name, str( args ) ) )
        if args:
            retVal = func( **args )
        else:
            retVal = func()
        success = 'Success' if retVal else 'Failure'
        logger.debug( '[ %s ] done with %s( %s )' % ( success, func.func_name, str( args ) ) )
            
        return retVal
        
    _wrapped()

def scheduleRepeatNextDay( startTime, taskName, func, args, firstExec, dayRule, logger, flag=None ):
    
    def _wrapped( logger, execNow ):
        
        if flag and not flag.cont:
            logger.debug( 'scheduleRepeatNextDay: stopping %s( %s )' % ( func.func_name, str( args ) ) )
            return
        
        now     = cal.now()
        dayNow  = now.date()
        nextbd  = cal.bizday( dayNow, dayRule )
        nexttm  = cal.formdatetime( nextbd, startTime )
        
        delay   = dut.toTimeSec(nexttm, asTime=False) - dut.toTimeSec(now, asTime=False)
        nextExec= True 
        timer   = threading.Timer( delay, functools.partial( _wrapped, logger, nextExec ) )
        timer.start()

        if execNow:
            logger.debug( 'scheduleRepeatNextDay: invoking %s( %s )' % ( func.func_name, str( args ) ) )
            if args:
                retVal, txt  = func( **args )
            else:
                retVal, txt  = func()
            argus_util.storeRetVals( logger, taskName, txt )            
            success = 'Success' if retVal else 'Failure'
            logger.debug( 'scheduleRepeatNextDay: %s %s' % (taskName, success ) )
            logger.flush()
        else:
            logger.debug( 'scheduleRepeatNextDay: skipping %s( %s )' % ( func.func_name, str( args ) ) )
            
        return timer
        
    if firstExec == 'timeBefore':
        execNow = cal.now().time() < startTime
    elif firstExec == 'notFirst':
        execNow = False
    elif firstExec == 'always':
        execNow = True
    else:
        raise ValueError( 'Unknown firstExec=%s' % firstExec )
    
    return _wrapped( logger, execNow )

def scheduleRepeat( startTime, taskName, delay, func, args, firstExec, flag=None ):
    env     = twkval.getenv( 'run_env' )
    logger.debug( 'scheduleRepeat env=%s' % env )    

    def _wrapped( logger, execNow ):
        if flag and not flag.cont:
            logger.debug( 'stopping %s( %s )' % ( func.func_name, str( args ) ) )
            return

        nextExec= True 
        timer   = threading.Timer( delay, functools.partial( _wrapped, logger, nextExec ) )
        timer.start()

        if execNow:
            logger.debug( 'invoking %s( %s )' % ( func.func_name, str( args ) ) )
            if args:
                retVal, txt  = func( **args )
            else:
                retVal, txt  = func()
            argus_util.storeRetVals( logger, taskName, txt )            
            success = 'Success' if retVal else 'Failure'
            logger.debug( '%s %s' % (taskName, success ) )    
            # logger.debug( 'return: %s' % txt )    
        else:
            logger.debug( 'skipping %s( %s )' % ( func.func_name, str( args ) ) )
        
    if firstExec == 'timeBefore':
        execNow = cal.now().time() < startTime
    elif firstExec == 'notFirst':
        execNow = False
    elif firstExec == 'always':
        execNow = True
    else:
        raise ValueError( 'Unknown firstExec=%s' % firstExec )
    
    _wrapped( logger, execNow )

