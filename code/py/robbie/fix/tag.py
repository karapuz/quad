'''
TYPE        : lib
OWNER       : ilya
DESCRIPTION : fix tags
'''

import quickfix as fix

LimitTagVal     = fix.OrdType_LIMIT
MarketTagVal    = fix.OrdType_MARKET

HndlInstPrivVal =  fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION
HndlInstPubVal  =  fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PUBLIC_BROKER_INTERVENTION_OK

_tag2name = {
    '1'  : 'Account',
    '6'  : 'AvgPx',    
    '7'  : 'BeginSeqNo',
    '8'  : 'BeginString',
    '9'  : 'BodyLength',
    '10' : 'CheckSum',
    '11' : 'ClOrdID',
    '14' : 'CumQty',
    '15' : 'Currency',    
    '16' : 'EndSeqNo',
    '17' : 'ExecID',
    '20' : 'ExecTransType',
    '21' : 'HandlInst',    
    '31' : 'LastPx',
    '32' : 'LastShares',
    '34' : 'MsgSeqNum',
    '35' : 'MsgType',
    '36' : 'NewSeqNo',
    '37' : 'OrderID',
    '38' : 'OrderQty',
    '39' : 'OrdStatus',
    '40' : 'OrderType',
    '41' : 'OrigClOrdID',
    '43' : 'PossDupFlag',    
    '44' : 'Price',    
    '49' : 'SenderCompID',
    '52' : 'SendingTime',
    '54' : 'Side',
    '55' : 'Symbol',
    '56' : 'TargetCompID',
    '58' : 'Text',
    '59' : 'TimeInForce',
    '60' : 'TransactTime',
    '63' : 'SettlmntTyp',
    '65' : 'SymbolSfx',
    '98' : 'EncryptMethod',
    '99' : 'StopPx',
    '100': 'Exchange',
    '108': 'HeartBtInt',
    '109': 'ClientID',          # will be used to signal to InfoReach where to drop copy
    '115': 'OnBehalfOfCompID',
    '122': 'OrigSendingTime',
    '123': 'GapFillFlag',    
    '150': 'ExecType',
    '151': 'LeavesQty',
    '167': 'SecurityType',    
    '209': 'AllocHandlInst',
    '231': 'ContractMultiplier',
    '141': 'ResetSeqNumFlag',
    '789': 'NextExpectedMsgSeqNum',
        
}

_name2tag = dict( ( val, name ) for ( name, val ) in _tag2name.iteritems() )

_tagVals = {
    'MsgType': {
        '0': 'Heartbeat',
        '1': 'TestRequest',    
        '2': 'ResendRequest',    
        '3': 'Reject',
        '4': 'SequenceReset',    
        '5': 'Logout',
        '6': 'IOI',    
        '7': 'Advertisement',
        '8': 'ExecutionReport',    
        '9': 'OrderCancelReject',
        'A': 'Logon',
        'B': 'News',
        'C': 'Email',
        'D': 'NewOrderSingle',
        'E': 'NewOrderList',
        'F': 'OrderCancelRequest',
        'G': 'OrderCancelReplaceRequest',
        'H': 'OrderStatusRequest',
        'J': 'AllocationInstruction',
        'K': 'ListCancelRequest',
        'L': 'ListExecute',
        'M': 'ListStatusRequest',
        'N': 'ListStatus',
        'P': 'AllocationInstructionAck',
        'Q': 'DontKnowTrade',
        'R': 'QuoteRequest',
        'S': 'Quote',
        'T': 'SettlementInstructions',
        'V': 'MarketDataRequest',
        'W': 'MarketDataSnapshotFullRefresh',
        'X': 'MarketDataIncrementalRefresh',
        'Y': 'MarketDataRequestReject',
        'Z': 'QuoteCancel',
        'a': 'QuoteStatusRequest',
        'b': 'MassQuoteAcknowledgement',
        'c': 'SecurityDefinitionRequest',
        'd': 'SecurityDefinition',
        'e': 'SecurityStatusRequest',
        'f': 'SecurityStatus',
        'g': 'TradingSessionStatusRequest',
        'h': 'TradingSessionStatus',
        'i': 'MassQuote',
        'j': 'BusinessMessageReject',
        'k': 'BidRequest',
        'l': 'BidResponse',
        'm': 'ListStrikePrice',
    },


    'Side' : {
        '1': 'Buy',
        '2': 'Sell',
        '3': 'BuyMinus',
        '4': 'SellPlus',
        '5': 'SellShort',
        '6': 'SellShortExempt',
        '7': 'Undisclosed',
        '8': 'Cross',
        '9': 'CrossShort',
    },

    'ExecTransType': {
        '0' : 'New',
        '1' : 'Cancel',
        '2' : 'Correct',
        '3' : 'Status',
    },
            
    'TimeInForce': {
        '0': 'DAY',
        '1': 'GTC',
        '2': 'OPG',
        '3': 'IOC',
        '4': 'FOK',
        '5': 'GTX',
        '6': 'GTD',
    },

    'OrderType' : {
        '1': 'Market',
        '2': 'Limit',
        '3': 'Stop',
        '4': 'StopLimit',
        '5': 'MarketOnClose',
        '6': 'WithOrWithout',
        '7': 'LimitOrBetter',
        '8': 'LimitWithOrWithout',
        '9': 'OnBasis',
        'A': 'OnClose',
        'B': 'LimitOnClose',
        'C': 'ForexMarket',
        'D': 'PreviouslyQuoted',
        'E': 'PreviouslyIndicated',
        'F': 'ForexLimit',
        'G': 'ForexSwap',
        'H': 'ForexPreviouslyQuoted',
        'I': 'Funari',
        'P': 'Pegged',
    },

   'OrdStatus' : {
        '0': 'New',
        '1': 'PartiallyFilled',
        '2': 'Filled',
        '3': 'DoneForDay',
        '4': 'Canceled',
        '5': 'Replaced',
        '6': 'PendingCancel',
        '7': 'Stopped',
        '8': 'Rejected',
        '9': 'Suspended',
        'A': 'PendingNew',
        'B': 'Calculated',
        'C': 'Expired',
        'D': 'AcceptedForBidding',
        'E': 'PendingReplace',
    },

    'ExecType': {
        '0': 'New',
        '1': 'PartialFill',
        '2': 'Fill',
        '3': 'DoneForDay',
        '4': 'Canceled',
        '5': 'Replaced',
        '6': 'PendingCancel',
        '7': 'Stopped',
        '8': 'Rejected',
        '9': 'Suspended',
        'A': 'PendingNew',
        'B': 'Calculated',
        'C': 'Expired',
        'D': 'Restated',
        'E': 'PendingReplace',
    },

}

_timeInForce= dict( (val,name) for (name,val) in _tagVals[ 'TimeInForce' ].iteritems() )
_orderType  = dict( (val,name) for (name,val) in _tagVals[ 'OrderType' ].iteritems() )
_msgType    = dict( (val,name) for (name,val) in _tagVals[ 'MsgType' ].iteritems() )


