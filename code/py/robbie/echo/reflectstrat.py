'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import robbie.echo.core as echocore
import robbie.echo.basestrat as basestrat

class Strategy(basestrat.BaseStrat):

    def __init__(self, agent):
        super(Strategy, self).__init__(agent)


