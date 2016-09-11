'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.logging module
'''

import os
import datetime
import robbie.tweak.value as twkval
import robbie.util.margot as margot
from   robbie.util.logging import Logger, STD_TIMESTAMP_FORMAT, logger

class FileLogger(object):
    def __init__(self, root, name, attrs, flush=False, debug=True, l=STD_TIMESTAMP_FORMAT):
        #super(FileLogger,self).__init__(l=l)
        self._l     = l
        self._d         = datetime.datetime
        self._fd    = None
        self._root  = root

        if not os.path.exists(self._root):
            os.makedirs(self._root)

        self._name  = name
        self._path  = os.path.join( self._root, self._name + '.csv')
        if debug:
            logger.debug('FileLogger: path=%s', self._path)
        self._fd    = open( self._path, 'w' )

        self._flush = flush
        self._attrs = attrs
        args = dict( (n,n) for n in self._attrs)
        self._fd.write( self._format( self._timesign(), 'DEBUG', label='Name', args=args) )

    def _timesign(self):
        return self._d.now().strftime(self._l)

    def debug(self, label, args):
        self._fd.write( self._format( self._timesign(), 'DEBUG', label, args) )

    def error(self, label, args):
        self._fd.write( self._format( self._timesign(), 'ERROR', label, args) )

    def __del__(self):
        if self._fd:
            self._fd.flush()
        else:
            logger.debug('FileLogger: _fd was never created!')

    def _format( self, timestamp, typeName, label, args):
        s = '%s,%s,%s,%s\n' % ( timestamp, typeName, label, self._args2tuple( args ) )
        return s

    def _args2tuple( self, args ):
        return ','.join(
            str(args.get(k,'')) for k in self._attrs
        )

def getFileLogger(domain, user, session, name, attrs):
    #path = margot.getSessionSlice( domain=domain, user=user, session=session, create=True )
    logger.debug('getFileLogger: domain=%s, user=%s, session=%s, name=%s', domain, user, session, name)
    root  = margot._getSharedRoot( domain=domain, user=user, session=session, create=True )
    return FileLogger(root=root, name=name, attrs=attrs, flush=True)
