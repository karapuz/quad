'''
TYPE        : lib
OWNER       : ilya
DESCRIPTION : various routines related to sequence number generation
'''
import os

import quickfix as fix
import robbie.fix.config as fixccfg
from   robbie.util.logging import logger

seqNum = None
def setSeqNums( client, gateNum ):
    global seqNum    
    seqNum = ( client, gateNum )
    logger.debug( 'seqNum: setting seqNum = %s' % str ( ( ( client, gateNum ) ) ) )

def getSeqNums( pn, typ='num' ):
    global seqNum
    
    if typ == 'header':
        logger.debug( 'seqNum: using header pn = %s' % pn )
    
        if not os.path.exists( pn ):
            seqNum  = (1,1)
            logger.debug( 'seqNum: header pn does not exist [%s]' % seqNum )
            logger.debug( 'seqNum: header setting seqNum = %s' % seqNum )
            return
                
        with open( pn ) as fd:
            txt = fd.read()
            
        pairs = txt.split( ' ' )
        for i in xrange(-1,-len(pairs),-1):
            triplet = pairs[ i ]
            if triplet:
                break
        triplet = triplet.split(',')
        seqNum  = ( int( triplet[0] ), int( triplet[0] ) )        
        logger.debug( 'seqNum: setting seqNum = %s' % str( seqNum ) )
        
    elif typ == 'seqnum':
        logger.debug( 'seqNum: using seqnum pn = %s' % pn )
    
        if not os.path.exists( pn ):
            seqNum  = ( 1 , 1 )
            logger.debug( 'seqNum: header pn does not exist [%s]' % str( seqNum ) )
            logger.debug( 'seqNum: header setting seqNum = %s' % str( seqNum ) )
            return
                
        with open( pn ) as fd:
            txt = fd.read()
            
        pair        = txt.split( ':' )
        clientNum   = int( int( pair[0] ) )
        gateNum     = int( int( pair[1] ) )
        seqNum      = ( clientNum, gateNum )
        logger.debug( 'seqNum: setting seqNum = %s' % str( seqNum ) )
    else:
        raise ValueError( 'Unknown type of pn = %s, type = %s' % ( str( pn ), str( typ ) ) )
    
def resetSeqNums( sessionID ):
    global seqNum
    logger.debug( 'session: setting seqNum = %s' % str( seqNum ) )
    clientNum, gateNum = seqNum
    session = fix.Session.lookupSession( sessionID )
    
    if clientNum > 0:
        session.setNextSenderMsgSeqNum( clientNum )
    if gateNum > 0:
        session.setNextTargetMsgSeqNum( gateNum )
    logger.debug( 'session: setting seqNum = %s' % str( seqNum ) )

def getHeaderFilePath( env, sender, target, fixVersion ):
    storePath   = fixccfg.getFIXConfig( env=env, tag='store', provider = 'inforeach' )
    return os.path.join( storePath, '%s-%s-%s.header' % ( fixVersion, sender, target) ) 

def getSeqNumFilePath( env, sender, target, fixVersion ):
    storePath   = fixccfg.getFIXConfig( env=env, tag='store', provider = 'inforeach' )
    return os.path.join( storePath, '%s-%s-%s.seqnums' % ( fixVersion, sender, target) ) 
