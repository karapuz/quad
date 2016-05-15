import nxtimeddump as ntd
import cPickle as pickle

def function( priceList ):
    symbList = ['X']
    tradeList = ['T']
    askList = ['A']
    bidList = ['B']
    aggsList = ['G']
    for d in priceList:
        symbList.append( d[0] )
        tradeList.append( d[1] )
        askList.append( d[2] )
        bidList.append( d[3] )
        aggsList.append( d[4] )
    print symbList
    print tradeList
    print askList
    print bidList
    print aggsList
    return True

minutes = range( 34200000, 57660000, 60000 )

with open('test.pkl', 'wb') as f:
    def function2(priceList):
        pickle.dump( priceList, f, pickle.HIGHEST_PROTOCOL )
        return True
    
    ntd.processTape( '/data/data/NxCore/20130211.GS.nxc' ,
                     '/data/marketdata/nxcore/corrections/20130211.txt',
                     function2,
                     minutes )
    
