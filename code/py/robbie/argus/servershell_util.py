'''
'''
import time
import datetime

from   meadow.lib.logging import logger

import meadow.argus.util as argus_util
import meadow.argus.taskrepository as repository

class Server( object ):
    
    def __init__( self, taskData ):
        self._taskData  = taskData
        
    def now( self ):
        return datetime.datetime.now()
            
    def clearStatus( self, env ):
        ''' clear all status '''
        td      = self._taskData
        td[ 'status' ] = {} 
    
    def startTask( self, env, taskType, schedName ):
        
        logger.debug( 'Start: env=%s specs=%s' % ( str( env ), str( ( taskType, schedName ) ) ) )
        
        td      = self._taskData
        taskName= argus_util.scheduledTaskName( taskType, schedName )
        
        td[ 'status' ][ taskName ] = argus_util.Status.alive
        td[ 'started'][ taskName ] = self.now()
        
        taskPath    = ( taskType, env )
        taskClass   = repository.getTask( taskPath )
        
        td[ 'timers' ][ taskName ] = []        
        timers = td[ 'timers' ][ taskName ]
                
        for funcName, dts in repository.getSched( schedName ).iteritems():
            for dt in dts:
                if isinstance( dt, str ):
                    dt = repository.computeTime( schedName=dt )
                    
                timer, delay = argus_util.newTimedThreadedTask( dt=dt, funcName=funcName, taskObj=taskClass.create(), logger=logger )
                if timer:            
                    logger.debug( 'timers data: %s' % str ( ( timer, delay ) ) )            
                    timers.append( ( timer, delay ) )

    def cancelTask( self, env, taskType, schedName, taskParams ):
        
        logger.debug( 'cancel: env=%s specs=%s' % ( str( env ), str( ( taskType, schedName, taskParams  ) ) ) )
        
        td      = self._taskData
        taskName= argus_util.scheduledTaskName( taskType, schedName )
        
        if taskName not in td[ 'status' ] or td[ 'status' ][ taskName ] != argus_util.Status.alive: 
            return argus_util.Request.pack( 'success',
                        argus_util.stateEvolution( argus_util.Status.none, argus_util.Status.none ) )
        
        td[ 'tasks'  ][ taskName ] = None
        td[ 'status' ][ taskName ] = argus_util.Status.dead
                
        timers = td[ 'timers' ][ taskName ]
        for timer, delay in timers:
            timer.cancel() 
            logger.debug( 'canceling timers data: %s' % str ( ( timer, delay ) ) )
        
        return argus_util.Request.pack( 'success',
                    argus_util.stateEvolution( argus_util.Status.alive, argus_util.Status.none ) )
        
def run():
    while 1:
        time.sleep( 10 )
