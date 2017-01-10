# -*- coding: utf8 -*-

from __future__ import unicode_literals

import itertools
import math

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
    # get min(reward) = -5 x maxSteps when crossing this region and
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
                 ....."""
}


class GridWorld(BaseProblem):
    """
    Custom GridWorld problem implementation
    """
    GYM_ENVIRONMENT_NAME = None

    PARAMS = utils.extends(
        {},
        width=ParamsTypes.Number,
        height=ParamsTypes.Number,
        startPosX=ParamsTypes.Number,
        startPosY=ParamsTypes.Number,
        nbTermStates=ParamsTypes.Number,
        successReward=ParamsTypes.Number,
        predefinedGrid=ParamsTypes.String,
        **BaseProblem.PARAMS)

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
        nbTermStates={
            'values': (0, 1, 2, 5, 10),
            'range': (0, 10000)
        },
        successReward={
            'values': (0, 100),
            'range': (0, 10000)
        },
        predefinedGrid={
            'values': PREDEFINED_GRIDS.keys()
        },
        **BaseProblem.PARAMS_DOMAIN)

    PARAMS_DEFAULT = utils.extends(
        {},
        width=20,
        height=20,
        startPosX=0,
        startPosY=0,
        nbTermStates=1,
        successReward=100,
        predefinedGrid='simple',
        **BaseProblem.PARAMS_DEFAULT)

    PARAMS_DESCRIPTION = utils.extends(
        {},
        width="If the grid is randomly generated, this controls its width.",
        height="If the grid is randomly generated, this controls its height",
        startPosX="Starting position for the agent along the X axis.",
        startPosY="Starting position for the agent along the Y axis.",
        nbTermStates="""If the grid is randomly generated, this controls the
number of termination states to generate.""",
        successReward="Success reward upon reaching a termination state.",
        predefinedGrid="Pick a predefined grid or leave random grid generation",
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

    def _setupRandom(self):
        self._grid = np.zeros([self.width, self.height], dtype=int)
        raise NotImplementedError()

    def _setupPreset(self):
        rep = PREDEFINED_GRIDS[self.predefinedGrid]
        lines = [l.strip() for l in rep.split('\n')]
        self.height = len(lines)
        self.width = len(lines[0])  # all lines should have the same length
        self._grid = np.zeros([self.width, self.height], dtype=int)

        for x in xrange(self.width):
            for y in xrange(self.height):
                self._grid[x, self.height - y - 1] = ord(lines[y][x])

    def setup(self):
        # generate the grid
        if self.predefinedGrid == 'random':
            self._setupRandom()
        else:
            self._setupPreset()

        # only during setup will the 'random' init state be randomized
        # use 'episodeRandom' to randomize init state at each episode
        self._currentPos = self.reset(setup=True)
        self._initState = self._currentPos
        self._grid[self._initState[0], self._initState[1]] = ord(
            CASE_TYPES.Open)

    def getStatesList(self):
        return list(itertools.product(range(self.width), range(self.height)))

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

        if x >= self.width:
            x = self.width - 1
        if y >= self.height:
            y = self.height - 1
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
            CASE_TYPES.Water: -5,
            CASE_TYPES.Sand: -2,
            CASE_TYPES.Open: -1,
            CASE_TYPES.Termination: self.successReward,
            CASE_TYPES.Trap: -5 * self.maxSteps
        }[chr(self._grid[x, y])]

        # termination state
        if chr(self._grid[x, y]) in [CASE_TYPES.Termination, CASE_TYPES.Trap]:
            self._done = True

        self._currentPos = (x, y)

        self._trajectory.append(self._currentPos)
        return self._currentPos, reward, self._done, {}

    def reset(self, setup=False):
        """
        Reset the state of the evironment for a new episode
        `setup` is used to let the reset function know when we're calling it
        from `setup`. If we don't, the 'random' init scheme should reset
        to the randomly choosen position instead of picking a new random one.
        """
        self._done = False

        x = None
        if (self.startPosX == 'random' and setup) or (
                self.startPosX == 'episodeRandom'):
            x = math.randint(0, self.width - 1)
        elif (self.startPosX == 'random' and not setup):
            x = self._initState[0]
        elif self.startPosX == 'center':
            x = self.width - 1
        else:
            x = int(self.startPosX)

        y = None
        if (self.startPosX == 'random' and setup) or (
                self.startPosX == 'episodeRandom'):
            y = math.randint(0, self.height - 1)
        elif (self.startPosY == 'random' and not setup):
            y = self._initState[1]
        elif self.startPosX == 'center':
            y = self.height - 1
        else:
            y = int(self.startPosX)

        print "reset to ", x, y
        self._currentPos = (x, y)
        self._grid[x, y] = ord(
            CASE_TYPES.Open)

        self._trajectory = [(x, y)]

        return (x, y)

    def _renderTrajectory(self):
        from gym.envs.classic_control import rendering
        points = [(
            x * self._xstep + self._xstep / 2,
            y * self._ystep + self._ystep / 2) for x, y in self._trajectory]
        trajectory = rendering.make_polyline(points)
        trajectory.set_color(0.3, 0.3, 0.3)
        trajectory.set_linewidth(4)
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
                0, screen_width, self.width + 1, retstep=True)
            ys, self._ystep = np.linspace(
                0, screen_height, self.height + 1, retstep=True)

            # render the grid
            for x in xrange(self.width):
                for y in xrange(self.height):
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
                    screen_width / (self.width + 1) / 10,
                    screen_height / (self.height + 1) / 10),
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
