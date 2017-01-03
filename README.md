# RLViz
A webapp based on tornado, gym and visjs for reinforcement learning algorithms visualisation.
Currently support only value function display on most simple reinforcement learning algorithms. Should be improved in the near future.

![Showcase](http://i.imgur.com/DDFH4IP.png)

## Goal

The project is still in its very early phase, do not expect to see anything useful here within several months.
The goal is to implement several reinforcement learning algorithms,
from the simplest Monte Carlo value-function learning approach and slightly more advanced SARSA that uses bootstapping, to Q-learning using
value function approximation, policy gradient, actor-critics or even model-based algorithms.

The work has been inspired by the excellent [Reinforcement Learning course by David Silver]( https://www.youtube.com/watch?v=ItMutbeOHtc&index=8&list=PL7-jPKtc4r78-wCZcQn5IqyuWhBZ8fOxT&spfreload=1)

## Install and Run

The project is based on python, and uses the following libraries:
* [tornado](http://www.tornadoweb.org/en/stable/) for the web server
* [gym](https://github.com/openai/gym) for environment implementation and execution
* [numpy](https://docs.scipy.org/doc/numpy/) for matrix manipulations.

### Binaries

To install, first downlowd and setup Python for your system using your favorite package manager. Alternatively, go to the [python.org](https://www.python.org/) and download the
appropriate binaries.

You'll then need to install pip, the python package manager. The easy way is to run
`easy_install pip`, tho it may already be part of your python installation.

Recommanded but not mandatory is to install virtualenv to isolate the environment of this
project from others. This won't go into the details, but it is recommanded to refer to https://virtualenv.pypa.io/en/stable/ for more info on how to setup and activate a virtual python environment.

### Dependencies

To install the required dependencies, simply run
```
pip install -r requirements.txt
```

### Run

Simply run `./go.sh` which will start the http server. It listends on `localhost:8888` which you should be able to reach with your favorite browser shortly.

## Project Structure

Short folder and sub-folder description:

* `experiments/` simple experiments that are not, or very little correlated with the rest of the code. Code wrote as part of early stages of the development of an algorithm usually stays there. Namely:
  * `experiments/gym_test_1.py` first gym environment setup, the agent follows a dummy uniform random policy.
  * `experiments/gym_test_2.py` SARSA implementation solving simple MountainCar problem. Every 1000 episode an episode is rendered to show the progression of the training. Since SARSA performs in discrete state space but the MountainCar problem is countinuous, a `RoundingSarsa` wraps SARSA to snap all states onto a 2D discrete grid.
* `templates/`: contains tornado templates that make up the UI
* `static/`: all static css and js files. The directory is organized as `static/<module>/[js|css]/*`.
  * `static/custom/`: all home-made js/css code.
* `src/`: all (python) code that is of use to the webserver
  * `src/algorithms/`: implementation of many algorithms following the interface defined in `src/algorithms/base.py`
  * `src/problems/`: implementation of many problems following the interface defined in `src/problems/base.py` so that they can be solved by the compatible algorithms
  * `src/inspectors/`: implementation of many inspectors following the interface defined in `src/inspectors/base.py`. These are used to visualize internal evolution of the algorithms _knowledge_
* `go.sh`: run this script to start the webserver.
