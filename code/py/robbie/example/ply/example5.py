# ------------------------------------------------------------
# calclex.py
#
# tokenizer for a simple expression evaluator for
# numbers and +,-,*,/
# ------------------------------------------------------------
from ply import lex

# List of token names.   This is always required
tokens = (
   'FOR',
   'SPACE',
   'SEMICOLUMN',
   'OP',
   'VAR',
   'QUOTES',
)

# Regular expression rules for simple tokens
t_FOR           = r'for'
t_SPACE         = r'[ \t]'
t_SEMICOLUMN    = r':'
t_VAR           = r'[a-ZA-Z]'
t_OP  = r'/'

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    #t.skip(1)

# Build the lexer
lex.lex()

# Test it out
with open(r'C:\Users\ilya\GenericDocs\dev\quad\code\py\robbie\example\ply\source.py') as fd:
    data = fd.read()
    print 'input:', data

# Give the lexer some input
lex.input(data)

# Tokenize
while 1:
    tok = lex.token()
    if not tok: break      # No more input
    print tok