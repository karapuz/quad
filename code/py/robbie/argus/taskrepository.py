'''
'''

import meadow.lib.datetime_util as dut
from   meadow.lib.logging import logger

_taskRepository = {
    'prep.mrkt' : {
        'dev'   : None,
        'fake'  : None,
    },

    'bbg' : {
        'dev'   : None,
        'fake'  : None,
    },

    'journal' : {
        'dev'   : None,
        'fake'  : None,
    },
                   
    'exec' : {
        'dev'   : None,
        'fake'  : None,
    },

    'algo' : {
        'dev'   : None,
        'fake'  : None,
    },

    'trade-prod' : { }, # will have models

}

def computeTime( schedName ):
    dt = dut.timeNow()
    if schedName == 'now':
        return dt
    
    elif schedName == 'now+1m':
        return dt+60
    
    raise ValueError( 'Unknown schedName=%s' % schedName )

def validateTaskPath( taskPath ):
    if isinstance( taskPath, (list, tuple ) ):
        if len( taskPath ) != 2:
            raise ValueError( 'Wrong length for the task path %s' % str( taskPath ) )
        return True
    raise ValueError( 'Wrong length for the task path %s' % str( taskPath ) )

def getTask( taskPath ):
    global _taskRepository
    validateTaskPath( taskPath )
    taskName, env = taskPath
    return _taskRepository[ taskName ][ env ]

def setTask( taskPath, taskObj ):
    global _taskRepository
    validateTaskPath( taskPath )
    taskName, env = taskPath
    
    if taskName not in _taskRepository:
        logger.debug( 'setTask: new task %s' % str( taskName ) )
        
        _taskRepository[ taskName ] = {}
         
    _taskRepository[ taskName ][ env ] = taskObj

_scheduleRepositoryComponents = {
    'start_allMinutes'  : 
        dut.schedTimes( 
            start = dut.timeInSecondsForStr( '09:29' ), 
            stop  = dut.timeInSecondsForStr( '16:01' ), 
            step  = 60, includeEnd=True   ),
    'stop_allMinutes'   : 
        dut.schedTimes( 
            start = dut.timeInSecondsForStr( '09:29' ), 
            stop  = dut.timeInSecondsForStr( '16:01' ), 
            step  = 60, includeStart=True ),
}

_src = _scheduleRepositoryComponents

_scheduleRepository = {
                       
    'begAllMinutes'    : { 
            'start' : _src['start_allMinutes'], 
    },
                       
    'allMinutes'        : { 
            'start' : _src['start_allMinutes'], 
            'stop'  : _src['stop_allMinutes'], 
    },
                       
    'allDay'            : { 
            'start' : ( dut.timeInSecondsForStr( '09:30' ), ), 
            'stop'  : ( dut.timeInSecondsForStr( '16:00' ), ) 
    },

    'startNowAllDay'            : { 
            'start' : ( 'now+1m', ), 
            'stop'  : ( dut.timeInSecondsForStr( '17:00' ), ) 
    },
                       
    'rightBeforeOpen'            : { 
            'start' : ( dut.timeInSecondsForStr( '09:29:59'), ), 
            'stop'  : ( dut.timeInSecondsForStr( '09:30:01'), ) 
    },
                       
    'startNow'          : { 'start': -1 },
    'stopNow'           : { 'stop' : -1 },
}

def getSched( schedName ):
    global _scheduleRepository
    
    if schedName == 'start_now':
        now = dut.timeNow()
        return { 'start': ( now+2, ) }
    
    elif schedName == 'stop_now':
        now = dut.timeNow()
        return { 'stop': ( now+2, ) }
    
    elif schedName == 'start_now+2*5':
        now = dut.timeNow()
        return { 'start': ( now+2, now+4, now+6, now+8, now+10 ) }
    
    return _scheduleRepository[ schedName ]

def setSched( schedName, schedObj ):
    global _scheduleRepository
    _scheduleRepository[ schedName ] = schedObj

def setStartStopSched( schedName, startTime, stopTime=None ):
    _scheduleRepository[ schedName ] = { 
        'start' : ( startTime, ),
    }
     
    if stopTime:
        _scheduleRepository[ schedName ][ 'stop'] = ( stopTime, ) 
