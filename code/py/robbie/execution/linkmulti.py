'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.linkmulti module
'''

import os
import robbie.lib.config as libconf
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger

def init():
    import robbie.execution.fixlink as fixlink

    turf            = twkval.getenv( 'run_turf' )
    
    fix_connConfig  = libconf.get(turf=turf, component='inforeach' )
    fix_root        = os.path.join( logger.dirName(), 'fix' )
    
    with twkcx.Tweaks(
        fix_root       = fix_root,
        fix_connConfig = fix_connConfig ):
        
        app, thread    = fixlink.init()

    val = app, thread
    twkval.setval('exec_equity', val)
