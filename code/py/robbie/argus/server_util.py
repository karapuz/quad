'''
'''

import datetime
import threading
import traceback

import meadow.argus.taskenv as taskenv

from   twisted.internet import reactor
from   twisted.internet.protocol import Factory
from   twisted.protocols.basic import LineReceiver

import meadow.lib.tmp as libtmp
import meadow.tweak.value as twkval 
import meadow.lib.report as libreport
from   meadow.lib.logging import logger

import meadow.argus.util as argus_util
import meadow.argus.taskrepository as repository
import meadow.argus.component_util as cmputil

__version__ = "2.01"

def specs2norm( specs ):
    taskType, schedName, taskParams = '', '', ''
    
    if len( specs ) == 1:
        taskType = specs
    elif len( specs ) == 2:
        taskType, schedName = specs
    elif len( specs ) == 3:
        taskType, schedName, taskParams = specs

    return taskType, schedName, taskParams

def reportUnknown( typ, val ):
    msg = 'Unknown %s=%s' % ( typ, str( val ) )
    logger.error( msg )
    return msg

class Server( object ):
    
    def __init__( self, taskData ):
        self.handlers = {
            argus_util.Request.start    : self._handleStart,
            argus_util.Request.cancel   : self._handleCancel,
            argus_util.Request.status   : self._handleStatus,
            argus_util.Request.clear    : self._handleClearStatus,
            argus_util.Request.mng      : self._handleMng,
        }        
        self._taskData  = taskData
        
    def now( self ):
        return datetime.datetime.now()

    def mng( self, env, taskType, optType, taskParams ):
        
        if taskType in ( 'exec' ):            
            if optType in [ 'load' ]:
                import meadow.argus.exectask as exectask
                
                tradeSpecs = eval( taskParams )
                logger.debug( 'tradeSpecs=%s' % str( tradeSpecs ) )
                
                orderQueue      = taskenv.getObj('env', 'orderQueue' )
                orderManager    = taskenv.getObj('env', 'orderManager' )                        
                
                try:
                    exectask.generateOrders( orderManager=orderManager, orderQueue=orderQueue, tradeSpecs=tradeSpecs )                    
                except:
                    msg = traceback.format_exc()
                    logger.error( 'Bad data (?) tradeSpecs=%s' % str( tradeSpecs ) )
                    logger.error( msg )
                    return argus_util.Request.pack( 'failure', msg ) 
            else:
                return reportUnknown( 'optType', optType )
        
        elif taskType in [ 'exposure', 'exp' ]:
            
            if optType in [ 'l', 'ld', 'load' ]:
                exposure = eval( taskParams )
                logger.debug( 'exposure = %s' % str( exposure ) )                
                taskenv.setObj('env', 'staticExposure', exposure ) 
            
            elif optType in [ 'dump' ]:
                fp = libtmp.getTempTimeFile('staticExposure_', suffix='rel', dn=logger.dirName() )                
                with open( fp, 'w' ) as fd:
                    fd.write( 'staticExposure:')
                    for line in taskenv.getObj('env', 'staticExposure' ):
                        fd.write( str( line ) + '\n' )
            else:
                return reportUnknown( 'optType', optType )
                
        elif taskType in [ 'thread', 'thrd', 'th' ]:
            if optType in [ 'c', 'count', 'cnt' ]:
                return 'threading.activeCount=%s' % threading.activeCount() 
            else:
                return reportUnknown( 'optType', optType )
        
        elif taskType in [ 'rel', 'relation', 'r' ]:
            
            relObj = taskenv.getObj('env', 'relations' )
            
            if optType in [ 'create', 'new', 'n' ]: 
                relObj.init()
            
            elif optType in [ 'dump' ]:
                fp = libtmp.getTempTimeFile('relation_', suffix='rel', dn=logger.dirName())                
                with open( fp, 'w' ) as fd:
                    relObj.dump( fd )
            else:
                return reportUnknown( 'optType', optType )
        else:
            return reportUnknown( 'taskType', taskType )
        
        msg = '%s %s done' % ( taskType, optType )
        logger.debug( msg )
        return argus_util.Request.pack( 'success', msg )
            
    def clearStatus( self, env ):
        ''' clear all status '''
        td      = self._taskData
        td[ 'status' ] = {} 
    
    def startTask( self, env, taskType, schedName ):
        
        logger.debug( 'Start: env=%s specs=%s' % ( str( env ), str( ( taskType, schedName ) ) ) )
        
        td      = self._taskData
        taskName= argus_util.scheduledTaskName( taskType, schedName )
        
        #        if 'now' not in schedName:
        #            if taskName in td[ 'status' ] and td[ 'status' ][ taskName ] == argus_util.Status.alive: 
        #                return argus_util.stateEvolution( argus_util.Status.alive, argus_util.Status.alive )
        
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
        
    def _handleStart( self, env, specs ):
        taskType, schedName, _taskParams = specs2norm( specs )
        
        self.startTask( env, taskType, schedName )
        
        return argus_util.Request.pack( 'success', 
                        argus_util.stateEvolution( argus_util.Status.none, argus_util.Status.alive ) )

    def _handleCancel( self, env, specs ):
        taskType, schedName, taskParams = specs2norm( specs )
        self.cancelTask( env, taskType, schedName, taskParams )
        return argus_util.Request.pack( 'success', 
                        argus_util.stateEvolution( argus_util.Status.none, argus_util.Status.dead ) )

    def _handleClearStatus(self, env, specs=None):
        return self.clearStatus( env )
    
    def _handleStatus( self, env, specs ):
        try:
            return argus_util.Request.pack( 'success', 
                        argus_util.formStatus( env=env, specs=specs, taskData=cmputil.taskData ) )
        except:
#            import pdb
#            pdb.set_trace()
            msg = traceback.format_exc()
            logger.debug( msg )
            return argus_util.Request.pack( 'failure', msg ) 

    def _handleMng( self, env, specs ):
        taskType, schedName, taskParams = specs2norm( specs )
        return argus_util.Request.pack( 'success',
                    self.mng( env, taskType, schedName, taskParams ) )
            
    def handleRequest(self, client, request ):
        typ, specs  = argus_util.Request.unpack( request )
        handler     = self.handlers[ typ ]
        env         = twkval.getenv( 'run_env' ) 
        msg         = handler( env, specs )
        client.sendLine( msg )
        
class ServerSession( LineReceiver ):
    MAX_LENGTH = int( 1e6 )
    
    def __init__(self, server):
        self._server = server
    
    def connectionMade(self):
        logger.debug( 'connectionMade\n' )

    def connectionLost(self, reason):
        logger.debug( 'connectionLost reason=%s\n' % reason )
    
    def lineReceived(self, request):
        logger.debug( 'lineReceived %s\n' %  str( argus_util.Request.unpack( request ) ) )
        self._server.handleRequest( self, request )
                
class ServerSessionFactory(Factory):
    def __init__(self, taskData ):
        self._server = Server( taskData )
        
    def buildProtocol(self, addr):
        return ServerSession( self._server )

def createFactory( port, taskData, debug ):
    try:
        factory = ServerSessionFactory( taskData )
        reactor.listenTCP( port, factory ) #@UndefinedVariable
        return factory
    except:
        txt=traceback.format_exc()            
        libreport.reportAndKill(txt=txt, subject='Argus died', sendFrom='argus', sendTo='ipresman' )

def run():
    reactor.run() #@UndefinedVariable
