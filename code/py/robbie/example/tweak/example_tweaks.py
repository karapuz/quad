__author__ = 'ilya'

import robbie.tweak.value as twkval

def run():
    for varName in ('today', 'env_userName', 'env_origUserName'):
        print '%-20s' % varName, twkval.getenv( varName )

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python.exe robbie\example\tweak\example_tweaks.py

'''