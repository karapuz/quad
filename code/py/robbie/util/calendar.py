'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.calendar module
'''

import numpy
import datetime

#import meadow.lib.pytables as pytables
#import meadow.lib.environment as environment
#import meadow.lib.datetime_util as dut

# _cache = {}
#
# def _loadbizsched( name ):
#     global _cache
#     if name not in _cache:
#         dn = environment.getDataRoot( 'calendar' )
#         _cache[ name ] = numpy.array( pytables.readArray( ( dn, 'us' ), ( 'bank', name ) ) )
#     return _cache[ name ]

def iseow( dt ):
    ''' detect end of week '''
    if isinstance( dt, ( int, float ) ):
        dt = dut.num2dt( dt )
    return ( dt.weekday() == 4 )

def iseom( dt ):
    ''' detect end of month '''
    if isinstance( dt, ( int, float ) ):
        dt = dut.num2dt( dt )
    m0 = dt.month
    dt = bizday( dt, specs='+1b' )
    m1 = dut.num2dt( dt ).month
    return m1 != m0

def getdate( name, typ='int' ):
    '''get today's date as an int'''

    dt = datetime.datetime.now()

    if name == 'today':
        if typ in (str, 'str'):
            return dt.strftime( '%Y%m%d' )
        elif typ == 'int':
            return int( dt.strftime( '%Y%m%d' ) )
        elif typ == 'dt':
            return dt

    raise ValueError( 'Unknown name="%s" type="%s"' % (name, typ ))

def today( typ='int' ):
    '''return today'''
    return getdate( name='today', typ=typ )

def getsession(name, _typ='str'):
    return getdate( name='today', typ='str' )

def now():
    '''return now'''
    return getdate( name='today', typ='dt' )

# def isbizday( dt ):
#     '''check if dt is a biz day'''
#     if isinstance( dt, datetime.datetime ):
#         return isbizdate_datetime( dt )
#
#     elif isinstance( dt, str ):
#         return isbizdate_num( int( dt ) )
#
#     elif isinstance( dt, int ):
#         return isbizdate_num( dt )
#
#     raise ValueError( 'Unknown %s with type %s' % ( str( dt ), type( dt ) ) )
#
# def isbizdate_datetime( dt ):
#     '''check if dt is a biz day'''
#     return isbizdate_num(  dut.dt2num( dt ) )
#
#  def isbizdate_num( dt ):
#     '''check if dt is a biz day'''
#     return dt in _loadbizsched( 'bizdays' )
#
# def bizdaterange( sd, ed ):
#     '''return biz range day as core'''
#     global _cache
#
#     if not isinstance( sd, int ) or not isinstance( ed, int ):
#         raise ValueError( 'bad types for sd, ed [%s %s]' % ( sd, ed ) )
#
#     b = _loadbizsched( 'bizdays' )
#     b = b[ b >= sd ]
#     return b[ b <= ed ]
# def nextbizday_datetime( dt, specs=( '+', 1, 'b' ) ):
#     '''return next biz day as core'''
#
#     _sign, count, typ = specs
#     if typ == 'b':
#         delta = datetime.timedelta( 1 )
#
#         while 1:
#             dt  += delta
#             dti = dut.dt2num( dt )
#             if isbizdate_num( dti ):
#                 count -= 1
#                 if not count:
#                     return dti
#     elif typ in ( 'd', 'c' ):
#         return dut.dt2num( dt + datetime.timedelta( count ) )
#
#     raise ValueError( 'Unknown specifications %s' % str( specs ) )
#
# def prevbizday_datetime( dt, specs=( '-', 1, 'b' ) ):
#     '''return next biz day as core'''
#
#     _sign, count, typ = specs
#
#     if typ == 'b':
#         delta = datetime.timedelta( 1 )
#
#         while 1:
#             dt  -= delta
#             dti = dut.dt2num ( dt )
#             if isbizdate_num( dti ):
#                 count -= 1
#                 if not count:
#                     return dti
#
#     elif typ in ( 'd', 'c' ):
#         return dut.dt2num(  dt - datetime.timedelta( count ) )
#
#     raise ValueError( 'Unknown specifications %s' % str( specs ) )

# def nextbizday( dt, specs=( '+', 1, 'b' )  ):
#     '''return next biz day as core'''
#     specs = _parse( specs )
#
#     if isinstance( dt, ( datetime.datetime, datetime.date ) ):
#         return nextbizday_datetime( dt, specs=specs )
#
#     elif isinstance( dt, ( int, float ) ):
#         return nextbizday_datetime( dut.num2dt( int( dt )  ), specs=specs )
#
#     else:
#         raise ValueError( 'Unknown dt=%s type=%s specs=%s' % ( dt, type(dt), str( specs ) ) )
#
# def prevbizday( dt, specs=( '-', 1, 'b' ) ):
#     '''return next biz day as core'''
#
#     specs = _parse( specs )
#     if isinstance( dt, ( datetime.datetime, datetime.date ) ):
#         return prevbizday_datetime( dt, specs=specs )
#
#     elif isinstance( dt, ( int, float ) ):
#         return prevbizday_datetime( dut.num2dt( dt ), specs=specs )
#
#     else:
#         raise ValueError( 'Unknown type=%s specs=%s' % ( type( dt), str( specs ) ) )
#
# import re
# dayPattern = '([-+])(.*)([bcd])'
#
# def _parse( specs ):
#     if isinstance( specs, str ):
#         m = re.match( dayPattern, specs )
#         sign, count, typ = m.groups()
#         return ( sign, int(count), typ )
#     elif isinstance( specs, ( tuple, list ) ):
#         return specs
#
# def bizday( dt, specs ):
#     ( sign, _count, _typ ) = _parse( specs )
#     if sign == '-':
#         return prevbizday( dt=dt, specs=specs )
#     elif sign == '+':
#         return nextbizday( dt=dt, specs=specs )
#     else:
#         raise ValueError( 'Unknown sign for specs=%s' % str ( specs ) )
# def formdatetime( dt, tm ):
#     '''return a datetime formed as date and time'''
#     if isinstance( dt, ( int, float ) ):
#         dt = dut.num2dt( dt )
#
#     if isinstance( tm, ( int, float ) ):
#         tm = dut.secToTime( tm )
#
#     return datetime.datetime( dt.year,  dt.month,  dt.day, tm.hour, tm.minute, tm.second )
