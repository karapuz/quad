import os
import shlex

def run(path):

    with open(path) as fd:
        s = fd.read()
        lines = s.split('\n')
        for line in lines:
            if not line:
                continue
            if line in ('\n', '', ' '):
                continue
            lexer = shlex.shlex(line)
            tokenList = []
            for token in lexer:
                tokenList.append(str(token))
            print tokenList

import re

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def run2():
    findWholeWord('seek')('those who seek shall find')    # -> <match object>
    findWholeWord('word')('swordsmith')                   # -> None

if __name__ == '__main__':
    path = r'robbie\example\tracing\tokens.py'
    print '-->', path
    print run( path=path )

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\tracing\tokens.py
'''