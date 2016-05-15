'''
'''

from meadow.lib.logging import logger
import meadow.lib.dataacquisition as daq

'''BID
ASK
LAST_PRICE

IBM US Equity,1
MMM US Equity,2

39491,1

'''

class BBGConfiger( object ):
    
    def __init__(self, fields, symbols, venues ):
        self._fields    = fields
        self._symbols   = symbols
        self._venues    = venues
    
    def config(self, stream ):
        for c in self._fields:
            stream.write( c + '\n' )
            
        stream.write( '\n' )
        
        for c in self._symbols:
            stream.write( c + '\n' )
            
        stream.write( '\n' )
        
        for c in self._venues:
            stream.write( c + '\n' )

        stream.write( '\n' )
        stream.write( '\n' )

class BBGOutputLineParser( object ):
    '''
    parse bloomberg output line
    '''
    
    def __init__( self, conf = None ):
        self._conf  = conf
        self._BAT   = set( 'BAT' )
        self._header= ( 'type', 'secId', 'price', 'size', 'ts_hour', 'ts_minute', 'ts_second', 'ts_microsecond', 'exId' )
    
    def parse(self, line ):
        # self._proper = False        
        # line = line.strip()
        
        if len( line ) < 4:
            return 

        if line[0] == '(' and line[1] == "'" and line[3] == "'":
            typ = line[2]            
            try:
                if typ == 'S':
                    line = line.strip()
                    ( typ, secId, msg ) = eval( line )
                    return ( typ, secId, msg )
                else:
                    # self._type  = typ 
                    return daq.parsBBG( line )
            except:
                logger.error('can not parse %s' % str( line ) )

    def header(self, line ):
        return self._header

# a few global constants
typeix, secIdix, priceix, sizeix, ts_hourix, ts_minuteix, ts_secondix, ts_msix, exIdix = [None] * 9
knownTypes = ( 'type', 'secId', 'price', 'size', 'ts_hour', 'ts_minute', 'ts_second', 'ts_microsecond', 'exId' )
def initStandardBBGHeaderStruct( header ):
    '''
    update indices
    ( 'type', 'secId', 'price', 'size', 'ts_hour', 'ts_minute', 'ts_second', 'ts_microsecond', 'exId' )
    '''
        
    global typeix, secIdix, priceix, sizeix, ts_hourix, ts_minuteix, ts_secondix, ts_msix, exIdix
    global knownTypes
    name2ix   = dict( ( n, ix ) for ( ix, n ) in enumerate( header ) )
    typeix, secIdix, priceix, sizeix, ts_hourix, ts_minuteix, ts_secondix, ts_msix, exIdix = [ name2ix[n] for n in knownTypes ]

class BBGUpdater2( object ):

    '''standard update(er) object for the bloomberg price server'''
    def __init__(self, cacheData, header, debug ):
        initStandardBBGHeaderStruct( header )
        priceArrIx, cumSizeIx, sizeArrIx   = 0, 1, 2
        
        self._cacheData = cacheData
        self._debug     = debug
                
        self._cacheData[ 'ACCUMED_TRADE' ] = []
        
        ac = self._cacheData[ 'ASK'        ]
        self._acp = ac[ priceArrIx ]
        self._acc = ac[ cumSizeIx  ]
        self._acs = ac[ sizeArrIx  ]
        
        bc = self._cacheData[ 'BID'        ]
        self._bcp = bc[ priceArrIx ]
        self._bcc = bc[ cumSizeIx  ]
        self._bcs = bc[ sizeArrIx  ]
        
        tc = self._cacheData[ 'TRADE'      ]
        self._tcp   = tc[ priceArrIx ]
        self._tcc   = tc[ cumSizeIx  ]
        self._tcs   = tc[ sizeArrIx  ]

        ct = self._cacheData[ 'CUM_TRADE'  ]
        self._ctcp  = ct[ priceArrIx ]
        self._ctcc  = ct[ cumSizeIx  ]
        self._ctcs  = ct[ sizeArrIx  ]
        
        self._symbolCache   = self._cacheData[ 'SYMBOL'     ]
        self._TrdQtCntCache = self._cacheData[ 'TRADE_QUOTE_COUNT' ]
        
        self._LstEvtTmeCache = self._cacheData[ 'LAST_EVENT_TIME' ][ 0 ]

    def update( self, data ):
        global typeix, secIdix, priceix, sizeix, ts_hourix, ts_minuteix, ts_secondix, ts_msix, exIdix
                
        typ = data[ typeix  ]
        ix  = data[ secIdix ]
        tradeCntIx, quoteCntIx  = 0, 1
        
        if typ == 'B':
            volume  = data[ sizeix  ] * 100
            
            self._bcp[ ix ]  = data[ priceix ]
            self._bcc[ ix ] += volume
            self._bcs[ ix ]  = volume
            
            self._TrdQtCntCache[ quoteCntIx ][ ix ] += 1
            self._LstEvtTmeCache[ 0 ] = data[ ts_minuteix ]
            self._LstEvtTmeCache[ 1 ] = data[ ts_secondix ]
        
        elif typ == 'A':
            volume  = data[ sizeix  ] * 100

            self._acp[ ix ]  = data[ priceix ]
            self._acc[ ix ] += volume
            self._acs[ ix ]  = volume
            self._LstEvtTmeCache[ 0 ] = data[ ts_minuteix ]
            self._LstEvtTmeCache[ 1 ] = data[ ts_secondix ]
        

        elif typ == 'T':
            price   = data[ priceix ]
            volume  = data[ sizeix  ]
            
            self._tcp[ ix ]  = price
            self._tcc[ ix ] += volume
            self._tcs[ ix ]  = volume
            
            self._ctcp[ ix ] += price * volume
            self._ctcc[ ix ] += volume
            self._ctcs[ ix ]  = price * volume
            
            self._TrdQtCntCache[ tradeCntIx ][ ix ] += 1
            self._LstEvtTmeCache[ 0 ] = data[ ts_minuteix ]
            self._LstEvtTmeCache[ 1 ] = data[ ts_secondix ]
        
            
        elif typ == 'S':
            ix = int(ix)
            priceArrIx, cumSizeIx, sizeArrIx   = 0, 1, 2
            self._symbolCache[ priceArrIx ][ ix ]  = ( data[ priceix ] == 'SubscriptionStarted' )
            