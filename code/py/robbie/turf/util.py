'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : turf.util module
'''

import robbie.turf.repo as repo

def get( turf, component, sub=None ):
    if not turf in repo._conf:
        raise ValueError('Unknown turf=%s' % turf)
    if not component in repo._conf[turf]:
        raise ValueError('Unknown component=%s in truf=%s' % (component, turf))
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

