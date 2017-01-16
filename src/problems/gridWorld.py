# -*- coding: utf8 -*-

from __future__ import unicode_literals

import itertools
import random

import numpy as np

from problems.base import BaseProblem
from consts import Spaces, ParamsTypes
import utils


CASE_TYPES = utils.enum(
    # get 5x more negative reward when crossing this region
    Water='W',
    # get 2x more negative reward when crossing this region
    Sand='S',
    # cannot cross this region
    Wall='X',
    # only get -1 reward when crossing this region
    Open='.',
    # terminate the episode, and get `successReward`
    Termination='T',
    # get min(reward) = -maxSteps when crossing this region and
    # terminate the episode
    Trap='!')

CASE_COLORS = {
    CASE_TYPES.Water: (0, 0, 0.7),
    CASE_TYPES.Sand: (0.7, 0.7, 0),
    CASE_TYPES.Wall: (0, 0, 0),
    CASE_TYPES.Open: (1, 1, 1),
    CASE_TYPES.Termination: (0, 1, 0),
    CASE_TYPES.Trap: (1, 0, 0)
}

# Grids are indexed by their
PREDEFINED_GRIDS = {
    'random': None,
    'simple': """....T
                 .....
                 .XXXX
                 .....
                 .....""",
    'complex': """..........!.T
                  ..SS......!..
                  .XWWX.....!..
                  ..SSXXXXX.!..
                  ........X.W..
                  ...!....X.W..
                  ...!....X.S..
                  ...!....X....
                  ........XXXXX
                  .............""",
    'complex2': """
........SWSWS.......WW............!...WT
..SS.....S!S.......WWWW...........!S.WWW
.XWWX.....!.........WW............!..WWW
..SSXXXXX.!XXX!XXXX!XXXXWXXX!XXXXX!.SWWW
........X.W.........X..WWW.X...........W
...!....X.W.........X...W..X........!!!!
...!....X.S.........X......X............
...!....X.....XXXXXXX......X............
........XXXXXXX............X............
...........X.....XXXXXXXXXXX............
...........X.XXXXX......................
...........X.X.WWW.XXXX.................
...........X.X........X.................
...........X.X..XXXXWWXXXXXXXXXXXXXXXXXX
...........X.X..............!...........
...........X.X..............!.!!!!.XXXX.
...........X................SSWWW!.X....
...........XXXXXXXXXXXXXXXXXXXWWWXX!!.!!
...........X...............X..WWW.......
...........X...............X.......!!!..
...........X.......!.......X..!!!..!!!..
...........X...............X..!!!..!!!..
...........X...............X..!!!.......
...........X...............X............
.......XXX.X...............XXXXXXXX!.!.!
.........!.................X......X.....
...X.!.SSSX................X.XXXX.X.!.!.
...X....WXX................X...!X.X.....
...X...XXXX................XXXXXX.X!.!.!
...X..............!........X............
WWWW.......................X............
.XXXXXXXXXXXX..............X..XXXXXXXXXX
...........WWWWWWWWWWWWWWWWXWWWWWW......
SSSSSSSSSSSS......W........X...!........
SSSSSSSSSSSS......W........XXXX!........
.................WWWW......X...!........
SXXXXX.XXXXXX......XX......X.!.!........
WWWWWWWWWWWWXXXXXX!XX......X.!..........
........XXXXX......XX......X.!..........
..................!..........!..........
"""
}


class GridWorld(BaseProblem):
    """
    Custom GridWorld problem implementation
    """
    GYM_ENVIRONMENT_NAME = None

    PARAMS = utils.extends(
        {},
        startPosX=ParamsTypes.Number,
        startPosY=ParamsTypes.Number,
        successReward=ParamsTypes.Number,
        stepReward=ParamsTypes.Number,
        sandReward=ParamsTypes.Number,
        waterReward=ParamsTypes.Number,
        failureReward=ParamsTypes.Number,
        trapReward=ParamsTypes.Number,
        **BaseProblem.PARAMS)

    PARAMS_DOMAIN = utils.extends(
        {},
        startPosX={
            'values': (0, 'random', 'center', 'episodeRandom'),
            # startPosX < width will only be checked at runtime
            'range': (0, 1000)
        },
        startPosY={
            'values': (0, 'random', 'center', 'episodeRandom'),
            # startPosY < height will only be checked at runtime
            'range': (0, 1000)
        },
        successReward={
            'values': (0, 100),
            'range': (0, 10000)
        },
        stepReward={
            'values': (-1, 0, 1),
            'range': (-100, 100)
        },
        sandReward={
            'values': (-5, -1, 0),
            'range': (-1000, 1000)
        },
        waterReward={
            'values': (-50, -10, -2, 0),
            'range': (-1000, 1000)
        },
        failureReward={
            'values': (-50, -10, -2, 0),
            'range': (-1000, 1000)
        },
        trapReward={
            'values': (-50, -10, -2, 0),
            'range': (-1000, 1000)
        },
        **BaseProblem.PARAMS_DOMAIN)

    PARAMS_DEFAULT = utils.extends(
        {},
        startPosX='episodeRandom',
        startPosY='episodeRandom',
        successReward=0,
        stepReward=-1,
        sandReward=-5,
        waterReward=-10,
        failureReward=0,
        trapReward=-50,
        **BaseProblem.PARAMS_DEFAULT)

    PARAMS_DESCRIPTION = utils.extends(
        {},
        startPosX="Starting position for the agent along the X axis.",
        startPosY="Starting position for the agent along the Y axis.",
        successReward="Success reward upon reaching a termination state.",
        stepReward="Reward received at each step into an 'Open' state.",
        sandReward="Reward received when stepping into a 'Sand' state.",
        waterReward="Reward received when stepping into a 'Water' state.",
        failureReward="Reward received when failing to reach a termination \
state after the configured number of steps.",
        trapReward="Reward received when stepping into a 'Trap' state.\
This cummulates to the negative reward already got that simulate that \
all the steps just got consumed.",
        **BaseProblem.PARAMS_DESCRIPTION)

    DOMAIN = {
        'action': Spaces.Discrete,
        'state': Spaces.Discrete
    }

    ACTION_NAMES = ['up', 'right', 'down', 'left']

    STATE_DIMENSION_NAMES = ['X', 'Y']

    def __init__(self, **kwargs):
        super(GridWorld, self).__init__(**kwargs)
        self._grid = None
        self._currentPos = None
        self._initState = None
        self._viewer = None
        self._trajectory = []

        # for rendering
        self._agentTrans = None
        self._ystep = 0
        self._xstep = 0

        self._width = 0
        self._height = 0
        self._nbSteps = 0

    def _setupGrid(self):
        # setup the grid, the `_width` and `_height` parameters
        raise NotImplementedError()

    def setup(self):
        self._setupGrid()
        # only during setup will the 'random' init state be randomized
        # use 'episodeRandom' to randomize init state at each episode
        self._currentPos = self.reset(setup=True)
        self._initState = self._currentPos

    def getStatesList(self):
        return list(itertools.product(range(self._width), range(self._height)))

    def getStatesDim(self):
        """
        Return the number of dimension of the state space
        """
        return 2

    def getStatesBounds(self):
        """
        Returns the max and min values each dimension can take.
        These are returned as two tuples, `low` and `high`, where both
        are a list of as many elements as there is dimension to the state space.
        """
        return (0, 0), (self._width - 1, self._height - 1)

    def getActionsList(self):
        return range(len(self.ACTION_NAMES))

    def _move(self, action, x, y):
        x, y = self._currentPos

        if action == 0:  # up
            y += 1
        if action == 1:  # right
            x += 1
        if action == 2:  # down
            y -= 1
        if action == 3:  # left
            x -= 1

        if x >= self._width:
            x = self._width - 1
        if y >= self._height:
            y = self._height - 1
        if x < 0:
            x = 0
        if y < 0:
            y = 0

        if chr(self._grid[x, y]) == CASE_TYPES.Wall:
            x, y = self._currentPos  # revert move

        return x, y

    def step(self, action):
        """
        The agent take the given action and receives back the new state, reward,
        whether the episode is terminated and some nothingness.
        """
        x, y = self._move(action, *self._currentPos)

        if chr(self._grid[x, y]) == CASE_TYPES.Wall:
            # error - previous state was already a wall
            self._done = True
            self._trajectory.append(self._currentPos)
            return self._currentPos, -1, self._done, {}

        reward = {
            CASE_TYPES.Water: self.waterReward,
            CASE_TYPES.Sand: self.sandReward,
            CASE_TYPES.Open: self.stepReward,
            CASE_TYPES.Termination: self.successReward,
            CASE_TYPES.Trap: (
                -(self.maxSteps - len(self._trajectory)) + self.failureReward +
                self.trapReward)
        }[chr(self._grid[x, y])]

        # termination state
        if chr(self._grid[x, y]) in [CASE_TYPES.Termination, CASE_TYPES.Trap]:
            self._done = True

        self._currentPos = (x, y)

        self._trajectory.append(self._currentPos)
        self._nbSteps += 1

        if self._nbSteps >= self.maxSteps and not self._done:
            reward += self.failureReward

        return self._currentPos, reward, self._done, {}

    def reset(self, setup=False):
        """
        Reset the state of the evironment for a new episode
        `setup` is used to let the reset function know when we're calling it
        from `setup`. If we don't, the 'random' init scheme should reset
        to the randomly choosen position instead of picking a new random one.
        """
        self._done = False
        self._nbSteps = 0

        x = None
        if (self.startPosX == 'random' and setup) or (
                self.startPosX == 'episodeRandom'):
            x = random.randint(0, self._width - 1)
        elif (self.startPosX == 'random' and not setup):
            x = self._initState[0]
        elif self.startPosX == 'center':
            x = self._width - 1
        else:
            x = int(self.startPosX)

        y = None
        if (self.startPosX == 'random' and setup) or (
                self.startPosX == 'episodeRandom'):
            y = random.randint(0, self._height - 1)
        elif (self.startPosY == 'random' and not setup):
            y = self._initState[1]
        elif self.startPosX == 'center':
            y = self._height - 1
        else:
            y = int(self.startPosX)

        self._currentPos = (x, y)
        self._trajectory = [(x, y)]

        return (x, y)

    def _renderTrajectory(self):
        from gym.envs.classic_control import rendering
        points = [(
            x * self._xstep + self._xstep / 2,
            y * self._ystep + self._ystep / 2) for x, y in self._trajectory]
        trajectory = rendering.make_polyline(points)
        trajectory.set_color(0.3, 0.3, 0.3)
        trajectory.set_linewidth(3)
        self._viewer.add_onetime(trajectory)

    def render(self, mode="human", close=False):
        """
        Render the environment server-side
        """
        if close and self._viewer is None:
            if self._viewer is not None:
                self._viewer.close()
                self._viewer = None
            return

        screen_width = 600
        screen_height = 600
        if self._viewer is None:
            from gym.envs.classic_control import rendering
            self._viewer = rendering.Viewer(screen_width, screen_height)

            # generate the grid
            xs, self._xstep = np.linspace(
                0, screen_width, self._width + 1, retstep=True)
            ys, self._ystep = np.linspace(
                0, screen_height, self._height + 1, retstep=True)

            # render the grid
            for x in xrange(self._width):
                for y in xrange(self._height):
                    l, r, t, b = (0, self._xstep, self._ystep, 0)
                    tile = rendering.FilledPolygon([
                        (l, b), (l, t), (r, t), (r, b)])
                    tile.add_attr(rendering.Transform(translation=(
                        x * self._xstep, y * self._ystep)))
                    tile.set_color(*CASE_COLORS[chr(self._grid[x, y])])
                    self._viewer.add_geom(tile)

            # render starting point
            l, r, t, b = (0, self._xstep, self._ystep, 0)
            tile = rendering.FilledPolygon([
                (l, b), (l, t), (r, t), (r, b)])
            tile.add_attr(rendering.Transform(translation=(
                self._trajectory[0][0] * self._xstep,
                self._trajectory[0][1] * self._ystep)))
            tile.set_color(0, 1.0, 1.0)
            self._viewer.add_geom(tile)

            # render grid lines
            for x in xs[1:len(xs) - 1]:
                # not including the first and last one
                line = rendering.Line((x, 0), (x, screen_height))
                self._viewer.add_geom(line)
            for y in ys[1: len(ys) - 1]:
                line = rendering.Line((0, y), (screen_width, y))
                self._viewer.add_geom(line)

            agent = rendering.make_circle(
                radius=min(
                    screen_width / (self._width + 1) / 3,
                    screen_height / (self._height + 1) / 3),
                res=30)
            self._agentTrans = rendering.Transform(translation=(
                self._currentPos[0] * self._xstep + (self._xstep / 2),
                self._currentPos[1] * self._ystep + (self._ystep / 2)))
            agent.add_attr(self._agentTrans)
            self._viewer.add_geom(agent)

        self._renderTrajectory()

        self._agentTrans.set_translation(
            self._currentPos[0] * self._xstep + (self._xstep / 2),
            self._currentPos[1] * self._ystep + (self._ystep / 2))

        self._viewer.render(return_rgb_array=(mode == 'rgb_array'))

        if close:
            if self._viewer is not None:
                self._viewer.close()
                self._viewer = None
            return

    def release(self):
        if self._viewer is not None:
            self._viewer.close()


class PresetGridWorld(GridWorld):
    """
    A gridworld implementation that offers a set of predefined grids for
    your agent to train on.
    """

    PARAMS = utils.extends(
        {},
        predefinedGrid=ParamsTypes.String,
        **GridWorld.PARAMS)

    PARAMS_DOMAIN = utils.extends(
        {},
        predefinedGrid={
            'values': PREDEFINED_GRIDS.keys()
        },
        **GridWorld.PARAMS_DOMAIN)

    PARAMS_DEFAULT = utils.extends(
        {},
        predefinedGrid='complex2',
        **GridWorld.PARAMS_DEFAULT)

    PARAMS_DESCRIPTION = utils.extends(
        {},
        predefinedGrid="Pick a predefined grid",
        **GridWorld.PARAMS_DESCRIPTION)

    def _setupGrid(self):
        rep = PREDEFINED_GRIDS[self.predefinedGrid]
        lines = [l.strip() for l in rep.split('\n') if len(l.strip()) > 0]
        self._height = len(lines)
        self._width = len(lines[0])  # all lines should have the same length
        self._grid = np.zeros([self._width, self._height], dtype=int)

        for x in xrange(self._width):
            for y in xrange(self._height):
                self._grid[x, self._height - y - 1] = ord(lines[y][x])


class RandomGridWorld(GridWorld):
    """
    A gridworld implementation that generates a random grid problem
    """

    PARAMS = utils.extends(
        {},
        width=ParamsTypes.Number,
        height=ParamsTypes.Number,
        nbTermStates=ParamsTypes.Number,
        nbTraps=ParamsTypes.Number,
        **GridWorld.PARAMS)

    PARAMS_DOMAIN = utils.extends(
        {},
        width={
            'values': (10, 20, 100),
            'range': (5, 1000)
        },
        height={
            'values': (10, 20, 100),
            'range': (5, 1000)
        },
        nbTermStates={
            'values': (0, 1, 2, 5, 10),
            'range': (0, 10000)
        },
        nbTraps={
            'values': (0, 10, 100),
            'range': (0, 10000)
        },
        **GridWorld.PARAMS_DOMAIN)

    PARAMS_DEFAULT = utils.extends(
        {},
        width=20,
        height=20,
        nbTermStates=1,
        nbTraps=100,
        **GridWorld.PARAMS_DEFAULT)

    PARAMS_DESCRIPTION = utils.extends(
        {},
        width="Controls the generated grid's width.",
        height="Controls the generated grid's height",
        nbTermStates="""Controls the number of termination states.""",
        nbTraps="""Controls the number of traps to generate.""",
        **GridWorld.PARAMS_DESCRIPTION)

    def _setupGrid(self):
        self._width = self.width
        self._height = self.height
        self._grid = np.zeros([self._width, self._height], dtype=int)

        for x in xrange(self._width):
            for y in xrange(self._height):
                self._grid[x, self._height - y - 1] = ord(CASE_TYPES.Open)

        traps = [(
            random.randint(0, self.width - 1),
            random.randint(0, self.height - 1))
            for x in xrange(self.nbTraps)
        ]
        for term in traps:
            self._grid[term[0], term[1]] = ord(CASE_TYPES.Trap)

        termStates = [(
            random.randint(0, self.width - 1),
            random.randint(0, self.height - 1))
            for x in xrange(self.nbTermStates)
        ]
        for term in termStates:
            self._grid[term[0], term[1]] = ord(CASE_TYPES.Termination)
