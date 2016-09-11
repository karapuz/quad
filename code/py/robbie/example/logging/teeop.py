import os
import subprocess

def components5(python, prog, args=['1>&2']):
    p = subprocess.Popen(python + prog + args, stdout=subprocess.PIPE)
    return iter(p.stdout.readline, b'')

def components6(python, prog, args=['2>&1']):
    p = subprocess.Popen(python + prog + args, stderr=subprocess.PIPE)
    return iter(p.stderr.readline, b'')

def components8(python, prog, args=['1>&2']):
    p = subprocess.Popen(python + prog + args, stderr=subprocess.PIPE)
    return iter(p.stderr.readline, b'')

def components7(python, prog, args=['2>&1']):
    p = subprocess.Popen(python + prog + args, stdout=subprocess.PIPE)
    return iter(p.stdout.readline, b'')

def components9(python, prog, args=['1>&2']):
    p = subprocess.Popen(python + prog + args, stderr=subprocess.PIPE)
    return iter(p.stdout.readline, b'')

def components1(python, prog, args=['1>&2']):
    p = subprocess.Popen(python + prog + args, stdout=subprocess.PIPE)
    return iter(p.stdout.readline, b'')

def components2(python, prog, args=['1>&2']):
    x = python + prog + args
    print 'x =', x
    p = subprocess.Popen(x, stderr=subprocess.PIPE, bufsize=0)
    return iter(p.stderr.readline, b'')

'''
myproc = subprocess.Popen('<cmd> 1>&2', stderr=subprocess.PIPE)
'''
if __name__ == '__main__':
    prog    = [r'robbie\example\logging\teeapp.py']
    python  = [r'c:\Python27\python2.7.exe']
    for l in components2(python, prog):
        print '>>>>>>>>>>>', l

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\logging\teeop.py

if 1:
    prog    = [r'robbie\example\logging\teeapp.py']
    logRoot = r'c:\temp'
    logName = 'teeop.txt'
    python  = [r'c:\Python27\python2.7.exe']
    args    = ['']
    args=['1>&2']


'''
