__author__ = 'ilya'

import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx

def run():
    with twkcx.Tweaks(today='now!'):
        for varName in ('today', 'env_userName', 'env_origUserName'):
            print '%-20s' % varName, twkval.getenv( varName )

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\tweak\example_context.py

'''