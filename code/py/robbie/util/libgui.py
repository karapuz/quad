import threading

import wx
import datetime
import wx.lib.sheet as sheet #@UnresolvedImport

class Sheet(sheet.CSheet):
    def __init__(self, parent, N, M ):
        sheet.CSheet.__init__(self, parent)
        self.SetNumberRows( N )
        self.SetNumberCols( M )

class SimpleSheetNotebook( wx.Frame ):                  #@UndefinedVariable
    def __init__( self, parent, windowsId, title, N, M, needHeader=False, size=( 600, 500 ) ):

        wx.Frame.__init__(self, parent, windowsId, title, size=size ) #@UndefinedVariable        
        menubar = wx.MenuBar()                          #@UndefinedVariable
        fileMenu= wx.Menu()                             #@UndefinedVariable
        fileMenu.Append(101, 'Quit', '' )
        
        menubar.Append( fileMenu, '&File')
        self.SetMenuBar( menubar )
        wx.EVT_MENU(self, 101, self.OnQuit)             #@UndefinedVariable
        
        nb = wx.Notebook(self, -1, style=wx.NB_BOTTOM ) #@UndefinedVariable
        self.sheet = Sheet( parent=nb, N=N, M=M )        
        nb.AddPage(self.sheet, title )

        if not needHeader:
            self.sheet.SetRowLabelSize(2)
            self.sheet.SetColLabelSize(2)
        
        self.sheet.SetFocus()
        self.StatusBar()
        self.Centre()
        self.Show()
        
    def StatusBar(self):
        self.statusbar = self.CreateStatusBar()
        
    def OnQuit(self, event):
        self.Close()

class Notebook( wx.Frame ):                  #@UndefinedVariable
    def __init__( self, parent, windowsId, windowTitle, titles, N, M, needHeader=False ):

        wx.Frame.__init__(self, parent, windowsId, windowTitle, size=( 1000, 1000 ) ) #@UndefinedVariable        
        menubar = wx.MenuBar()                          #@UndefinedVariable
        fileMenu= wx.Menu()                             #@UndefinedVariable
        fileMenu.Append(101, 'Quit', '' )
        
        menubar.Append( fileMenu, '&File')
        self.SetMenuBar( menubar )
        wx.EVT_MENU(self, 101, self.OnQuit)             #@UndefinedVariable
        
        nb = wx.Notebook(self, -1, style=wx.NB_BOTTOM ) #@UndefinedVariable
        
        self.sheets = []
        for title in titles:
            sheet = Sheet( parent=nb, N=N, M=M )        
            nb.AddPage( sheet, title )
            self.sheets.append( sheet )

            if not needHeader:
                sheet.SetRowLabelSize( 2 )
                sheet.SetColLabelSize( 2 )
        
        self.sheets[0].SetFocus()
        
        self.StatusBar()
        self.Centre()
        self.Show()
        
    def StatusBar(self):
        self.statusbar = self.CreateStatusBar()
        
    def OnQuit(self, event):
        self.Close()

_mainLoopApp =  {}
def mainLoop( app, wait=False ):
    global _mainLoopApp
    
    if app in _mainLoopApp:
        return _mainLoopApp[ app ]
      
    if wait:
        return app.MainLoop()
        
    def run():
        app.MainLoop()
        
    t = threading.Thread( target=run )
    t.daemon = True
    t.start()
    _mainLoopApp[ app ] = t
    
    return t

_app = None
def getApp():
    global _app
    if _app == None:
        _app = wx.App() #@UndefinedVariable
    return _app

def showDict( data, title='', N=100, M=100, wait=True, computeGeometry=False, debug=False ):
    import meadow.lib.io as io
    app = getApp()
    
    if computeGeometry:
        N, M = io.obj2table( tag0=None, val0=data, N=0, M=0, sheet=None, debug=debug )
        print 'N =', N, 'M =', M
                
    nb      = SimpleSheetNotebook( parent=None, windowsId=-1, title=title, N=N, M=M )
    sheet   = nb.sheet
    io.obj2table( tag0=None, val0=data, N=0, M=0, sheet=sheet, debug=False )
    mainLoop( app, wait=wait )


def showTable( mat, wait=True ):
    import numpy
    
    app = getApp()
    
    if isinstance( mat, numpy.ndarray ):
        mat = mat.tolist()
            
    ncols   = None    
    count   = 1
    nmat    = []
    for cells in mat:
        if ncols == None:
            ncols = len( cells )
        else:
            ncols = max( ncols, len( cells ) )
        nmat.append( [str(count)] + cells )
        count += 1

    ncols += 1
    nrows = len( nmat )
    nb = Notebook( 
            parent      =None, 
            windowsId   =-1, 
            windowTitle ='table', N=nrows, M=ncols, 
            titles      = [ 'Page 0' ] )
    
    sheet = nb.sheets[ 0 ]
    for rix, cells in enumerate( mat ):
        sheet.SetCellBackgroundColour( rix, 0, 'LIGHT GREY')                    
        sheet.SetCellValue( rix, 0, str( rix ) )
        for cix, cell in enumerate( cells ):
            sheet.SetCellValue( rix, cix+1, str( cell ) )

    mainLoop( app, wait=wait )

def showTime( sheet, n, m ):
    now = datetime.datetime.now()
    now = datetime.datetime.strftime( now, '%Y-%m-%d %H:%M:%S' )
    sheet.SetCellValue( n, m, now )
