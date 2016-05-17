'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : tweak.func module - support functions for tweak
'''

def const( val ):
    def _const( name ):
        return val
    return _const

def runtag( name ):
    ''' we default it to today '''
    import robbie.tweak.value as twkval
    return str( twkval.getenv( 'today' ) )
