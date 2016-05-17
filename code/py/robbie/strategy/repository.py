import robbie.strategy.repository_util as reputil

initWithZeros = reputil.initWithZeros

def init():
    import robbie.strategy.repository_golden as repo_gold

    reputil.clear()
        
    repo_gold.init()

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
