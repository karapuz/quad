# ------------------------------------------------------------
# calclex.py
#
# tokenizer for a simple expression evaluator for
# numbers and +,-,*,/
# ------------------------------------------------------------
from ply import lex

# List of token names.   This is always required
tokens = (
   'KEYWORD',
   'NUMBER',
   'OP',
   'PAREN',
   'SPACE',
   'COLUMN',
   'QUOTED_TEXT',
   'VARIABLE',
   'QUOTES',
   'COMMENT',
)

def t_COMMENT(t):
    r'\#.*\n'
    print '##  --->"%s"' % t.value

def t_KEYWORD(t):
    r'(for )|(while )|(def )|(with )|(if )|(in )|(not )'
    print 'KW  --->"%s"' % t.value

def t_QUOTED_TEXT(t):
    r"['\"][a-zA-Z0-9_]*['\"]"
    print 'TXT --->"%s"' % t.value

def t_QUOTES(t):
    r"['\"]"
    print 'QT  --->"%s"' % t.value

def t_COLUMN(t):
    r":"
    print 'CL  --->"%s"' % t.value

def t_OP(t):
    r'[\+-/\*=\\|<>%]'
    print 'OP  --->"%s"' % t.value

def t_PAREN(t):
    r'[\)\(\]\[\}\{]'
    print 'PN  --->"%s"' % t.value

def t_VARIABLE(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    print 'VAR --->"%s"' % t.value

def t_SPACE(t):
    r'[ \t]+'
    print 'SP  --->"%s"' % t.value

# A regular expression rule with some action code
def t_NUMBER(t):
    r'\d+'
    print 'NM  --->"%s"' % t.value

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)
    print 'LN  --->"%s"' % t.value

# Error handling rule
def t_error(t):
    print "Illegal value '%s'" % t.value
    # t.skip(1)

def run():
    # Build the lexer
    lex.lex()

    # Test it out
    # data = '''
    # 3 + 4 * 10 * xyz
    #   + -20 *2
    # '''

    # path = r'C:\Users\ilya\GenericDocs\dev\quad\code\py\robbie\example\ply\source.py'
    path = r'C:\Users\ilya\GenericDocs\dev\quad\code\py\robbie\example\ply\example6.py'
    with open(path) as fd:
        data = fd.read()
    # Give the lexer some input
    lex.input(data)

    # Tokenize
    while 1:
        tok = lex.token()
        if not tok: break      # No more input
        # print tok

if __name__ == '__main__':
    run()