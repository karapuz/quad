html = '''<html>
<head>
<title>A Sample Page</title>
</head>
<body>
<h1>Hello, World!</h1>
<hr />
I have nothing to say.
</body>
</html>'''

import sys
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebView

def decor(path):
    with open(path) as fd:
        txt = fd.read()
        lines = txt.split('\n')
        for line in lines:
            tokens = line.split(' ')

def run():
    app = QApplication(sys.argv)

    web = QWebView()
    web.setHtml(html)
    web.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()