# -*- coding: utf8 -*-

from __future__ import unicode_literals

import logging
import os


class TermColors(object):
    # Reset
    Color_Off = '\033[0m'       # Text Reset

    # Regular Colors
    Black = '\033[0;30m'        # Black
    Red = '\033[0;31m'          # Red
    Green = '\033[0;32m'        # Green
    Yellow = '\033[0;33m'       # Yellow
    Blue = '\033[0;34m'         # Blue
    Purple = '\033[0;35m'       # Purple
    Cyan = '\033[0;36m'         # Cyan
    White = '\033[0;37m'        # White

    # Bold
    BBlack = '\033[1;30m'       # Black
    BRed = '\033[1;31m'         # Red
    BGreen = '\033[1;32m'       # Green
    BYellow = '\033[1;33m'      # Yellow
    BBlue = '\033[1;34m'        # Blue
    BPurple = '\033[1;35m'      # Purple
    BCyan = '\033[1;36m'        # Cyan
    BWhite = '\033[1;37m'       # White

    # Underline
    UBlack = '\033[4;30m'       # Black
    URed = '\033[4;31m'         # Red
    UGreen = '\033[4;32m'       # Green
    UYellow = '\033[4;33m'      # Yellow
    UBlue = '\033[4;34m'        # Blue
    UPurple = '\033[4;35m'      # Purple
    UCyan = '\033[4;36m'        # Cyan
    UWhite = '\033[4;37m'       # White

    # Background
    On_Black = '\033[40m'       # Black
    On_Red = '\033[41m'         # Red
    On_Green = '\033[42m'       # Green
    On_Yellow = '\033[43m'      # Yellow
    On_Blue = '\033[44m'        # Blue
    On_Purple = '\033[45m'      # Purple
    On_Cyan = '\033[46m'        # Cyan
    On_White = '\033[47m'       # White

    # High Intensity
    IBlack = '\033[0;90m'       # Black
    IRed = '\033[0;91m'         # Red
    IGreen = '\033[0;92m'       # Green
    IYellow = '\033[0;93m'      # Yellow
    IBlue = '\033[0;94m'        # Blue
    IPurple = '\033[0;95m'      # Purple
    ICyan = '\033[0;96m'        # Cyan
    IWhite = '\033[0;97m'       # White

    # Bold High Intensity
    BIBlack = '\033[1;90m'      # Black
    BIRed = '\033[1;91m'        # Red
    BIGreen = '\033[1;92m'      # Green
    BIYellow = '\033[1;93m'     # Yellow
    BIBlue = '\033[1;94m'       # Blue
    BIPurple = '\033[1;95m'     # Purple
    BICyan = '\033[1;96m'       # Cyan
    BIWhite = '\033[1;97m'      # White

    # High Intensity backgrounds
    On_IBlack = '\033[0;100m'   # Black
    On_IRed = '\033[0;101m'     # Red
    On_IGreen = '\033[0;102m'   # Green
    On_IYellow = '\033[0;103m'  # Yellow
    On_IBlue = '\033[0;104m'    # Blue
    On_IPurple = '\033[0;105m'  # Purple
    On_ICyan = '\033[0;106m'    # Cyan
    On_IWhite = '\033[0;107m'   # White

DEBUG_LOGGERS_COLORS = {}

LEVEL_COLORS = {
    logging.INFO: TermColors.Green,
    logging.WARNING: TermColors.BYellow,
    logging.ERROR: TermColors.Red,
    logging.CRITICAL: TermColors.BIRed
}

DEFAULT_COLOR = TermColors.IWhite


class ColorFormatter(logging.Formatter):

    DO_NOT_TRUNCATE = [logging.WARNING, logging.ERROR, logging.CRITICAL]
    CWD = os.getcwd()

    def __init__(self, format, lineMaxLen=-1, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        logging.Formatter.__init__(self, format, *args, **kwargs)
        self.lineMaxLen = lineMaxLen
        self.DEBUG_LOGGERS_COLORS = {
            tuple(k.split('.')): v for k, v in DEBUG_LOGGERS_COLORS.iteritems()
        }

    def _getRecordColor(self, record):
        color = None
        if record.levelno in LEVEL_COLORS:
            return LEVEL_COLORS[record.levelno]
        loggerName = record.name.split('.')
        for x in xrange(1, len(loggerName) + 1):
            k = tuple(loggerName[:x])
            if k in self.DEBUG_LOGGERS_COLORS:
                color = self.DEBUG_LOGGERS_COLORS[k]
        return color or DEFAULT_COLOR

    def format(self, record):
        color = self._getRecordColor(record)
        if not isinstance(record.msg, unicode) and\
           not isinstance(record.msg, str):
            record.msg = repr(record.msg)
        record.msg = color + record.msg + TermColors.Color_Off
        record.levelname = TermColors.Purple + record.levelname + \
            ' (' + record.name + ')' + TermColors.Color_Off
        path = record.pathname[len(self.CWD):] \
            if len(record.pathname) > len(self.CWD) else record.pathname
        path = filter(
            (lambda s: len(s) > 0), path.split('/')[:-1])
        path = '/'.join(map((lambda s: s[0]), path))
        record.filename = TermColors.Cyan + \
            './' + path + \
            ('/' if path else '') + record.filename + TermColors.Color_Off
        record.processName = TermColors.Blue + record.processName + \
            TermColors.Color_Off
        if record.exc_text:
            record.exc_text = color + record.exc_text + TermColors.Color_Off
        message = logging.Formatter.format(self, record)
        if self.lineMaxLen > -1 and len(message) > self.lineMaxLen\
                and record.levelno not in self.DO_NOT_TRUNCATE:
            message = message[:self.lineMaxLen / 2 - 5] \
                + '[...]' + message[-(self.lineMaxLen / 2 - 5):] + \
                TermColors.Color_Off
        return message


def init(colored=True):

    # get the root logger
    logger = logging.getLogger()
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    msgFormat = '%(message)s'

    Formatter = ColorFormatter if colored else logging.Formatter
    msgFormat = '%(message)s'
    formatter = Formatter(
        '%(processName)s :: %(levelname)s :: ' + msgFormat)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
