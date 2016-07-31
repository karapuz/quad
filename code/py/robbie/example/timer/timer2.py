import time
from threading import Timer

def print_time():
    print "From print_time", time.time()

class Order(object):
    def __init__(self, x):
        self._x = x
    def run(self,y):
        print 'x->', self._x, 'y->', y, type(y)

def print_some_times():
    print time.time()
    Timer(5, print_time, ()).start()
    Timer(10, print_time, ()).start()
    time.sleep(11)  # sleep while time-delay events execute
    print time.time()

def print_some_times2():
    print '0000', time.time()
    Timer(5, Order(5).run, (500,)).start()
    Timer(10, Order(10).run, (1000,)).start()
    time.sleep(11)  # sleep while time-delay events execute
    print '1111', time.time()

if __name__ == '__main__':
    print_some_times2()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\timer\timer2.py
'''