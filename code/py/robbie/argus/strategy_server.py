'''
'''
from   optparse import OptionParser

import meadow.lib.calendar as cal
import meadow.tweak.util as twkutil
import meadow.tweak.value as twkval 
import meadow.lib.cache as libcache
import meadow.lib.config as libconf
import meadow.tweak.context as twkcx 
import meadow.lib.report as libreport
import meadow.argus.taskenv as taskenv
import meadow.argus.util as argus_util
from   meadow.lib.logging import logger
import meadow.argus.server_util as svrutil
import meadow.argus.component_util as cmputil

import meadow.argus.dailytask as dailytask
import meadow.lib.journalling as journalling

__version__ = "2.01"

usage   = '''\n\t%prog -p port -t exec,bbg,strat --sched=now+2m --fakebbg=randint
    --tasks    : bbg, jrnl, strat, exec, init
    --fakebbg  : randint
    --sched    : now+2m
'''

version = '%%prog %s' % __version__
    
if __name__ == '__main__':
    
    parser = OptionParser( usage=usage, version=version )
        
    parser.add_option('-k', '--fakebbg'    ,action="store"     ,default=None, dest='run_fakebbg')
    parser.add_option('-b', '--instarbucks',action="store_true",default=False, dest='instarbucks')
    parser.add_option('-s', '--sched',      action="store",     default=None, dest='argus_schedule')
    parser.add_option('-g', '--tag',        action="store",     default=None, dest='run_tag')
    parser.add_option('-d', '--debug',      action="store",     default=None, dest='debug')
    parser.add_option('-t', '--tasks',      action="store",     default=None, dest='tasks')
    parser.add_option('-T', '--turf',       action="store",     default=None, dest='turf')
    (options, args) = parser.parse_args()

    taskenv.setObj('env', 'application', 'argus' )
    argus_util.resetLogger()

    logger.debug( '>>> args = %s' % str( args ) )

    if args:
        libreport.reportAndKill( txt='Unknown options=%s' % str( args ), subject='Process is killed', sendFrom=None, sendTo=None )

    if not options.tasks:
        libreport.reportAndKill( txt='Must have tasks specified', subject='Process is killed', sendFrom=None, sendTo=None )

    if options.instarbucks:
        twkval.setval('env_inStarbucks', True )

    turf        = options.turf
    if not libconf.exists( turf ):
        libreport.reportAndKill( 
            txt='Must have valid turf. Turf "%s" does not exist' % str( turf ) , 
            subject='Process is killed', sendFrom=None, sendTo=None )

    jrnlRoot    = journalling.getJournalRoot( create=False )
    logger.debug( 'jrnlRoot=%s' % jrnlRoot )

    bbgp_space  = journalling.jrnl_space
    
    run_env = libconf.get(turf=turf, component='type' )
    allowed_tweaks = libconf.get(turf=turf, component='argus', sub='allowed_tweaks' )
    tweaks = twkutil.allowedTurfOptions( allowed_tweaks, options, fatal=True )
    
    if 'run_tag' in tweaks:
        tweaks[ 'run_tradeDate' ]   = int( tweaks[ 'run_tag' ] )
    else:
        tweaks[ 'run_tradeDate' ]   = cal.today()
        tweaks[ 'run_tag'       ]   = cal.today()
    
    tweaks[ 'run_fakebbg'       ] = options.run_fakebbg
    tweaks[ 'run_env'           ] = run_env
    tweaks[ 'run_turf'          ] = turf
    tweaks[ 'jrnl_root'         ] = jrnlRoot
    tweaks[ 'bbgp_space'        ] = bbgp_space
    tweaks[ 'exec_components'   ] = options.tasks.split(',')
    
    with twkcx.Tweaks( **tweaks ):
        twkutil.showProdVars( tweaks )
        libcache.cacheInfo()
        factory = svrutil.createFactory( 
                        port        = libconf.get(turf=turf, component='argus', sub='port'), 
                        taskData    = cmputil.taskData, 
                        debug       = options.debug )
        cmputil.initComponents()
        
        firstExec   = 'always'
        tag         = 'PRESOD'

        dailytask.setTask( tag='PRESOD', taskName='resetserver', args={ 'server':factory._server } )
        dailytask.scheduleDailyTasks( logger=logger, tag=tag, firstExec=firstExec )
    
        svrutil.run()
