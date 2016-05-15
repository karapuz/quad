import os
import cmd
import sys
import threading

from sys import stdout
from   optparse import OptionParser

import meadow.lib.config as libconf
import meadow.argus.util as argus_util

import twisted.internet.error
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ClientEndpoint

def cmdPrompt():
    return 'argus:>'

whatAlias = {
    'bloomberg' : 'bbg',
    'jrnl'      : 'journal',
} 

whenAlias = { } 

class ArgusCmd( cmd.Cmd ):
    
    def setProtocolInstance(self, protocolInstance ):
        self._protocolInstance = protocolInstance
            
    def sendMessage( self, req ):
        stdout.write( '%s raw = %s\n' % ( cmdPrompt(), str ( argus_util.Request.unpack( req ) ) ) )
        self._protocolInstance.sendMessage( req )

    def emptyline( self ):
        pass
    
    def do_help( self, x ):
        print 'Argus commands:'
        for a in dir( self ):
            if 'do_' in a:
                print '\t', a[3:]

    def do_shell( self, s ):
        print os.system( s )

    def do_exit(self, x):
        try:
            def sleepAndExit():
                import time
                import meadow.lib.report as libreport
                time.sleep(2)
                libreport.reportAndKill( txt='Killing the client', subject='Process is killed', sendFrom=None, sendTo=None )
                
            threading.Thread( target=sleepAndExit ).start()
            reactor.stop() #@UndefinedVariable
        except twisted.internet.error.ReactorNotRunning as _e:
            print 'already stopped'
        sys.exit()

    prompt = cmdPrompt()
    
    def parseReq(self, x ):
        global whatAlias, whenAlias
        stdout.write( '%s x = %s\n' % ( cmdPrompt(), str( x ) ) )
        
        parts= x.split(' ')
        what, when, how = '', '', ''
        
        if len( parts ) == 3:
            what, when, how = parts
        elif len( parts ) == 2:
            what, when = parts
        elif len( parts ) == 1:
            what = parts[0]

        stdout.write( '%s what = %s when = %s\n' % ( cmdPrompt(), what, when ) )
        
        if what:            
            what = whatAlias.get( what,  what )
        if when:
            when = whenAlias.get( when, when ) 

        return what, when, how

    def do_status( self, x):
        typ = 'STATUS'
        what, when, how = self.parseReq(x)
        req = argus_util.createReq( typ=typ, what=what, when=when, how=how )
        self.sendMessage( req )

    def do_start( self, x):
        typ = 'START'
        what, when, how = self.parseReq(x)
        req = argus_util.createReq( typ=typ, what=what, when=when, how=how )
        self.sendMessage( req )

    def do_stop( self, x):
        global whenAlias
        typ = 'START'
        what, when, how = self.parseReq(x)
        req = argus_util.createReq( typ=typ, what=what, when=when, how=how )
        self.sendMessage( req )
    
    def do_cx( self, x ):
        typ = 'CANCEL'
        what, when, how = self.parseReq(x)
        req = argus_util.createReq( typ=typ, what=what, when=when, how=how )
        self.sendMessage( req )

    def do_mng( self, x ):
        typ = 'MNG'
        what, when, how = self.parseReq(x)
        
        if what in ( 'exp', 'exposure' ):
            if when in ( 'load', 'l' ):
                if not how:
                    stdout.write( '%s ERROR must have filename to load exposure%s\n' % ( cmdPrompt(), how ) )
                    return
                
                exists, dn, fn, fp = argus_util.getClientFile( how )
                
                if not exists:
                    stdout.write( '%s ERROR no such file %s at %s\n' % ( cmdPrompt(), fn, dn ) )
                    return
                
                exposure = argus_util.loadExposure( fp )
                what = 'exposure'
                when = 'load'
                how  = str( exposure )

        elif what in ( 'exec' ):
            
            if when in ( 'load', 'l' ):
                
                if not how:
                    stdout.write( '%s ERROR must have filename to load trades %s\n' % ( cmdPrompt(), how ) )
                    return
                
                exists, dn, fn, fp = argus_util.getClientFile( how, '.trd' )
                
                if not exists:
                    stdout.write( '%s ERROR no such file %s at %s\n' % ( cmdPrompt(), fn, dn ) )
                    return
                
                data = argus_util.loadTrade( fp )
                what = 'exec'
                when = 'load'
                how  = str( data )

        req = argus_util.createReq( typ=typ, what=what, when=when, how=how )
        self.sendMessage( req )
    
class ArgusThread( threading.Thread ):
    
    def __init__(self, protocolInstance ):
        super( ArgusThread, self ).__init__()
        self._protocolInstance = protocolInstance
        
    def run(self):
        cmdObj = ArgusCmd()
        cmdObj.setProtocolInstance( self._protocolInstance )
        cmdObj.cmdloop('argus v1.0')
        
# should I block?
globalCache = {}

class ArgusTwistedClient( LineReceiver ):
    MAX_LENGTH = int( 1e6 )
                    
    def sendMessage( self, msg ):
        self.transport.write( msg + '\r\n' )
    
    def connectionMade(self):
        stdout.write( '%s connectionMade\n' % cmdPrompt() )

    def connectionLost(self, reason):
        stdout.write( '%s connectionLost reason=%s\n' % ( cmdPrompt(), reason ) )
        # reactor.stop()

    def lineReceived(self, resp):
        global globalCache
        resp = argus_util.Request.unpack( resp )
        stdout.write( '%s\n' % str( resp ) )

class ArgusTwistedClientFactory( Factory ):
    
    def buildProtocol( self, addr ):
        stdout.write( '%s addr = %s\n' % ( cmdPrompt(), addr ) )
        return ArgusTwistedClient()

def connectedNow( protocolInstance ):
    thread = ArgusThread( protocolInstance )
    thread.start()    

def run( serverHost, serverPort ):
    point       = TCP4ClientEndpoint( reactor, serverHost, serverPort )
    endPoint    = point.connect( ArgusTwistedClientFactory() )
    endPoint.addCallback( connectedNow )    
    reactor.run() #@UndefinedVariable

if __name__ == '__main__':
    
    parser = OptionParser()    
    parser.add_option('-d', '--debug',  action="store", default=None, dest='debug')
    parser.add_option('-T', '--turf',   action="store", default=None, dest='turf')
    (options, args) = parser.parse_args()
    
    turf = options.turf
    
    port=libconf.get(turf=turf, component='argus', sub='port')
    host=libconf.get(turf=turf, component='argus', sub='host')
    
    run( host, port )
