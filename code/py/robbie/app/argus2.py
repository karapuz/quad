'''
AUTHOR      : ilya presman, 2016
TYPE:       : app
DESCRIPTION : app.argus2 module
'''

import os
import sys
import threading
import subprocess

from PyQt5.Qt import QApplication, QWidget, QVBoxLayout, QTableView, QIcon
from PyQt5.Qt import QDesktopWidget, QTextEdit, QMainWindow, QAction, QTabWidget
# from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant

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

# def component2(textWidget, logRoot, logName, python, prog, args, logpath):
#     stdOut = os.path.join( logRoot, logName)
#     with open( stdOut, 'w' ) as fdStdout:
#         p = subprocess.Popen(python + prog + args,
#                              stderr=subprocess.PIPE)
#         for l in iter(p.stdout.readline, b''):
#             textWidget.append(l)
#             fdStdout.write(l)
#             fdStdout.flush()

import time
def component2(textWidget, logRoot, logName, python, prog, args, logpath):
    p = subprocess.Popen(python + prog + args )
    while not os.path.exists(logpath):
        time.sleep(1)

    with open( logpath, 'r' ) as fd:
        for l in iter(fd.readline, b''):
            textWidget.append(l)

class TopWindow(QMainWindow):

    def __init__(self, table=None):
        super(TopWindow, self).__init__()
        self._table = table
        self._init()

    def _init(self):
        import functools
        turf        = twkval.getenv('run_turf')
        exitAction  = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(_exit)

        panigAction     = QAction(QIcon('exit.png'), '&Panic', self)
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

        top     = QTabWidget()
        self.setCentralWidget(top)

        # prog    = [r'robbie\example\logging\teeapp.py']
        prog    = [r'robbie\example\logging\demoapp.py']
        python  = [r'c:\Python27\python2.7.exe']
        self._texts     = []
        self._threads   = []
        for ix in xrange(3):
            t       = QTextEdit()
            logpath = r'c:\temp\log%d.txt' % ix
            args   = [ '--logpath', logpath ]
            top.addTab(t,"Tab %s" % ix )
            kwargs = dict(textWidget=t, logRoot=r'c:\temp', logName='log_%s.txt' % ix, python=python, prog=prog, args=args, logpath=logpath)
            thread = threading.Thread(target=component2, kwargs=kwargs)
            thread.start()
            self._threads.append( thread )

        #grid = QtGui.QGridLayout()
        #grid.setSpacing(5)
        #top.setLayout(grid)

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
python robbie\app\argus2.py --turf=ivp_redi_fix
'''
