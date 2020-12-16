from functools import wraps


# COMMAND DECORATORS
regex_commands=[]
regex_commands_accept_pm=[]
def regex_cmd(filters, acccept_pms=True, **kwargs):
    """regex_cmd. The function should take a match object from the re python library. Will not receive private messages, use regex_commands_with_message instead.
    :param filters: Regex expression
    :param acccept_pms: bool. Should this command work with private messages?.
    :param kwargs:
    """
    def wrap_cmd(func):
        @wraps(func)
        def wrapped (*a, **bb):
            return func(*a, **bb)
        regex_commands.append({filters: func})
        regex_commands_accept_pm.append(acccept_pms)
        return wrapped
    return wrap_cmd

regex_commands_with_message=[]
regex_commands_with_message_accept_pm=[]
regex_commands_with_message_pass_data=[]
def regex_cmd_with_messsage(filters, acccept_pms=True, pass_data=False, **kwargs):
    """regex_cmd_with_sender. The function should take a match object from the re python library and a IrcBot.Message as a second parameter.
    :param filters: regex filter
    :param acccept_pms: bool. Should this command work with private messages?.
    :param pass_data: If true function should accept an extra data argument.
    :param kwargs:
    """
    def wrap_cmd(func):
        @wraps(func)
        def wrapped (*a, **bb):
            return func(*a, **bb)
        regex_commands_with_message.append({filters: func})
        regex_commands_with_message_accept_pm.append(acccept_pms)
        regex_commands_with_message_pass_data.append(pass_data)
        return wrapped
    return wrap_cmd

url_commands=[]
def url_handler(**kwargs):
    """url_handler. The function should take a string that is the matched url
    :param kwargs:
    """
    def wrap_cmd(func):
        @wraps(func)
        def wrapped (*a, **bb):
            return func(*a, **bb)
        url_commands.append(func)
        return wrapped
    return wrap_cmd


# LOGGING SETUP
import logging
logger=None

def setLogging(level, logfile=None):
    """Sets the loggins level of the logging module.

    :param level: int. level, (logging.DEBUG, logging.INFO, etc...)
    :param logfile: str. Path for file or empty for none.
    """
    global logger
    logging.basicConfig(level=level, filename=logfile, format='%(asctime)s::%(levelname)s -> %(message)s', datefmt='%I:%M:%S %p')
    logger = logging.getLogger()
    logger.setLevel(level)

setLogging(logging.DEBUG)

def log(*args, level=logging.INFO):
    msg=" ".join([str(a) for a in list(args)])
    if type(level)==int:
        logger.log(level, msg)
    elif type(level)==str:
        getattr(logger, level)(msg)

def debug(*args, level=logging.DEBUG):
    msg=" ".join([str(a) for a in list(args)])
    logger.log(level, msg)

def warning(*args, level=logging.WARNING):
    msg=" ".join([str(a) for a in list(args)])
    logger.log(level, msg)

import validators
def validateUrl(url):
    return validators.url(url)
