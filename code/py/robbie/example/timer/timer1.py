import sched, time

def print_time():
    print "From print_time", time.time()

def print_some_times():
    print time.time()

def run():
    s = sched.scheduler(time.time, time.sleep)

    s.enter(5, 1, print_time, ())
    s.enter(10, 1, print_time, ())
    s.run()

    print time.time()

if __name__ == '__main__':
    run()
    print_some_times()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\timer\timer1.py
'''