import sys
import time
from   threading import Timer
from   PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from   PyQt5.Qt import QApplication, QWidget, QVBoxLayout, QTableView, QBrush, QDesktopWidget, QSize

'''
white, black,
red, darkRed,
green, darkGreen,
blue, darkBlue,
cyan, darkCyan,
magenta, darkMagenta,
yellow, darkYellow,
gray, darkGray, lightGray
'''

def doubleClicked(index):
    print 'doubleClicked --->', index.row(), index.column()

def clicked(index):
    print 'clicked --->', index.row(), index.column()

class MyWindow(QWidget):
    def __init__(self, data, *args):
        QWidget.__init__(self, *args)

        self._tableModel = MyTableModel(data, self)
        self._tableView  = QTableView()
        self._tableView.setModel(self._tableModel)
        self._tableView.doubleClicked.connect(doubleClicked)
        self._tableView.clicked.connect(clicked)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._tableView)
        self.setLayout(self._layout)

    def tableModel(self):
        return self._tableModel

    def tableLayout(self):
        return self._layout

class MyTableModel(QAbstractTableModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._data = datain

    def setData(self, data):
        self._data = data

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return QVariant(
                    self._data[ index.row() ][ index.column() ]
            )

        elif role == Qt.BackgroundRole:
            return QBrush(Qt.yellow)

        elif role == Qt.SizeHintRole:
            return QSize( 30, 0 )

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            # return 'Column' + str(section)
            return ''

_cycle_ix = 0
def cycle( table, delay=5):
    global _cycle_ix
    print 'cycle( table=%s, delay=%s) _cycle_ix=%s' % ( table, delay, _cycle_ix )

    data = []
    for i in xrange(100):
        r = [ str(j*_cycle_ix) for j in xrange(100) ]
        data.append(r)

    table.tableModel().setData(data)
    model = table.tableModel()
    model.dataChanged.emit(
        model.createIndex(0, 0),
        model.createIndex(
            model.rowCount(0), model.columnCount(0)
        )
    )

    _cycle_ix += 1
    # if _cycle_ix > 3:
    #     return
    time.sleep(delay)
    timer = Timer(delay, cycle, (table, delay))
    timer.start()

data = []
for i in xrange(100):
    r = [ str(j) for j in xrange(100) ]
    data.append(r)

def createWindow():

    app = QApplication(sys.argv)
    dw  = QDesktopWidget()
    w   = MyWindow(data=data)

    x   = dw.width()*0.7
    y   = dw.height()*0.7;
    w.setFixedSize(x,y)

    return app, w

def main(app, w):
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app, w = createWindow()
    cycle( table=w, delay=1)
    main(app, w)