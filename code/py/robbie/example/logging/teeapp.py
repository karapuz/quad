import time

def run():
    for ix,e in enumerate( xrange(1000000)):
        print ix,e, 'x' * 1000
        time.sleep(1)

if __name__ == '__main__':
    run()

'''
python -m trace --count -C . somefile.py ...

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe -m trace --count . robbie\example\logging\teeapp.py
'''