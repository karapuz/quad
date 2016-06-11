'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.symboldb module
DESCRIPTION : this module contains symboldb object
'''

_x      = 0
_m_s2i  = {}
_m_i2s  = {}

def symbol2id(symbols):
    _x      = max( _m_i2s.iterkeys() ) if _m_i2s else 0
    symIds  = []
    for s in symbols:
        if s not in _m_s2i:
            _x += 1
            _m_s2i[s] = _x
            _m_i2s[_x] = s
        symIds.append( _m_s2i[s] )
    return symIds

def currentSymbols():
    '''  current universe of symbols '''
    return (
        'IBM', 'MSFT', 'C', 'MS', 'AAPL', 'F', 'AMZN'
    )