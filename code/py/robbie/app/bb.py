'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : app.fakebbg module
'''

import sys
import time
from   threading import Timer
from   PyQt4 import QtGui
from   PyQt4.QtCore import QAbstractTableModel, QVariant, Qt, QSize
from   PyQt4.QtGui import QWidget, QTableView, QVBoxLayout, QApplication, QBrush, QColor
from   PyQt4.QtGui import QDesktopWidget, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QTextEdit

import zmq
import json
import numpy
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger

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

_signalCategory = ['PEND', 'RLZED', 'ECHO-PEND', 'ECHO-RLZD']
_targets        = ('SRC', 'SNK')
_sliceTypes     = ['pending', 'realized', ]


def doubleClicked(index):
    print 'doubleClicked --->', index.row(), index.column()

def clicked(index):
    print 'clicked --->', index.row(), index.column()

class ExposureTable(QWidget):
    def __init__(self, signalNames, symbols, data, *args):
        QWidget.__init__(self, *args)

        self._tableModel = MyTableModel(signalNames, symbols, data, self)
        self._tableView  = QTableView()
        self._tableView.setModel(self._tableModel)
        self._tableView.doubleClicked.connect(doubleClicked)
        self._tableView.clicked.connect(clicked)
        # self._tableView.setStyleSheet("QHeaderView::section { background-color:red }")

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._tableView)
        self.setLayout(self._layout)

    def tableModel(self):
        return self._tableModel

    def tableLayout(self):
        return self._layout

class MyTableModel(QAbstractTableModel):

    def __init__(self, signalNames, symbols, data, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._data = data
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

    def toColor(self, rowIx, colIx):
        '''
        can be either data, symbols, or signal (sub elements)
        '''
        if colIx > 0:
            #return QBrush(Qt.black), QBrush(Qt.green)
            return QBrush(Qt.black), QBrush(QColor(128, 195, 66))

        if colIx == 0:
            return QBrush(Qt.white), QBrush(Qt.darkGreen)

    def setData(self, data):
        self._data = data

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data[0])

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
            #return QBrush(Qt.yellow)
            return self.toColor(rowIx=rowIx, colIx=colIx)[1]

        elif role == Qt.SizeHintRole:
            return QSize( 30, 0 )

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return ''

            nx = int((section-1) / 4)
            cx = (section-1) % 4

            if nx * 4 == (section-1):
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
        msg = 'cycle( table=%s, delay=%s) _cycle_ix=%s' % ( table, delay, _cycle_ix )
        text.append(msg)

        data    = getData(orderStates=orderStates, agents=agents, symbols=symbols, debug=True)

        table.tableModel().setData(data)
        model   = table.tableModel()
        beg     = 0, 0
        end     = model.rowCount(0), model.columnCount(0)
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

class TopWindow(QtGui.QMainWindow):

    def __init__(self, table):
        super(TopWindow, self).__init__()
        self._table = table
        self._init()

    def _init(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(_exit)

        self.statusBar()

        menuBar     = self.menuBar()
        fileMenu    = menuBar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.setMinimumSize(dwX,dwY)
        self.setWindowTitle('Menubar')
        top     = QWidget()
        self._text = QTextEdit()
        self._text.ensureCursorVisible()

        grid = QtGui.QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(self._table, 0, 0)
        grid.addWidget(self._text, 1, 0, 10, 1 )

        top.setLayout(grid)
        self.setCentralWidget(top)

    def getTextWidget(self):
        return self._text

def createGUI(data, signalNames, symbols):
    table   = ExposureTable(signalNames=signalNames, symbols=symbols, data=data)
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

def getData(orderStates, agents, symbols, debug=True):
    global _targets, _sliceTypes
    mat = []
    for agent in agents:
        for target in _targets:
            domain = basestrat.getOrderStateDomain(target=target, agent=agent)
            ordState = orderStates[domain]
            for sliceType in _sliceTypes:
                symbolSlice = ordState.getSymbolSlice(which=sliceType)
                if debug:
                    logger.debug('getData: domain=%s data=%s', domain, symbolSlice)
                mat.append( symbolSlice.tolist() )
    if debug:
        logger.debug('getData: -------------')
    return numpy.array( mat ).T.tolist()

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
        agents      = turfutil.get(turf=turf, component='agents')
        symbols     = symboldb.currentSymbols()
        mode        = EXECUTION_MODE.NEW_FILL_CX
        orderStates = prepareOrderStates(agents=agents, mode=mode)
        data        = getData(orderStates=orderStates, agents=agents, symbols=symbols)
        top, table, text = createGUI(signalNames=agents, data=data, symbols=symbols)
        cycle( turf=turf, tweaks=tweaks, orderStates=orderStates, agents=agents, table=table, text=text, delay=1)
        top.show()
        table.show()
        sys.exit(app.exec_())

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\app\bb.py --turf=ivp_redi_fix
'''
