import os
import numpy

def readSlice( root, names, shape, dtype='float32' ):
  '''
  /tmp/mmaps/20160708/TRADE_QUOTE_COUNT-0.mmap"
  "TRADE", "ASK", "BID", "SYMBOL", "CUM_TRADE", "TRADE_QUOTE_COUNT", "LAST_EVENT_TIME"
  '''
  mode  = 'r'
  for name in names:
    path = os.path.join( root, name ) + '.mmap'
    arr  = numpy.memmap( path, dtype=dtype, mode=mode, shape=shape )
  return arr


'''
import robbie.util.bbgutil as bbgutil
reload( bbgutil )

root = '/tmp/mmaps/20160708'
arr = bbgutil.readSlice( root=root, names=['TRADE-0'], shape=(200,1), dtype='float32' )
'''
