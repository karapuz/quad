import pylab
import numpy

def plots( tss, title ):
    pylab.figure()
    N = len( tss )
    iplot = 0
    for n,ts in zip( ('costs', 'realized' ), tss ):
        keys = sorted( ts.keys() )
        vals = [ numpy.mean( ts[k] ) for k in keys ]
        pylab.hold( False )
        pylab.subplot( N, 1, iplot+1 )
        pylab.plot( keys, vals, 'o' )
        pylab.hold( True )
        pylab.plot( keys, vals )
        pylab.title( '%s %s' % ( n, title ) )
        title = ''
        pylab.grid()
        iplot += 1
        
def plot( ts, title ):
    pylab.figure()
    keys = sorted( ts.keys() )
    vals = [ numpy.mean( ts[k] ) for k in keys ]
    pylab.plot( keys, vals, 'o' )
    pylab.hold( True )
    pylab.plot( keys, vals )
    pylab.title( title )
    pylab.grid()

def simpleplot( title, vals ):
    pylab.figure()
    
    if isinstance( vals, ( tuple, list ) ):
        N = len( vals )
        
        for iplot, data in enumerate( vals ):
            pylab.hold( False )
            pylab.subplot( N, 1, iplot+1 )
            pylab.plot( data, 'o' )
            pylab.hold( True )
            pylab.plot( data )
            pylab.title( title[iplot] )
            pylab.grid()
    else:
        raise ValueError( 'Cannot handle this data!')
