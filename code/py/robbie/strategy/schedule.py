'''
define named schedules
'''

import robbie.util.datetime_util as dut

_dataSourceSchedule = {
    'nxc_lasttrade_930-935' : ( ( 'nxc', 'lasttrade', '09:35' ), [  (-1, 'nxc_lasttrade_930-935'    ) ], ),
    
    'nxc_low_935-357'       : ( ( 'nxc', 'low', '15:57' ), [  (-1, 'nxc_low_935-357'    ) ], ),    
    'nxc_high_935-357'      : ( ( 'nxc', 'high', '15:57' ), [  (-1, 'nxc_high_935-357'    ) ], ),

    'nxc_low_935-344'       : ( ( 'nxc', 'low', '15:44' ), [  (-1, 'nxc_low_935-344'    ) ], ),    
    'nxc_high_935-344'      : ( ( 'nxc', 'high', '15:44' ), [  (-1, 'nxc_high_935-344'    ) ], ),
                       
    'nxc_lastmids_352'      : ( ( 'nxc', 'lastmids', '15:52' ), [  (-1, 'nxc_lastmids_352'        ) ]  ),
    'nxc_lastmids_930-351'  : ( ( 'nxc', 'lastmids', '15:51' ), [  (-1, 'nxc_lastmids_930-351'    ) ], ),

    'nxc_lasttrade_351'     : ( ( 'nxc', 'lasttrade', '15:51' ), [  (-1, 'nxc_lasttrade_351'       ) ], ),
    'nxc_lasttrade_352'     : ( ( 'nxc', 'lasttrade', '15:52' ), [  (-1, 'nxc_lasttrade_352'       ) ], ),

    'nxc_avgmin_352'        : ( ( 'nxc', 'avgmin',    '15:52' ), [  (-1, 'nxc_avgmin_352'          ) ], ),
    'nxc_avgmin_353'        : ( ( 'nxc', 'avgmin',    '15:53' ), [  (-1, 'nxc_avgmin_353'          ) ], ),
    'nxc_avgmin_354'        : ( ( 'nxc', 'avgmin',    '15:54' ), [  (-1, 'nxc_avgmin_354'          ) ], ),
    'nxc_avgmin_355'        : ( ( 'nxc', 'avgmin',    '15:55' ), [  (-1, 'nxc_avgmin_355'          ) ], ),
    'nxc_avgmin_356'        : ( ( 'nxc', 'avgmin',    '15:56' ), [  (-1, 'nxc_avgmin_356'          ) ], ),
    'nxc_avgmin_358'        : ( ( 'nxc', 'avgmin',    '15:58' ), [  (-1, 'nxc_avgmin_358'          ) ], ),
    
    'nxc_lasttrade_356'     : ( ( 'nxc', 'lasttrade', '15:56' ), [  (-1, 'nxc_lasttrade_356'       ) ], ),
    
    'nxc_lasttrade_930-359' : ( ( 'nxc', 'lasttrade', '15:59' ), [  (-1, 'nxc_lasttrade_930-359'   ) ], ),
    'nxc_lasttrade_930-351' : ( ( 'nxc', 'lasttrade', '15:51' ), [  (-1, 'nxc_lasttrade_930-351'   ) ], ),
    'nxc_lasttrade_930-352' : ( ( 'nxc', 'lasttrade', '15:52' ), [  (-1, 'nxc_lasttrade_930-352'   ) ], ),
    'nxc_lasttrade_930-353' : ( ( 'nxc', 'lasttrade', '15:53' ), [  (-1, 'nxc_lasttrade_930-353'   ) ], ),
    'nxc_lasttrade_930-354' : ( ( 'nxc', 'lasttrade', '15:54' ), [  (-1, 'nxc_lasttrade_930-354'   ) ], ),
    'nxc_lasttrade_930-355' : ( ( 'nxc', 'lasttrade', '15:55' ), [  (-1, 'nxc_lasttrade_930-355'   ) ], ),
    'nxc_lasttrade_930-357' : ( ( 'nxc', 'lasttrade', '15:57' ), [  (-1, 'nxc_lasttrade_930-357'   ) ], ),
    'nxc_lasttrade_357-359' : ( ( 'nxc', 'lasttrade', '15:59' ), [  (-1, 'nxc_lasttrade_357-359'   ) ], ),
    

    'nxc_lasttrade_930-359_wYahoo': ( ( 'nxc', 'lasttrade', '15:59' ), [ (-1, ('yahoo',20130326) ), (20040102 , 'nxc_lasttrade_930-359' ) ], ),
    'nxc_lasttrade_930-357_wYahoo': ( ( 'nxc', 'lasttrade', '15:57' ), [ (-1, ('yahoo',20130326) ), (20040102 , 'nxc_lasttrade_930-357' ) ], ),
    'nxc_lasttrade_930-355_wYahoo': ( ( 'nxc', 'lasttrade', '15:55' ), [ (-1, ('yahoo',20130326) ), (20040102 , 'nxc_lasttrade_930-355' ) ], ),
    'nxc_lasttrade_930-351_wYahoo': ( ( 'nxc', 'lasttrade', '15:51' ), [ (-1, ('yahoo',20130326) ), (20040102 , 'nxc_lasttrade_930-351' ) ], ),
    
}

_sourceName, _sliceType, _sliceTime = 0,1,2

def getSched( name ):
    ( _schedNameSpecs, schedSpecs ) =_dataSourceSchedule[ name ]
    return schedSpecs

def getSliceSpecs( name ):
    ( sliceSpecs, _schedSpecs ) =_dataSourceSchedule[ name ]
    return sliceSpecs

def getSliceTime( name, asType='asStr' ):
    ''' get slice as '''
    
    timeStr = getSliceSpecs( name )[ _sliceTime ]
    
    if asType == 'asStr':
        return timeStr
    
    elif asType == 'asSec':
        return dut.toTimeSec( timeStr )
    
    else:
        raise ValueError( 'Unknown asType=%s' % asType )
    
def checkSimpleSlice( name ):
    ''' check if a slice is implemented in real time '''
    
    global _sourceName, _sliceType, _sliceTime
    return getSliceSpecs( name )[ _sliceType ] in ( 'lasttrade', )
