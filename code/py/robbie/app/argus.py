'''
AUTHOR      : ilya presman, 2016
TYPE:       : app
DESCRIPTION : app.argus module
'''

import os
import time
import os.path
import argparse
import threading
import subprocess
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.util.margot as margot

def component(logRoot, logName, python, prog, args):
    stdout = os.path.join( logRoot, logName)
    with open( stdout, 'w' ) as fdStdout:
        logger.debug( 'executing: %s' % str( python + prog + args ) )
        subprocess.call(python + prog + args, stdin=None, stdout=fdStdout, stderr=None, shell=False)

def component2(textWidget, logRoot, logName, python, prog, args):
    stdOut = os.path.join( logRoot, logName)
    with open( stdOut, 'w' ) as fdStdout:
        p = subprocess.Popen(python + prog + args,
                             stderr=subprocess.PIPE)
        for l in iter(p.stdout.readline, b''):
            textWidget.append(l)
            fdStdout.write(l)

def run_argus():
    turf        = twkval.getenv('run_turf')
    agetnList   = turfutil.get(turf=turf, component='agents')
    argusConf   = turfutil.get(turf=turf, component='argus')

    domain  = twkval.getenv('run_domain')
    session = twkval.getenv('run_session')
    user    = twkval.getenv('env_userName')

    logRoot = margot.getLogRoot( domain, user, session, create=True )
    logger.debug('logRoot=%s', logRoot)

    threads = []
    python  = argusConf['python']
    for name in argusConf['components']:
        prog    = argusConf[name]['prog']
        logName = argusConf[name]['logName']
        args    = ['--turf=%s' % turf]

        kwargs = dict(logRoot=logRoot, logName='%s.log' % logName, python=python, prog=prog, args=args)
        thread = threading.Thread(target=component, kwargs=kwargs)
        thread.start()
        threads.append( thread )
        time.sleep(5)

    for strat in agetnList:
        prog    = argusConf['agent']['prog']
        args    = ['--turf=%s' % turf, '--strat=%s' % strat ]

        kwargs = dict(logRoot=logRoot, logName='%s.log' % strat, python=python, prog=prog, args=args)
        thread = threading.Thread(target=component, kwargs=kwargs)
        thread.start()
        threads.append( thread )
        time.sleep(5)

    prog    = argusConf['bb2']['prog']
    logName = argusConf['bb2']['logName']
    args    = ['--turf=%s' % turf]

    kwargs = dict(logRoot=logRoot, logName='%s.log' % logName, python=python, prog=prog, args=args)
    thread = threading.Thread(target=component, kwargs=kwargs)
    thread.start()
    threads.append( thread )
    time.sleep(5)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    '''
    -T turf
    -S strat
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
    }
    logger.debug( 'agent: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_argus()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\app\argus.py --turf=ivp_redi_fix
'''
