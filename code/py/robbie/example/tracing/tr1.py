import sys

def traceit(frame, event, arg):
    if event == "line":
        lineno = frame.f_lineno
        # print dir(frame)
        print "line", lineno
        #print 'f_code', dir(frame.f_code)
        c = frame.f_code
        print 'co_filename', c.co_filename, c.co_name

    return traceit

def F():
    pass

def main():
    print "In main"
    for i in range(5):
        print i, i*3
    print "Done."
    F()
    

sys.settrace(traceit)
main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\tracing\tr1.py
'''