'''
'''

import threading
import traceback

import meadow.argus.taskenv as taskenv

import meadow.tweak.value as twkval 
import meadow.lib.report as libreport
from   meadow.lib.logging import logger

import meadow.argus.util as argusutil
import meadow.argus.taskrepository as repository
import meadow.argus.initialposition as initialposition  

__version__ = "2.01"

# indexed by taskName
taskData    = {
    'tasks'     : {},
    'params'    : {},
    'status'    : {},
    'started'   : {},
    'timers'    : {},
}

def initComponents():
    try:
        _initComponents()
    except:
        txt=traceback.format_exc()            
        libreport.reportAndKill(txt=txt, subject='Argus failed to initalize', sendFrom='argus', sendTo='ipresman' )

_allComps    = ( 'bbg', 'jrnl', 'strat', 'init' )        
def _initComponents():
    import meadow.argus.bbgtask as bbgtask
    import meadow.lib.space as libspace
    from   meadow.lib.symbChangeDB import symbDB
    
    components  = twkval.getenv( 'exec_components' )
    tradeDate   = twkval.getenv( 'run_tradeDate')
    logger.debug( 'initComponents: components=%s' % (  str( components ) ) )
    
    print 'initComponents: components=%s' % (  str( components ) )
    
    for e in components:
        if e not in _allComps:
            libreport.reportAndKill( 
                txt='Unknown component = %s' % str( e ), 
                subject='Process is killed', sendFrom=None, sendTo=None )
        
    if not components:
        libreport.reportAndKill( txt='No components', subject='Process is killed', sendFrom=None, sendTo=None )
    
    env = 'dev'
    if 'bbg' in components:
        marketData  = argusutil.newMarketData( readOnly=False, create=True )
        taskenv.setObj('env', 'marketData', marketData )
        
        taskPath    = ( 'bbg', env )
        taskObj     = bbgtask.BBGPriceTask( marketData=marketData ) 
        repository.setTask( taskPath, taskObj )

    if 'jrnl' in components:
        taskPath    = ( 'journal', env )
        # taskObj     = bbgtask.BBGJournalTask( marketData=marketData ) 
        taskObj     = bbgtask.BBGJournalTaskSingleThread( marketData=marketData, startTime='09:29', stopTime='16:01' ) 
        repository.setTask( taskPath, taskObj )

    if  ( 'strat' in components ) or ( 'init' in components ):        
        import meadow.order.manager as mom
        import meadow.argus.exectask as exectask
        import meadow.order.relation as relation
        import meadow.execution.linkmulti as links
        
        marketData  = argusutil.newMarketData( readOnly=True, create=False )
        taskenv.setObj('env', 'marketData', marketData )

        mids    = marketData[ 'MIDS' ]
        msymbs  = [ symbDB.MID2symb( MID=mid, date=tradeDate ) for mid in mids if mid ]
        
        symbols = libspace.translateList2Vendor( msymbs, vendor='bbg' )
        logger.debug( 'initComponents: space=len %s, %s' % ( len( symbols ), str( symbols[:3] ) + '...' + str( symbols[-3:] ) ) ) 
        
        relObj  = relation.OrderState( readOnly=False, maxNum=relation.MAXNUM, mids=mids )
        relObj.addTags( symbols )
        
        taskenv.setObj('env', 'relations', relObj )

        links.init()
        initialposition.initExposureObj( relObj=relObj, asComponent=True, asMMap=True )
        initialposition.initPriceObj( relObj=relObj, asComponent=True, asMMap=True )
        
        if 'init' in components:
            libreport.reportAndKill( 
                txt='done with init', 
                subject='Process is killed', sendFrom=None, sendTo='ipresman' )

        app, _thrd      = twkval.getenv( 'exec_equity' )
        
        orderQueue      = taskenv.getObj('env', 'orderQueue' )
        initialExposure = taskenv.getObj('env', 'initialExposure' )
        
        orderManager    = mom.OrderManager( relObj=relObj, linkObj=app, initialExposure=initialExposure )
        taskenv.setObj('env', 'orderManager', orderManager )
        
        algoThread      = threading.Thread()
        algoThread.run  = exectask.newRunner( 
                            orderManager = orderManager, 
                            orderQueue   = orderQueue, 
                            marketData   = marketData, 
                            flag         = argusutil.Flag( True ) )
        algoThread.start()

    if 1:
        # we always have it for now
        import meadow.argus.runcommand as runcmd
        flag = argusutil.Flag( True )
        sleepInterval = 10
        runcmd.runner(flag=flag, sleepInterval=sleepInterval )
        logger.debug( 'initComponents: starting runcmd' ) 
