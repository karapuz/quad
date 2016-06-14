'''
TYPE        : lib
OWNER       : ilya
DESCRIPTION : fix util
'''

import copy
import datetime

import quickfix as fix #@UnresolvedImport
import robbie.fix.tag as mftag

_tag2name       = mftag._tag2name
_name2tag       = mftag._name2tag
_tagVals        = mftag._tagVals
_timeInForce    = mftag._timeInForce
_msgType        = mftag._msgType

def mapMsgType( n ):
    global _msgType
    return _msgType[ n ]

def mapTimeInForce( name ):
    global _timeInForce
    return _timeInForce[ name ]

def tag2name( t ):
    global _tag2name
    return _tag2name.get(t,t)

def name2tag( t, frmt=int ):
    global _name2tag
    return frmt( _name2tag[t] )

# maps
Msg_Logout          = mapMsgType( 'Logout'          )
Msg_Logon           = mapMsgType( 'Logon'           )
Msg_Heartbeat       = mapMsgType( 'Heartbeat'       )
Msg_ExecReport      = mapMsgType( 'ExecutionReport' )
Msg_NewOrderSingle  = mapMsgType( 'NewOrderSingle' )

# maps
Tag_OrderStatus     = name2tag( 'OrdStatus'     )
Tag_ExecTransType   = name2tag( 'ExecTransType' )
Tag_ExecType        = name2tag( 'ExecType'      )
Tag_CumQty          = name2tag( 'CumQty'        )
Tag_OrderQty        = name2tag( 'OrderQty'      )
Tag_LastShares      = name2tag( 'LastShares'    )
Tag_LastPx          = name2tag( 'LastPx'        )
Tag_SendingTime     = name2tag( 'SendingTime'   )
Tag_Side            = name2tag( 'Side'          )
Tag_ExecId          = name2tag( 'ExecID'        )
Tag_MsgType         = name2tag( 'MsgType'       )
Tag_Text            = name2tag( 'Text'          )
Tag_Symbol          = name2tag( 'Symbol'        )
Tag_LeavesQty       = name2tag( 'LeavesQty'     )
Tag_CumQty          = name2tag( 'CumQty'        )
Tag_OrderId         = name2tag( 'OrderID'       )
Tag_OrigClOrdID     = name2tag( 'OrigClOrdID'   )
Tag_ClientOrderId   = name2tag( 'ClOrdID'       )
Tag_TransactTime    = name2tag( 'TransactTime'  )
Tag_OrderType       = name2tag( 'OrderType'     )
Tag_Price           = name2tag( 'Price'         )
Tag_Account         = name2tag( 'Account'       )
Tag_Currency        = name2tag( 'Currency'      )
Tag_TimeInForce     = name2tag( 'TimeInForce'   )
Tag_HandlInst       = name2tag( 'HandlInst'     )
Tag_SenderCompID    = name2tag( 'SenderCompID'  )
Tag_TargetCompID    = name2tag( 'TargetCompID'  )

# maps
Val_Side_BUY        = fix.Side_BUY
Val_Side_Sell       = fix.Side_SELL
#Val_Side_SellShort  = fix.Side_SELLSHT
#Val_Side_Sells      = set( ( Val_Side_SellShort, Val_Side_Sell ) )
Val_Side_Sells      = set( (Val_Side_Sell, ) )

Val_OrdType_Limit   = fix.OrdType_LIMIT
Val_OrdType_Market  = fix.OrdType_MARKET

Val_ExecType_Fill   = fix.ExecType_FILL
Val_ExecType_New    = fix.ExecType_NEW
Val_ExecType_PF     = fix.ExecType_PARTIAL_FILL
Val_ExecType_Cx     = fix.ExecType_CANCELED
Val_ExecType_Rx     = fix.ExecType_REJECTED

Val_OrderStatus_Fill= fix.OrdStatus_FILLED
Val_OrderStatus_PF  = fix.OrdStatus_PARTIALLY_FILLED
Val_OrderStatus_Cx  = fix.OrdStatus_CANCELED
Val_OrderStatus_Rx  = fix.OrdStatus_REJECTED
Val_OrderStatus_Fs  = set( ( Val_OrderStatus_Fill, Val_OrderStatus_PF ) ) 
Val_OrderStatus_Pnd = fix.OrdStatus_PENDING_NEW

Val_OrderStatus_Pnd_Cx      = fix.OrdStatus_PENDING_CANCEL
Val_OrderStatus_Stopped     = fix.OrdStatus_STOPPED
Val_OrderStatus_Suspended   = fix.OrdStatus_SUSPENDED

Val_TimeInForce_DAY =  mapTimeInForce( 'DAY' )


empty = {}
def tag2val( t,v ):
    global _tagVals, empty
    tt = tag2name(t)
    return tt,_tagVals.get( tt,empty).get(v,v)

def txt2list( row, ignore = [] ):
    l = row.split('\x01')
    s = []
    for e in l:
        if not e: continue
        p = tuple( e.split( '=' ) )
        if len(p) == 2:
            n,v = p
        elif len(p) == 3:
            n,v,v2 = p
            v = '->'.join( ( v,v2 ) )
        if n not in ignore:
            s.append( tag2val( n,v ) ) 
    return s

def split( row ):
    l = row.split('\x01')
    s = []
    for e in l:
        if not e:
            continue
        p = tuple( e.split( '=' ) )
        if len(p) == 2:
            n,v = p
            s.append( tag2val( n,v ) ) 
        elif len(p) == 3:
            n,v,v2 = p
            s.append( tag2val( n,( v,v2 ) ) ) 
    return s

def msg2dict( row ):
    return dict( split( row ) )

def transactionTime():
    '''create transaction time string'''
    
    now     = datetime.datetime.utcnow()
    tfmt    = '%Y%m%d-%H:%M:%S.%f'
    return now.strftime( tfmt )[:-3]
    
def create_NewOrderHeader( senderCompID, targetCompID):
    '''populate static header info of the message'''
    
    global Tag_SenderCompID, Tag_TargetCompID
    
    headerConfig = {
         8: 'FIX.4.2',
        35: 'D',
        # Tag_SenderCompID    : 'CLIENT1',
        # Tag_TargetCompID    : 'IREACH',
        Tag_SenderCompID    : senderCompID,
        Tag_TargetCompID    : targetCompID,
    }
    return headerConfig

def create_CancelHeader():
    '''populate static header info of the message'''
    
    global Tag_SenderCompID, Tag_TargetCompID
    
    headerConfig = {
         8: 'FIX.4.2',
        35: 'F',
        Tag_SenderCompID    : 'CLIENT1',
        Tag_TargetCompID    : 'IREACH',
    }
    return headerConfig

def create_staticNewOrderMsg( timeInForce ):
    '''populate static info of the message'''
    
    global Tag_Account, Tag_Currency, Tag_TimeInForce, Tag_HandlInst
    
    bodyConfig = {
        Tag_Account     : 'TEST_Account',
        Tag_Currency    : 'USD',
        Tag_TimeInForce : timeInForce,
        Tag_HandlInst   : mftag.HndlInstPubVal,
    }
    
    return bodyConfig

def create_staticCancelMsg():
    '''populate static info of the message'''
    global Tag_Account, Tag_Currency
    
    bodyConfig = {
        Tag_Account     : 'TEST_Account',
        Tag_Currency    : 'USD',
    }
    
    return bodyConfig

def create_NewOrderMsg( orderId, symbol, qty, price=None ):
    '''populate dynamic info of the message'''
    global Tag_ClientOrderId, Tag_Symbol, Tag_Side, Tag_OrderQty, Tag_TransactTime, Tag_OrderType
    
    bodyConfig = {
        Tag_ClientOrderId   : orderId,
        Tag_Symbol          : symbol,
        Tag_Side            : fix.Side_BUY if qty > 0 else fix.Side_SELL ,
        Tag_OrderQty        : str( abs( qty ) ),
        Tag_TransactTime    : transactionTime(),
    }
    
    if price:
        bodyConfig[ Tag_Price     ] = str( round( price, 2 ) )
        bodyConfig[ Tag_OrderType ] = fix.OrdType_LIMIT
    else:
        bodyConfig[ Tag_OrderType ] = fix.OrdType_MARKET

    return bodyConfig

def create_CancelMsg( orderId, origOrderId, symbol, qty ):
    '''populate dynamic info of the message'''
    global Tag_OrigClOrdID, Tag_ClientOrderId, Tag_Symbol, Tag_Side, Tag_OrderQty, Tag_TransactTime
    
    bodyConfig = {
        Tag_ClientOrderId   : orderId,
        Tag_OrigClOrdID     : origOrderId,
        Tag_Symbol          : symbol,
        Tag_Side            : fix.Side_BUY if qty > 0 else fix.Side_SELL ,
        Tag_OrderQty        : str( abs( qty ) ),
        Tag_TransactTime    : transactionTime(),
    }
    
    return bodyConfig

def form_NewOrder( senderCompID, targetCompID, timeInForce, orderId, symbol, qty, price=None, tagVal=None ):
    '''create a new order message a-new'''
    
    msg = fix.Message()
    hdr = msg.getHeader()


    for tag, val in create_NewOrderHeader(senderCompID, targetCompID).iteritems():
        hdr.setField( tag, val )

    for tag, val in create_staticNewOrderMsg( timeInForce ).iteritems():
        msg.setField( tag, val )
    
    for tag, val in create_NewOrderMsg( orderId=orderId, symbol=symbol, qty=qty, price=price ).iteritems():    
        msg.setField( tag, val )

    if tagVal != None:
        for tag, val in tagVal:
            msg.setField( tag, val )
        
    return msg

def form_Cancel( orderId, origOrderId, symbol, qty, tagVal ):
    '''create a cancel message'''
    
    msg = fix.Message()
    hdr = msg.getHeader()

    for tag, val in create_CancelHeader().iteritems():
        hdr.setField( tag, val )

    for tag, val in create_staticCancelMsg().iteritems():
        msg.setField( tag, val )
    
    for tag, val in create_CancelMsg( orderId=orderId, origOrderId=origOrderId, symbol=symbol, qty=qty ).iteritems():    
        msg.setField( tag, val )

    if tagVal != None:
        for tag, val in tagVal:
            msg.setField( tag, val )

    return msg

def form_incrNewOrder( msg, bag=None ):
    '''create a message incrementally '''
    
    msg = copy.deepcopy( msg )
    if not bag:
        return msg
    
    for tag, val in bag.iteritems():    
        msg.setField( tag, val )
    return msg

def add_Login( msg ):
    '''create a message a-new'''
    msg.setField( name2tag( 'ResetSeqNumFlag'), 'Y' )

def convertQty( side, qty ):
    ''' convert to signed quantity '''
    
    global Val_Side_Sells
    
    if side in Val_Side_Sells: 
        return -qty
    else: 
        return qty

