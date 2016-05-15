'''
turf.util module
ilya presman, 2012
'''

import robbie.turf.repo as repo

def get( turf, component, sub=None ):
    r = repo._conf[turf][component]
    if sub:
        return r[sub]
    else:
        return r

def exists( turf, component=None, sub=None ):
    if turf in repo._conf:
        if component in repo._conf[turf]:
            if sub:
                return sub in repo._conf[turf][component]
            else:
                return True
    return False

def turfNames():
    return repo._conf.keys()

