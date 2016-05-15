import meadow.strategy.repository_util as reputil

initWithZeros = reputil.initWithZeros

def init():
    import meadow.strategy.repository_golden as repo_gold
    import meadow.strategy.repository_dragon as repo_dragon
    import meadow.strategy.repository_pegasus as repo_pegasus
    import meadow.strategy.repository_colibri as repo_colibri
    
    reputil.clear()
        
    repo_gold.init()
    repo_dragon.init()
    repo_pegasus.init()
    repo_colibri.init()
    
def reinit():
    init()

def show():
    init()
    return reputil.show()

def listNames():
    init()
    return reputil.listNames()
    
getStrategy     = reputil.getStrategy
setStrategy     = reputil.setStrategy
strategyExists  = reputil.strategyExists

if __name__ == '__main__':
    show()
