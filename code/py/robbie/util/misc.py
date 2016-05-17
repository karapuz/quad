'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.misc module
'''

import os
import numpy
import errno


def makeDirsIfNotExists( dirName, mode=None ):
    '''
    A replacement for the code:
    
    if not os.path.exists( dirName ):
        os.makedirs( dirName )
        
    '''
    
    if not os.path.exists( dirName ):
        return makeMissingDirs( dirName=dirName, mode=mode )
    
    return dirName

def makeMissingDirs( dirName, mode=None ):
    '''
    A replacement for the code:
    
    os.makedirs( dirName )
       
    which can result in a race condition between two processes trying to create
    the same dirName.  If one process creates the directory between another thread's
    if statement and os.makedirs the above code fails.  The code in this function will
    not fail.  
    '''
    try:
        if mode:
            os.makedirs( dirName, mode )
        else:
            os.makedirs( dirName )            
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    return dirName
