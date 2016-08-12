'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.util - utils for the exec
'''

import os
import traceback
import quickfix as fix
import robbie.fix.util as fut
import robbie.tweak.value as twval
import robbie.fix.config as fixccfg
import robbie.util.margot as margot
import robbie.tweak.context as twkcx
import robbie.fix.seqnum as seqnumutil
from   robbie.util.logging import logger

def initFixConfig( fixTweakName ):
    '''
    needs tweak: fix_connConfig
    fixTweakName = fix_SrcConnConfig
    '''
    comm    = twval.getenv( fixTweakName )
    print 'comm =', comm, 'fixTweakName =', fixTweakName
    host, port, sender, target = comm[ 'host' ], comm[ 'port' ], comm[ 'sender' ], comm[ 'target' ]

    fixDictPath = os.path.join( margot.getConfigRoot('fix'), 'FIX42.xml')

    with twkcx.Tweaks( fix_source=sender ):
        fixLogRoot  = margot.getRoot(compName='fix')
        logPath     = fixccfg.getFIXConfig( root=fixLogRoot, name='log')
        storePath   = fixccfg.getFIXConfig( root=fixLogRoot, name='store')

        content = fixccfg.configContent(
            fixDictPath=fixDictPath, logPath=logPath, storePath=storePath, host=host, port=port, sender=sender, target=target
        )
        return fixccfg.createConfigFile( root=fixLogRoot, content=content )

def resetSeqNum( sessionID, message ):
    try:
        return _resetSeqNum( sessionID, message )
    except fix.FieldNotFound as _e:
        # logger.debug( 'Caught FieldNotFound=%s' % str(e) )
        logger.debug( 'Caught FieldNotFound')

def _resetSeqNum( sessionID, message ):
    text = message.getField( fut.Tag_Text )

    p = text.split(' ') # 'Logon seqnum 60 is lower than expected seqnum 255'
    if p[:2] == [ 'Logon', 'seqnum' ] and p[3:8] == 'is lower than expected seqnum'.split(' '):
        clientNum, gateNum = int( p[-1] ), 0
        seqnumutil.setSeqNums( clientNum, gateNum )
        seqnumutil.resetSeqNums( sessionID )

    #MsgSeqNum too low, expecting 543 but received 235
    elif p[:3] == [ 'MsgSeqNum', 'too', 'low,' ] and p[3] == 'expecting':
        clientNum, gateNum = int( p[4] ), 0
        seqnumutil.setSeqNums( clientNum, gateNum )
        seqnumutil.resetSeqNums( sessionID )

class AppThread( object ):
    def __init__(self, cfgpath, app, loop=False ):
        self._app   = app
        self._loop  = loop
        self._file  = cfgpath
        logger.debug('cfgpath = %s', cfgpath)

    def getApplication(self):
        return self._app

    def run( self ):
        try:
            self._settings    = fix.SessionSettings( self._file )
            self._storeFactory= fix.FileStoreFactory( self._settings )
            #self._logFactory  = fix.FileLogFactory( self._settings )
            self._logFactory  = fix.ScreenLogFactory( self._settings )
            self._initiator   = fix.SocketInitiator( self._app, self._storeFactory, self._settings, self._logFactory )
            self._initiator.start()
        except (fix.ConfigError, fix.RuntimeError), _e:
            logger.error( traceback.format_exc() )

def toVal(k,v):
    return str(v)

def toStr(c):
    nc = {}
    for k,v in c.iteritems():
        nc[str(k)] = toVal(k,v)
    return nc

