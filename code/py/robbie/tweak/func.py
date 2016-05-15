'''support funcs for the tweaks'''

def const( val ):
    def _const( name ):
        return val
    return _const

def runtag( name ):
    ''' we default it to today '''
    import robbie.tweak.value as twkval
    return str( twkval.getenv( 'today' ) )
