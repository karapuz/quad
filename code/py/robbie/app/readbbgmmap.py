import time
import numpy
import threading
import datetime

import robbie.lib.winston as winston
import robbie.lib.calendar as cal
import robbie.lib.context as libcx
import robbie.lib.space as libspace
from   optparse import OptionParser
import robbie.tweak.context as twkcx
import robbie.argus.util as argusutil
from   robbie.lib.logging import logger
import robbie.order.relation as relation
import robbie.lib.mmap_array as mmap_array
import robbie.lib.journalling as journalling
import robbie.rsrch.config.symbol as rcsymbol
import robbie.argus.initialposition as initialposition

from   robbie.lib.symbChangeDB import symbDB 

import robbie.tweak.value as twkval
import robbie.lib.config as libconf

symbolName  = '20130404'
fastSymbols = set( rcsymbol.names[ symbolName ] )

def getRelationVesion():
    return getVersion( component='relation', varName=mmap_array.RelationVersion )

def getBbgVesion():
    return getVersion( component='marketdata', varName=mmap_array.BbgVersion )
    
def getVersion( component, varName ):
    
    turf    = twkval.getenv( 'run_turf' )
    domain  = libconf.get( turf=turf, component=component, sub='domain' )    
    tweaks  = {}
    if libconf.exists( turf=turf, component=component, sub='owner' ):
        owner   = libconf.get( turf=turf, component=component, sub='owner' )
        wnDir   = libconf.get( turf=turf, component='bob', sub='winstonRoot' )[ owner ]
        tweaks[ 'run_winstonRoot'] = wnDir

    instanceName = libconf.get( turf=turf, component=component, sub='instance' )
    logger.debug( 'getVersion: turf=%s instanceName=%s component=%s varName=%s' % ( turf, instanceName, component, varName ) )
    
    with twkcx.Tweaks( ** tweaks ):
        return mmap_array.getVersion( domain=domain, instance=instanceName, varName=varName, create=True, debug=True )

def mrktDiff( mrk0, mrk1 ):
    if mrk0 and mrk1: 
        return ( mrk1 - mrk0 ) / abs( mrk0 )
    else:
        return numpy.sign( mrk1 - mrk0 )

def now():
    return datetime.datetime.strftime( datetime.datetime.now(),  '%H:%M:%S' )

def setSymbolCell( sheet, r, c, symbol ):
    '''
    C:\Users\ilya\Downloads\wxPython-3.0.2.0-cp27-none-win32.whl
    '''
    import wx
    sheet.SetCellValue( r, c, symbol )                    
    sheet.SetCellTextColour( r, c, 'white')                    
    sheet.SetCellBackgroundColour( r, c, 'dim gray')                    
    sheet.SetCellFont( r, c, wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD) ) #@UndefinedVariable
    sheet.SetCellAlignment(r, c, wx.ALIGN_CENTRE, wx.ALIGN_RIGHT ) #@UndefinedVariable

prevValues = {}
def run( op, columns, gui, thousands ):
    priceArrIx, _cumSizeIx, sizeArrIx   = 0, 1, 2
    turf        = twkval.getenv( 'run_turf' )
    flag        = argusutil.Flag( True )    
    marketData  = argusutil.newMarketData( create=False, readOnly=True )
    
    mids        = marketData[ 'MIDS' ]
    prices      = marketData[ 'TRADE'   ][ priceArrIx ]

    if not relation.sharedSpaceExists( varName='relation-realized' ):
        _relObj = relation.OrderState( readOnly=False, maxNum=relation.MAXNUM, mids=mids )
    
    relObj      = relation.OrderState( readOnly=True, maxNum=relation.MAXNUM, mids=mids )

    msymbs  = [ symbDB.MID2symb( MID=mid, date=tradeDate ) for mid in mids if mid ]    
    symbols = libspace.translateList2Vendor( msymbs, vendor='bbg' )
    ixs     = relObj.addTags( symbols )

    _mids, msymbs   = libspace.getListedMs( space=bbgp_space, date=None, alwaysRefresh=True )
    bbgSymbols      = libspace.translateList2Vendor( msymbs, vendor='bbg' )
    symbols_        = marketData[ 'SPACESYMBOLS'  ]
    
    if op != 'full' and symbols_ != bbgSymbols:
        logger.debug( 'Symbols in MMAP differ from listed!')
        time.sleep( 5 )

    maxLen      = max( ixs )
    
    rlzds       = relObj.getFullByType( posType='realized',     maxLen=maxLen )
    shpends     = relObj.getFullByType( posType='pendingShort', maxLen=maxLen )
    lnpends     = relObj.getFullByType( posType='pendingLong',  maxLen=maxLen )
    
    iExp        = initialposition.newInitialExposure( readOnly=True )
    iPrice      = initialposition.newInitialPrice( readOnly=True )
    
    iExpMap     = winston.loadInitialExposure( debug=True )
    iBlnSheet   = initialposition.computeExposure(iExpMap, relObj, isNetted=False )
    
    iBlnSheet   = iBlnSheet[:maxLen]        
    rprices     = prices[ :maxLen ]
    iExp_       = iExp[:maxLen] 
    iPrice      = iPrice[:maxLen] 


    if gui:
        import wx
        import robbie.lib.libgui as libgui
        import socket
                
        columns = 5
        N, M    = numpy.ceil( len( fastSymbols ) / columns ), columns * 8
        app     = wx.App() #@UndefinedVariable

        nb = libgui.Notebook( 
                parent      =None, 
                windowsId   =-1, 
                windowTitle ='%s, %s' % ( turf, socket.gethostname() ), N=N, M=M, 
                titles      = [ 'price', 'movers', 'contributors' ] 
        )
        libgui.mainLoop( app )

    def showPrices():
        sheet   = nb.sheets[ 0 ]
        
        subs    = marketData[ 'SYMBOL'  ][ 0 ]
        prices  = marketData[ 'TRADE'   ][ priceArrIx ]        
        sizes   = marketData[ 'TRADE'   ][ sizeArrIx  ]
        bids    = marketData[ 'BID'     ][ priceArrIx ]
        asks    = marketData[ 'ASK'     ][ priceArrIx ]        
        bidszs  = marketData[ 'BID'     ][ sizeArrIx  ]        
        askszs  = marketData[ 'ASK'     ][ sizeArrIx  ]

        def run_( ):
            global prevValues
                        
            count = 0
            for symbol, _kk, price, size, bid, ask, bidz, askz in zip( symbols_, subs, prices, sizes, bids, asks, bidszs, askszs ):
                if symbol not in fastSymbols:
                    continue
                bips    = ( ask-bid ) / ( ( ask + bid ) * .5 ) * 100 * 100
                vals = ( f % v for (f,v) in zip ( 
                        ( '%4s', '%6.2f', '%5d', '%5.2f', '%6.2f', '%5d', '%6.2f', '%5d',) ,
                        ( symbol, price, size, bips, bid, bidz, ask, askz ),
                        ) )
                rowcount    = numpy.floor( count / columns )
                columncount = ( count % columns )

                sheet.SetCellTextColour( rowcount, columncount * 8, 'white')                    
                sheet.SetCellBackgroundColour( rowcount, columncount * 8, 'dark green')                    
                sheet.SetCellFont(rowcount, columncount * 8, wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD) ) #@UndefinedVariable

                for si, sv in enumerate( vals ):
                    sheet.SetCellValue( rowcount, columncount * 8 + si, sv )
                    key = ( rowcount, columncount * 8 + si )
                    if key in prevValues:
                        
                        if prevValues[ key ] != sv:
                            sheet.SetCellValue( rowcount, columncount * 8 + si, sv )
                            if prevValues[ key ] > sv:
                                color = 'pink'
                            else:
                                color = 'green'
                                
                            if si not in ( 0, 2, 5, 7 ):
                                sheet.SetCellBackgroundColour(rowcount, columncount * 8 + si, color )
                        else:
                            if si not in ( 0, 2, 5, 7 ):
                                    sheet.SetCellBackgroundColour(rowcount, columncount * 8 + si, None )
                    else:
                        if si not in ( 0, 5, 7 ):
                            sheet.SetCellBackgroundColour(rowcount, columncount * 8 + si, None )
                        
                    prevValues[ key ] = sv
                    
                sheet.SetCellBackgroundColour( rowcount, columncount * 8+3, 'grey')                    
                sheet.SetCellTextColour( rowcount, columncount * 8+3, 'white')                    
                sheet.SetCellFont(rowcount, columncount * 8+3, wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD) )  #@UndefinedVariable
                count  += 1
                
        return run_

    def showMarkToMarket():
        sheet       = nb.sheets[ 1 ]
        
        firstrow    = 3
        width       = 5
        threshold   = 0.04
        columns     = 4
        
        if thousands:
            scalar      = 1e3
            extension   = 'k'
            floatfrmt   = '%6.2f'
        else:
            scalar      = 1
            extension   = ''
            floatfrmt   = '%8.0f'

        rowcount = 0
        for ix, title in enumerate( ( 'Mrk2Mrkt', 'Exposure', 'SOD BlnSht', 'RT BlnSht', 'Time' ) ):
            sheet.SetCellValue( rowcount, ix, title )
            sheet.SetCellTextColour( rowcount, ix, 'white' )                    
            sheet.SetCellBackgroundColour( rowcount, ix, 'dark blue' )                    
            sheet.SetCellFont( rowcount, ix, wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD) ) #@UndefinedVariable
        
        def run_( ):
            
            totalMmk1   = sum( ( rprices  - iPrice ) * ( rlzds + iExp_ ) )
            totalExp1   = sum( rprices * ( rlzds + iExp_ ) )
            sodBlnSheet = sum( numpy.abs( iPrice * iBlnSheet ) )
            rtBlnSheet  = sum( numpy.abs( rprices * ( rlzds + iBlnSheet ) ) )
            
            sheet.SetCellValue( 1, 0, ( floatfrmt + extension ) % ( totalMmk1/scalar ) )
            sheet.SetCellValue( 1, 1, ( floatfrmt + extension ) % ( totalExp1/scalar ) )
            sheet.SetCellValue( 1, 2, '%6.2fM' % ( sodBlnSheet/1e6 ) )
            sheet.SetCellValue( 1, 3, '%6.2fM' % ( rtBlnSheet/1e6 ) )
            sheet.SetCellValue( 1, 4, '%s' % ( now() ) )

            for cx in range( 5 ):
                sheet.SetCellAlignment(1, cx, wx.ALIGN_CENTRE, wx.ALIGN_RIGHT ) #@UndefinedVariable

            visuals = []
            count = 0
            for symbol, price, rlzd, _shpend, _lnpend, iexp, iprice in zip( symbols_, prices, rlzds, shpends, lnpends, iExp_, iPrice ):
                
                if not ( iexp or rlzd ):
                    continue
                
                mrk0    = iexp * iprice
                mrk1    = ( rlzd + iexp ) * price

                marked  = abs( mrktDiff( mrk0, mrk1 ) ) > threshold

                if not marked:
                    continue
                
                diff = abs( mrktDiff( mrk0, mrk1 ) ) 
                visuals.append( ( symbol, price, mrk0, mrk1, diff ) )
            
            visuals = sorted( visuals, key=lambda x: -x[ 4 ] )
            
            for symbol, price, mrk0, mrk1, diff in visuals:
                
                rowcount    = firstrow + numpy.floor( count / columns )
                columncount = ( count % columns )

                setSymbolCell( sheet, rowcount, columncount * width, symbol )
                diff  = mrktDiff( mrk0, mrk1 )
                
                vals = ( f % v for (f,v) in zip ( 
                        ( '%4s', '%6.2f', floatfrmt + '%s' % extension, floatfrmt + '%s' % extension, '%.0f%%' ),
                        ( symbol, price, mrk0/scalar, mrk1/scalar, diff  * 100 ),
                        ) )

                
                marked  = abs( mrktDiff( mrk0, mrk1 ) ) > threshold

                for si, sv in enumerate( vals ):
                    if si == 0:
                        continue
                    sheet.SetCellValue( rowcount, columncount * width + si, sv )
                    sheet.SetCellBackgroundColour( rowcount, columncount * width + si, 'light yellow')                    
                    sheet.SetCellAlignment(rowcount, columncount * width + si, wx.ALIGN_CENTRE, wx.ALIGN_RIGHT ) #@UndefinedVariable
                    if marked:
                        if  mrk1 - mrk0 > 0:
                            color   = 'green'
                            _color1  = 'YELLOW GREEN'
                            color2  = 'LIGHT GREY'
                        else:
                            color   = 'pink'
                            _color1  = 'INDIAN RED'
                            color2  = 'GREY'
                            
                        if si == 4:
                            sheet.SetCellBackgroundColour(rowcount, columncount * width + si, color )
                        else:
                            sheet.SetCellBackgroundColour(rowcount, columncount * width + si, color2 )
                            
                count  += 1
            
            # logger.debug( 'clean r=%s c=%s N=%s count=%s' % ( rowcount, columncount, N, count ) ) 
            for c in xrange( count + 1, int( N * columns ) ):
                columncount = ( c % columns )
                rowcount    = firstrow + numpy.floor( c / columns )
                for si in xrange( 5 ):
                    sheet.SetCellBackgroundColour(rowcount, columncount * width + si, 'white' )
                    sheet.SetCellValue( rowcount, columncount * width + si, '' )
                                
        return run_

    def showPosPrice():
        prices  = marketData[ 'TRADE'   ][ priceArrIx ]        
        maxLen  = len( mids )
        
        iExp    = initialposition.newInitialExposure( readOnly=True )
        iExp_   = iExp[:maxLen] 
        iPrice  = initialposition.newInitialPrice( readOnly=True )
        iPrice  = iPrice[:maxLen]
        
        width       = 5 
        firstrow    = 0
        sheet       = nb.sheets[ 2 ]
        mmkpos      = 4
        def run_():
            count   = 0
            visuals = []
            
            for symbol, price, iprice, iexp in zip( symbols_, prices, iPrice, iExp_ ):
                if not iexp:
                    continue

                mmk = ( price - iprice ) * iexp
                visuals.append( ( symbol, price, iprice, iexp, mmk ) )
            
            visuals = sorted( visuals, key=lambda x: -abs( x[ 4 ] ) )
            
            for symbol, price, iprice, iexp, mmk  in visuals:
                
                rowcount    = firstrow + numpy.floor( count / columns )
                columncount = ( count % columns )
                
                vals = ( f % v for (f,v) in zip ( 
                        ( '%4s', '%6.2f', '%6.2f', '%6.0f', '%6.0f' ),
                        ( symbol, price, iprice, iexp, mmk ),
                        ) )

                setSymbolCell( sheet, rowcount, columncount * width, symbol )
                for si, sv in enumerate( vals ):
                    if si == 0:
                        continue                    
                    sheet.SetCellValue( rowcount, columncount * width + si, sv )
                    
                if  mmk > 0:
                    color   = 'green'
                else:
                    color   = 'pink'
                
                sheet.SetCellBackgroundColour(rowcount, columncount * width + mmkpos, color )
                sheet.SetCellAlignment(rowcount, columncount * width + mmkpos, wx.ALIGN_CENTRE, wx.ALIGN_RIGHT ) #@UndefinedVariable

                count += 1        
        return run_

    def textPosPrice():        
        asks    = marketData[ 'ASK'   ][ priceArrIx ]        
        bids    = marketData[ 'BID'   ][ priceArrIx ]        
        asksizes= marketData[ 'ASK'   ][ sizeArrIx ]        
        bidsizes= marketData[ 'BID'   ][ sizeArrIx ]        
        prices  = marketData[ 'TRADE'   ][ priceArrIx ]        

        print '%5s %6s %6s %5s %6s %5s %8s %8s %6s' % ( 'symbol', 'price', 'ask', 'size', 'bid', 'size', 'rlzd', 'iexp', 'iprice' )

        mmks = 0        
        for symbol, price, ask, asksize, bid, bidsize, rlzd, iexp, iprice in \
                zip( symbols_, prices, asks, asksizes, bids, bidsizes, rlzds, iExp_, iPrice ):
            if iexp != 0 or rlzd != 0:
                mmk = ( price - iprice ) * ( rlzd + iexp )
                mmks += mmk 
                print '%5s %6.2f %6.2f %5d %6.2f %5d %8d %8d %6.2f : %6.2fk %6.2fk' % ( 
                    symbol, price, ask, asksize, bid, bidsize, rlzd, iexp, iprice, 
                    mmk/1e3, mmks/1e3 )
        
        print 'mmk = %sk' % ( mmks/1e3 )
        
    def showMmkAndPrices():
        runs = []
        runs.append( showPrices() )
        runs.append( showMarkToMarket() )
        runs.append( showPosPrice() )
        
        while 1:
            for run in runs:
                wx.FutureCall( 1, run )  #@UndefinedVariable
            time.sleep( 5 )
        
    if op == 'showmmk':
        t = threading.Thread( target=showMmkAndPrices )
    elif op == 'full':
        return textPosPrice()
    else:
        raise ValueError( 'Unknown operation=%s' % op )
    
    t.daemon = True
    interval = 60
    
    try:
        t.start()    
        while t.is_alive():
            t.join( interval )
    except KeyboardInterrupt as _e:
        logger.debug( 'mmap read is wrapping up' )
        flag.cont = False

if __name__ == '__main__':
    parser = OptionParser( usage='', version=1.0 )        
    parser.add_option('-T', '--turf',       action="store",     default=None,           dest='turf' )
    parser.add_option('-c', '--columns',    action="store",     default=3,              dest='columns' )
    parser.add_option('-p', '--operation',  action="store",     default='showmmk',    dest='operation' )
    parser.add_option('-s', '--thousands',  action="store_true",default=False,          dest='thousands' )
    parser.add_option('-g', '--gui',        action="store_true",default=False,          dest='gui' )
    
    (options, args) = parser.parse_args()
    
    tradeDate   = cal.today()
    bbgp_space  = journalling.jrnl_space
    turf        = options.turf

    tweaks      = {
        'run_tradeDate'     : tradeDate,
        'bbgp_space'        :bbgp_space,
        'run_mrktDtSharing' : 'mmap',
        'run_turf'          : turf,
    }        

    if options.operation == 'full':
        gui = False
    else:
        gui = options.gui
        
    with libcx.Pumpkin( absolute=datetime.time( 22, 00 ) ):    
        with twkcx.Tweaks( **tweaks ):            
            run( 
                op          = options.operation, 
                columns     = int( options.columns ),
                gui         = gui,
                thousands   = options.thousands,
            )
