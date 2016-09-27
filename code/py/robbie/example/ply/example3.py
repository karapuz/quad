from ply import lex

tokens = (
    "LOOP",
    "DEF",
    "TEXT",
)

def t_LOOP(t):
    r'for'
    print 'LOOP --->', t.value
    return t

def t_TEXT(t):
    r'.+'
    print 'TEXT --->', t.value
    return t

def t_DEF(t):
    r'def'
    print 'DEF --->', t.value
    return t

def t_error(t):
    print 'error --->', t.value
    return t

lex.lex()

def run():
    # p = r'robbie\example\ply\example3.py'
    # with open(p) as fd:
    #     txt = fd.read()
    #
    # lex.input(txt)
    txt = 'for a def b\n'
    lex.input(txt)

    for tok in iter(lex.token, None):
        print repr(tok.type), repr(tok.value)

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\ply\example3.py
'''