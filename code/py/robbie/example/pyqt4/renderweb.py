import sys
from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QApplication
#from PyQt4.QtWebKit import *
from PyQt4.QtWebKit import QWebView

app = QApplication(sys.argv)

web = QWebView()
web.load(QUrl("http://google.pl"))
web.show()

sys.exit(app.exec_())