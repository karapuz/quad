'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : app.fakebbg module
'''

import os
import sys
import threading
import subprocess
from   PyQt4 import QtGui
from   PyQt4.QtGui import QApplication
from   PyQt4.QtGui import QDesktopWidget, QTextEdit

import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx

app = QApplication(sys.argv)
dw  = QDesktopWidget()
dwX = dw.width()*0.7
dwY = dw.height()*0.7

def _exit(*args):
    global _continue
    print '----------------->', _exit
    _continue = False
    sys.exit()

def _panic(turf):
    args    = ['--turf=%s' % turf, "--data=\"('SRC','SNK')\"", '--cmd=KILL']
    argusConf   = turfutil.get(turf=turf, component='argus')
    python      = argusConf['python']
    prog        = argusConf['cmd']['prog']
    subprocess.call(python + prog + args, stdin=None, stdout=None, stderr=None, shell=False)
    sys.exit()

def component2(textWidget, logRoot, logName, python, prog, args):
    stdOut = os.path.join( logRoot, logName)
    with open( stdOut, 'w' ) as fdStdout:
        p = subprocess.Popen(python + prog + args,
                             stderr=subprocess.PIPE)
        for l in iter(p.stdout.readline, b''):
            textWidget.append(l)
            fdStdout.write(l)
            fdStdout.flush()

class TopWindow(QtGui.QMainWindow):

    def __init__(self, table=None):
        super(TopWindow, self).__init__()
        self._table = table
        self._init()

    def _init(self):
        import functools
        turf        = twkval.getenv('run_turf')
        exitAction  = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(_exit)

        panigAction     = QtGui.QAction(QtGui.QIcon('exit.png'), '&Panic', self)
        panigAction.setShortcut('Ctrl+X')
        panigAction.setStatusTip('Panic')
        panigAction.triggered.connect(functools.partial(_panic, turf))

        self.statusBar()

        menuBar     = self.menuBar()
        fileMenu    = menuBar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(panigAction)

        self.setMinimumSize(dwX,dwY)
        self.setWindowTitle('Menubar')

        top     = QtGui.QTabWidget()
        prog    = [r'robbie\example\logging\teeapp.py']
        python  = [r'c:\Python27\python2.7.exe']
        args    = ['1>&2']
        self._texts     = []
        self._threads   = []
        for ix in xrange(10):
            t = QTextEdit()
            top.addTab(t,"Tab %s" % ix )
            kwargs = dict(textWidget=t, logRoot=r'c:\temp', logName='log_%s.txt' % ix, python=python, prog=prog, args=args)
            thread = threading.Thread(target=component2, kwargs=kwargs)
            thread.start()
            self._threads.append( thread )

        #grid = QtGui.QGridLayout()
        #grid.setSpacing(5)

        #top.setLayout(grid)
        self.setCentralWidget(top)

    def getTextWidget(self):
        return self._texts

_NoData = ('NoData',)

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    turf    = args.turf
    tweaks  = {
        'run_turf'  : turf,
    }
    with twkcx.Tweaks( **tweaks ):
        top = TopWindow()
        top.show()
        sys.exit(app.exec_())

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\app\argus2.py --turf=ivp_redi_fix
'''
