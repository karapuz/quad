import robbie.util.calendar as cal
import robbie.util.space as libspace

def getMIDs( stratName, endDate=None ):
    ''' query strategy for MIDs '''
    import robbie.strategy.repository as strategyrep
    strategyrep.init()
    
    endDate = endDate if endDate else cal.today()
     
    _instance, params = strategyrep.getStrategy( endDate=endDate, strategyName=stratName )
    space = params[ 'GetData' ][ 'SymbolSpace' ]
    return libspace.getMIDs( space )


'''
import meadow.strategy.stratinfo as stratinfo

stratinfo.getMIDs( 'COLIBRI_V1' )

'''