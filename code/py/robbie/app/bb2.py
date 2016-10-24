'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : app.fakebbg module
'''

import os
import sys
import time
from   threading import Timer
#from   PyQt4 import QtGui
#from   PyQt4.QtCore import QAbstractTableModel, QVariant, Qt, QSize
#from   PyQt4.QtGui import QWidget, QTableView, QVBoxLayout, QApplication, QBrush, QColor
#from   PyQt4.QtGui import QDesktopWidget, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QTextEdit

from PyQt5.Qt import QApplication, QWidget, QVBoxLayout, QTableView, QIcon, QColor, QBrush, QColor, QSize
from PyQt5.Qt import QDesktopWidget, QTextEdit, QMainWindow, QAction, QTabWidget, QLineEdit, QPushButton, QGridLayout
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant


import zmq
import json
import numpy
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger, LoggingModes

import robbie.echo.basestrat as basestrat
import robbie.echo.orderstate as orderstate
from   robbie.echo.stratutil import STRATSTATE, EXECUTION_MODE

app = QApplication(sys.argv)
dw  = QDesktopWidget()
dwX = dw.width()*0.7
dwY = dw.height()*0.7

'''
white, black,
red, darkRed,
green, darkGreen,
blue, darkBlue,
cyan, darkCyan,
magenta, darkMagenta,
yellow, darkYellow,
gray, darkGray, lightGray


Dark green	        Medium green	Light green	        Dark blue	            Blue	            Violet	            Purple
HEX #006325	        HEX #328930	    HEX #80c342	        HEX #14148c	            HEX #14aaff	        HEX #6400aa	        HEX #ae32a0
RGB 0, 99, 37	    RGB 50, 137, 48	RGB 128, 195, 66	RGB 20, 20, 140	        RGB 20, 170, 255	RGB 100, 0, 170	    RGB 174, 50, 160

Double dark gray	Dark gray	    Medium gray	        Regular gray	        Light gray	        Pale gray	        White
HEX #1e1b18	        HEX #35322f	    HEX #5d5b59	        HEX #868482	            HEX #aeadac	        HEX #d7d6d5	        HEX #ffffff
RGB 30, 27, 24	    RGB 53, 50, 47	RGB 93, 91, 89	    RGB 134, 132, 130	    RGB 174, 173, 172	RGB 215, 214, 213	RGB 255, 255, 255

'''

_colors = {
    'LightGreen'    : QColor(128, 195, 66),
    'MediumGreen'   : QColor(50, 137, 48),
    'DarkGreen'     : QColor(0, 99, 37),
}

_signalCategory = ['LONG', 'SHORT', 'RLZED', 'ECHO-LONG', 'ECHO-SHORT', 'ECHO-RLZD']
_echoSignals    = ['ECHO-LONG', 'ECHO-SHORT', 'ECHO-RLZD']
_targets        = ('SRC', 'SNK')
_sliceTypes     = ['pending-long', 'pending-short', 'realized', ]

def clickColToSignalName(colIx):
    nx = int((colIx-1) / len(_signalCategory))
    return nx

def clickColToSectionName(colIx):
    cx = (colIx-1) % len(_signalCategory)
    return cx

class ExposureTable(QWidget):
    def __init__(self, signalNames, symbols, data, *args):
        QWidget.__init__(self, *args)

        self._tableModel = MyTableModel(signalNames, symbols, data, self)
        self._tableView  = QTableView()
        self._tableView.setModel(self._tableModel)
        #self._tableView.doubleClicked.connect(doubleClicked)
        #self._tableView.clicked.connect(clicked)
        self._tableView.clicked.connect(self.click)

        self._symbols    = symbols
        self._signalNames=signalNames

        # self._tableView.setStyleSheet("QHeaderView::section::horizontal { background-color:red }")
        # self._tableView.setStyleSheet("QHeaderView::section:horizontal {margin: 0px;  border: 0; padding 0px}")
        # self._tableView.setStyleSheet("horizontal {margin: 0px;  border: 0; padding 0px}")
        # self._tableView.setStyleSheet("QTableView::item {padding: 0px; margin: 0px; border: 0; background-color: orange; }")

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._tableView)
        self.setLayout(self._layout)

    def registerEventHandler(self, eventHandler):
        self._eventHandler = eventHandler

    def click(self, index):
        rowIx       = index.row()
        colIx       = index.column()
        logger.debug( 'clicked ---> %d %d', rowIx, colIx)

        nx          = clickColToSignalName(colIx)
        signalName  = self._signalNames[ nx ]
        cx          = clickColToSectionName(colIx)
        secName     = _signalCategory[cx]
        symbol      = self._symbols[ rowIx ]

        self._eventHandler( source='table', data=(signalName, secName, symbol) )
        logger.debug( 'name=%s secName=%s symbol=%s', signalName, secName, symbol )

    def tableModel(self):
        return self._tableModel

    def getData(self):
        return self._tableModel._data

    def setChanged(self, changed):
        # self._changed = changed
        self._tableModel.changed( changed )

    def tableLayout(self):
        return self._layout

class MyTableModel(QAbstractTableModel):

    def __init__(self, signalNames, symbols, data, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._data = data
        self._changed = {}
        self.initLabels( signalCategory=_signalCategory, signalNames=signalNames, symbols=symbols)

    def initLabels( self, signalCategory, signalNames, symbols):
        self._signalNames   = signalNames
        self._symbols       = symbols
        self._signalCategory= signalCategory

    def toLabel(self, rowIx, colIx):
        '''
        can be either data, symbols, or signal (sub elements)
        '''
        if colIx > 0:
            x = colIx - 1
            y = rowIx
            return self._data[ y ][ x ]
        elif colIx == 0:
            return self._symbols[ rowIx ]

    def changed( self, changed ):
        self._changed = changed
        # logger.debug('MyTableModel->changed = %s' % str(changed) )

    def toColor(self, rowIx, colIx):
        '''
        can be either data, symbols, or signal (sub elements)
        '''
        if self._changed:
            indx = rowIx, colIx - 1
            # print '---------> indx ', indx

            if indx in self._changed:
                # print '--------->>>>>>>>>>>>>> indx ', indx
                del self._changed[ indx ]
                return QBrush(Qt.white), QBrush(Qt.magenta)

        if colIx > 0:
            #return QBrush(Qt.black), QBrush(Qt.green)
            signalCount = len(_signalCategory)
            even = ( int( (colIx - 1) / signalCount) % 2) == 0

            if even:
                return QBrush(Qt.black), QBrush(_colors['LightGreen'])
            else:
                return QBrush(Qt.black), QBrush(_colors['MediumGreen'])

        if colIx == 0:
            return QBrush(Qt.white), QBrush(_colors['DarkGreen'])


    def setData(self, data):
        self._data = data

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data[0])+1

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        rowIx = index.row()
        colIx = index.column()

        if role == Qt.DisplayRole:
            e = self.toLabel(rowIx=rowIx, colIx=colIx)
            return QVariant( e )

        elif role == Qt.ForegroundRole:
            return self.toColor(rowIx=rowIx, colIx=colIx)[0]

        elif role == Qt.BackgroundRole:
            # return QBrush(Qt.yellow)
            return self.toColor(rowIx=rowIx, colIx=colIx)[1]

        elif role == Qt.SizeHintRole:
            return QSize( 30, 0 )

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return ''

            nx = clickColToSignalName(section)
            cx = clickColToSectionName(section)

            signalCount = len(_signalCategory)

            if nx * signalCount == (section-1):
                return '%s\n%s' % ( self._signalNames[ nx ], self._signalCategory[ cx ] )
            else:
                return '%s\n%s' % ( '', self._signalCategory[ cx ] )

        elif role == Qt.BackgroundRole:
            return QBrush(Qt.darkGreen)

_cycle_ix = 0
_continue = True
def cycle( turf, tweaks, orderStates, agents, table, text, delay=5):
    global _cycle_ix, _continue
    with twkcx.Tweaks( **tweaks ):
        if not _continue:
            return
        symbols     = symboldb.currentSymbols()
        # msg = 'cycle( table=%s, delay=%s) _cycle_ix=%s' % ( table, delay, _cycle_ix )
        # text.append(msg)

        data    = getData(orderStates=orderStates, agents=agents, symbols=symbols, debug=False)

        model   = table.tableModel()
        d0      = table.getData()

        changed = {}
        for ix in xrange( len( d0 )):
            for jx in xrange( len(d0[0])):
                if d0[ ix ][ jx ] != data[ ix ][ jx ]:
                    changed[ ix, jx ] = 1

        model.setData(data)
        table.setChanged(changed)
        beg     = 0, 0
        end     = len(data) + 1, len(data[0]) + 1
        model.dataChanged.emit( model.createIndex( *beg ), model.createIndex( *end ))

        _cycle_ix += 1
        time.sleep(delay)
        timer = Timer(delay, cycle, (turf, tweaks, orderStates, agents, table, text, delay))
        timer.start()

def _exit(*args):
    global _continue
    print '----------------->', _exit
    _continue = False
    sys.exit()

def _panic(turf):
    global _continue
    import subprocess
    args    = ['--turf=%s' % turf, "--data=\"('SRC','SNK')\"", '--cmd=KILL']
    argusConf   = turfutil.get(turf=turf, component='argus')
    python      = argusConf['python']
    prog        = argusConf['cmd']['prog']
    subprocess.call(python + prog + args, stdin=None, stdout=None, stderr=None, shell=False)
    # print python, prog, args, turf
    _continue = False
    sys.exit()

class TopWindow(QMainWindow):

    def __init__(self, table):
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
        top             = QWidget()
        self._text      = QTextEdit()
        self._cmdLine   = QLineEdit()
        self._execButton= QPushButton('go!')
        self._text.ensureCursorVisible()
        self._execButton.clicked.connect( buttonClicked )
        sinkRegister(sinkName='CmdLink', sink=self._cmdLine)

        grid = QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(self._table, 0, 0, 1, 10)
        grid.addWidget(self._cmdLine, 1, 0, 1, 9)
        grid.addWidget(self._execButton, 1, 9)
        grid.addWidget(self._text, 2, 0, 10, 10 )

        top.setLayout(grid)
        self.setCentralWidget(top)

    def getTextWidget(self):
        return self._text

_NoData = ('NoData',)

_sinks = {}
def sinkRegister(sinkName, sink):
    global _sinks
    _sinks[sinkName]=sink

_storedSignals = {}
def storedSignals(signalName, signal=_NoData):
    global _storedSignals
    if signal == _NoData:
        return _storedSignals[signalName]
    else:
        _storedSignals[signalName] = signal
        return signal

def buttonClicked(*args):
    global _sinks
    signal  = storedSignals(signalName='CmdLink')

    signal = [str(e) for e in signal]
    (signalName, secName, symbol) = signal

    _sinks[ 'CmdLink' ].setText( '' )

    # expSrc, expType = secName.split('-')
    if secName not in _echoSignals:
        errorMsg = 'Cannot execute %s' % str(signal)
        logger.error(errorMsg)
        _sinks['TextWindow'].append('ERROR:' + errorMsg)
        return

    bbIn    = storedSignals(signalName='BBIn')
    cmd     = {'signalName': signalName, 'secName': secName, 'symbol': symbol }
    msg     = json.dumps(cmd)
    bbIn[ signalName ].send(msg)
    logger.debug( 'buttonClicked: %s', str(cmd))
    _sinks['TextWindow'].append('SENDING:' + str(cmd))

def eventHandler(source, data):
    # source='table', data=(signalName, secName, symbol)
    global _sinks, _storedSignals
    logger.debug('eventHandler: source=%s data=%s', source, data)

    if source == 'table':
        storedSignals(signalName='CmdLink', signal=data)
        text = _storedSignals[ 'CmdLink' ]
        _sinks[ 'CmdLink' ].setText( str(text) )

def createGUI(data, signalNames, symbols):
    table   = ExposureTable(signalNames=signalNames, symbols=symbols, data=data)
    table.registerEventHandler(eventHandler)
    top     = TopWindow(table=table)
    text    = top.getTextWidget()
    return top, table, text

def prepareOrderStates(agents, mode):
    global _targets

    symbols    = symboldb.currentSymbols()
    maxNum     = symboldb._maxNum
    orderStates = {}
    for agent in agents:
        for target in _targets:
            domain = basestrat.getOrderStateDomain(target=target, agent=agent)
            with twkcx.Tweaks(run_domain=domain):
                if mode == EXECUTION_MODE.NEW_FILL_CX:
                    seePending = True
                elif mode == EXECUTION_MODE.FILL_ONLY:
                    seePending = False
                else:
                    raise ValueError('Unknown signalMode=%s' % mode)

                orderState = orderstate.OrderState(
                        readOnly    = True,
                        maxNum      = maxNum,
                        symbols     = symbols,
                        seePending  = seePending,
                        debug       = True )
                orderStates[ domain ] = orderState
    return orderStates

def getData(orderStates, agents, symbols, debug=False):
    global _targets, _sliceTypes
    mat = []
    for agent in agents:
        for target in _targets:
            domain      = basestrat.getOrderStateDomain(target=target, agent=agent)
            ordState    = orderStates[domain]
            for sliceType in _sliceTypes:
                symbolSlice = ordState.getSymbolSlice(which=sliceType)
                if debug:
                    logger.debug('getData: domain=%s data=%s', domain, symbolSlice)
                mat.append( symbolSlice.tolist() )
    if debug:
        logger.debug('getData: -------------')
    return numpy.array( mat ).T.tolist()

def createBBComm():
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')
    bbIn        = {}

    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('BB: not an agent: %s', agent)
            continue
        logger.debug( 'BB: agent=%s', agent)
        agent_BBIn      = agt_comm['agent_BBIn']
        agent_BBInCon   = context.socket(zmq.PUB)
        agent_BBInCon.bind('tcp://*:%s' % agent_BBIn)
        bbIn[agent] = agent_BBInCon
    return bbIn

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    parser.add_argument("-L", "--logpath",  help="log path", action="store")
    args    = parser.parse_args()
    if args.logpath:
        logger.debug('switching to file logger path=%s', args.logpath)
        logger.setMode(mode=LoggingModes.FILE, data=args.logpath)

    turf    = args.turf
    tweaks  = {
        'run_turf'  : turf,
    }
    with twkcx.Tweaks( **tweaks ):
        agents      = turfutil.get(turf=turf, component='agents')
        symbols     = symboldb.currentSymbols()
        mode        = EXECUTION_MODE.NEW_FILL_CX
        orderStates = prepareOrderStates(agents=agents, mode=mode)
        data        = getData(orderStates=orderStates, agents=agents, symbols=symbols)
        bbIn        = createBBComm()
        storedSignals(signalName='BBIn', signal=bbIn)
        top, table, text = createGUI(signalNames=agents, data=data, symbols=symbols)
        sinkRegister('TextWindow', text)
        cycle( turf=turf, tweaks=tweaks, orderStates=orderStates, agents=agents, table=table, text=text, delay=1)
        top.show()
        table.show()
        sys.exit(app.exec_())

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\app\bb2.py --turf=ivp_redi_fix
'''
