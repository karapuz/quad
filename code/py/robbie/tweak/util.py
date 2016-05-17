'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : tweak.util module
'''

import robbie.tweak.value as twkval
from   robbie.util.logging import logger

def isProdVars( name ):
    ''' detect important vars for the production '''
    return name.startswith('run_')

def showProdVars( tweaks=None, asStr=False ):
    ''' show important vars for the production '''
    names = set( [] )
    if asStr:
        s = '------ showProdVars ------------\n'
    else:
        logger.debug( '------ showProdVars ------------' )
        
    for name in twkval.alldefined():
        if isProdVars( name ):
            if asStr:
                s += '%-20s = %-20s' % ( name, twkval.getenv(name) ) + '\n'
            else:
                logger.debug( '%-20s = %-20s' % ( name, twkval.getenv(name) ) )
            names.add( name )
    if tweaks:
        for name in tweaks:
            if name not in names:
                if asStr:
                    s += '%-20s = %-20s' % ( name, twkval.getenv(name) ) + '\n'
                else:
                    logger.debug( '%-20s = %-20s' % ( name, twkval.getenv(name) ) )
    if asStr:
        return s

def allowedOptions( options, debug=True ):
    ''' if allowed_tweaks are present '''
    tweaks = {}
    if not hasattr( options, 'allowed_tweaks' ):
        if debug:
            logger.debug( 'no allowed_tweaks present' )
        return tweaks
    for name in options.allowed_tweaks:
        if hasattr( options, name ):
            val = getattr( options, name )
            tweaks[ name ] = val
        if debug:
            logger.debug( 'allowed_tweak %s=%s' % ( name, val ) )
    return tweaks

def checkIfTweaksSet( options, allDefined, fatal ):
    names = []
    for name in allDefined:
        if hasattr( options, name ) and getattr( options, name ):
            names.append( name )
    if names:
        if fatal:
            libreport.reportAndKill(txt=names, subject='Tweaks are not allowed', sendFrom=None, sendTo=None )
        else:
            raise ValueError( 'for current turf vars not allowed: %s' % str( names ) )

def allowedTurfOptions( allowed_tweaks, options, debug=True, fatal=False ):
    ''' if allowed_tweaks are present '''
    tweaks = {}
    if not allowed_tweaks:
        checkIfTweaksSet( options=options, allDefined=twkval.alldefined(), fatal=fatal )
        return tweaks
    
    logger.debug( 'allowed_tweaks=%s' % str( allowed_tweaks) )
    for name in allowed_tweaks:
        if hasattr( options, name ):
            val = getattr( options, name )
            if val != None:
                tweaks[ name ] = val
                if debug:
                    logger.debug( 'allowed_tweak: %12s=%12s' % ( name, val ) )
    return tweaks

def asUser( userName, func, args=None ):
    ''' run func as user '''
    import meadow.tweak.context as twkcx    
    with twkcx.Tweaks( env_userName=userName ):
        if args != None:
            return func( **args )
        return func()

def runWith( tweaks, func, args=None ):
    ''' run func wtih tweaks '''
    import meadow.tweak.context as twkcx    
    with twkcx.Tweaks( **tweaks ):
        if args != None:
            return func( **args )
        return func()

def allTweaks( tweaks=None ):
    tweaks = tweaks.copy() if tweaks else {}
    for name in twkval.alldefined():
        tweaks[ name ] = twkval.getenv( name )
    return tweaks
