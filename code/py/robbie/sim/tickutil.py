from math import floor
import meadow.lib.nxcore as nxcore

def time2str( msTime ):
    seconds = msTime / 1000
    minutes = floor(seconds) / 60
    hours   = floor(minutes) / 60
    return '%i:%i:%i' % (floor(hours) , floor(minutes) % 60 , floor(seconds) % 60 )

if __name__ == '__main__':
    symbols     = set( [ 'eAAPL' ] )
    import meadow.lib.context as cx
    l = []
    with cx.Timer( 'loading' ) as t:
        nxcore.processFullTapeAsList( procDate=20130211, symbols=symbols )
    print 'Done', t.elapsed()
