'''
'''
import functools

import meadow.lib.shell as shell
import meadow.lib.compat as compat
import meadow.argus.util as argus_util
import meadow.lib.datetime_util as dut
from   meadow.lib.logging import logger
import meadow.argus.schedutil as schedutil

_dailySchedule = {
    'PRESOD'    : dut.symbolTimes['01:00'],
    'SOD'       : dut.symbolTimes['05:00'],
    'EOD'       : dut.symbolTimes['18:00'],
    'POSTEOD'   : dut.symbolTimes['22:00'],
}

pingExec, pingArgs = compat.ping('10.1.1.200', 5)

_dailyOps = { 
    'shell'     : shell.runCmdNoInput,
    'startbbg'  : argus_util.startBbg,
    'startjrnl' : argus_util.startJrnl,
    'resetlog'  : argus_util.resetLogger,
    'resetserver' : argus_util.resetServer,
}

_dailyCommands = {
    'PRESOD': (
        [ 'resetserver', { 'server': None }, ],  
    ),
    'SOD': [
        [ 'shell', { 'executable':pingExec, 'args':pingArgs, 'postProc' : functools.partial( argus_util.notContain, 'timed out' ) }, ],    
    ],
}

def setTask( tag, taskName, args ):
    global _dailyCommands
    for line in _dailyCommands[ tag ]:
        if taskName == line[0]:
            line[1] = args
            return
    logger.error( 'can not find %s' % taskName )

def scheduleDailyTasks( tag, firstExec, logger ):
    ''' 
        run all daily tasks for the tag
        tag: SOD, EOD
        
    '''
    
    global _dailySchedule, _dailyCommands, _dailyOps
        
    startTime   = _dailySchedule[ tag ]
    for taskName, args in _dailyCommands[ tag ]:
        func    = _dailyOps.get( taskName )
        
        if not func:
            func = taskName.func_name

        schedutil.scheduleRepeatNextDay( 
                startTime = startTime, 
                taskName  = taskName, 
                func      = func, 
                args      = args, 
                firstExec = firstExec,
                dayRule   = '+1b',
                logger    = logger, flag=None )

if __name__ == '__main__':
    import meadow.lib.logging as logging
    logging.toFile(app='argus', mode='p' )

    tag, firstExec = 'SOD', 'always'
    scheduleDailyTasks( tag=tag, firstExec=firstExec, logger=logging.logger )