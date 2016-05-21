'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : tweak.value module
'''

import robbie.util.tmp as tmplib
import robbie.tweak.func as twfunc
import robbie.util.compat as compat
import robbie.util.calendar as calendar

def getRobbieTempRoot( typ ):
    if typ == 'env_tmpRoot':
        username = getenv( 'env_userName' )
        return tmplib.getUserTempRoot( username )
    raise ValueError( 'Unknown type = %s' % str( typ ) )

_access     = {}
_setvalues  = {}
_argsvalues = {}
_funcvalues = {
    'today'             : calendar.getdate,
    'run_turf'          : twfunc.const( None ),    
    'run_margotRoot'    : twfunc.const( None ),
    'run_tradeDate'     : calendar.getdate,
    'run_session'       : calendar.getsession,
    'run_domain'        : twfunc.const( 'echo' ),
    'env_userName'      : compat.getenv,
    'env_origUserName'  : compat.getenv,
    'env_tmpRoot'       : getRobbieTempRoot,
    'env_inStarbucks'   : twfunc.const( False ),
    'env_loggerDir'     : twfunc.const( False ),    
    'debug_level'       : twfunc.const( None ),

    'agt_strat'         : twfunc.const( None ),
}

def getval( name ):
    global _setvalues
    return _setvalues.get( name, None )

def permission( name, val ):
    global _access
    if name in _access and 'RO' in _access[ name ]:
        raise ValueError( 'Can not change read-only variable %s %s->%s' % ( name, getval( name ), val ) )

def setperm( name, al ):
    global _access
    if name in _access:
        oal = _access[ name ]
        if 'RO' in oal and al != 'RO':
            raise ValueError( 'Can not re-assign perm to a read-only %s %s->%s' % ( 
                               name, getval( name ), str( ( oal, al ) ) ) 
                             )
    _access[ name ] = al
    
def setval( name, val ):
    global _setvalues, _access
    permission( name, val )
    _setvalues[ name ] = val

def unsetval( name ):
    global _setvalues
    del _setvalues[ name ]

def isset( name ):
    global _setvalues
    return name in _setvalues

def allset( name, val ):
    global _setvalues
    return _setvalues.keys()

def isdefined(name, val):
    global _setvalues, _funcvalues
    return name in _setvalues or name in _funcvalues

def alldefined():
    global _setvalues, _funcvalues
    return set( sorted( _setvalues.keys() + _funcvalues.keys() ) )

def getenv( name, throwIfNone=False ):
    global _setvalues, _funcvalues, _argsvalues
    
    found = False
    if name in _setvalues:
        val = _setvalues[ name ]
        found = True

    elif name in _funcvalues:
        found = True
        if name in _argsvalues:
            val = _funcvalues[ name ]( name, _argsvalues[ name ] )
        else:
            val = _funcvalues[ name ]( name )

    if not found:     
        raise ValueError( 'Unknown tweak name=%s' % str( name ) )
    
    if throwIfNone and val == None:
        raise ValueError( 'None for tweak name=%s' % str( name ) )

    return val
