'''
TYPE    : lib
OWNER   : ilya
'''

import os
import meadow.lib.config as libconf
import meadow.tweak.value as twkval 
import meadow.tweak.context as twkcx 
from   meadow.lib.logging import logger

def init():
    import meadow.execution.fixlink as fixlink 

    turf            = twkval.getenv( 'run_turf' )
    
    fix_connConfig  = libconf.get(turf=turf, component='inforeach' )
    fix_root        = os.path.join( logger.dirName(), 'fix' )
    
    with twkcx.Tweaks(
        fix_root       = fix_root,
        fix_connConfig = fix_connConfig ):
        
        app, thread    = fixlink.init()

    val = app, thread
    twkval.setval('exec_equity', val)
