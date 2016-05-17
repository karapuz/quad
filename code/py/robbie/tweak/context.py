'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : tweak.contenxt module
'''

import robbie.tweak.value as twval

class Tweaks:
    
    def __init__(self, **tweaks ):
        self._tweaks    = tweaks        
        self._setval    = {}
        self._unset     = set()
        
    def __enter__( self ):
        for k,v in self._tweaks.iteritems():
            if twval.isset( k ):
                self._setval[ k ] = twval.getval( k )
            else:
                self._unset.add( k )
            twval.setval( k, v )
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb ):
        for k,v in self._setval.iteritems():
            twval.setval( k, v )
        for k in self._unset:
            twval.unsetval( k )
        return False
    
    def tweaks(self):    
        return self._tweaks
        
    def setvals(self):    
        return self._setval
    
    def unset(self):
        return self._unset
