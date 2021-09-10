#TODO make a class instead of this globals crap 

import collections
import logging
import re
import sys
from functools import wraps

has_validators = False
try:
    import validators
    has_validators = True
except:
    pass

from .message import Message
from .shortestPrefix import findShortestPrefix

logger = None

parse_order = False

# COMMAND DECORATORS
regex_commands = []
regex_commands_accept_pm = []


def regex_cmd(filters, acccept_pms=True, **kwargs):
    """regex_cmd. The function should take a match object from the re python
    library. Will not receive private messages, use regex_commands_with_message
    instead.

    :param filters: Regex expression
    :param acccept_pms: bool. Should this command work with private messages?.
    :param kwargs:
    """

    def wrap_cmd(func):
        @wraps(func)
        def wrapped(*a, **bb):
            return func(*a, **bb)

        regex_commands.append({filters: func})
        regex_commands_accept_pm.append(acccept_pms)
        return wrapped

    return wrap_cmd


regex_commands_with_message = []
regex_commands_with_message_accept_pm = []
regex_commands_with_message_pass_data = []


def regex_cmd_with_messsage(filters, acccept_pms=True, pass_data=False, **kwargs):
    """regex_cmd_with_sender. The function should take a match object from the
    re python library and a IrcBot.Message as a second parameter.

    :param filters: regex filter
    :param acccept_pms: bool. Should this command work with private messages?.
    :param pass_data: If true function should accept an extra data argument.
    :param kwargs:
    """
    logging.debug("Creating regex with message: %s", filters)

    def wrap_cmd(func):
        @wraps(func)
        def wrapped(*a, **bb):
            return func(*a, **bb)

        regex_commands_with_message.append({filters: func})
        regex_commands_with_message_accept_pm.append(acccept_pms)
        regex_commands_with_message_pass_data.append(pass_data)
        return wrapped

    return wrap_cmd


url_commands = []
def url_handler(**kwargs):
    """url_handler. The function should take a string that is the matched url.

    :param kwargs:
    """

    def wrap_cmd(func):
        @wraps(func)
        def wrapped(*a, **bb):
            return func(*a, **bb)

        url_commands.append(func)
        return wrapped

    return wrap_cmd

custom_handlers = {}
def custom_handler(action, **kwargs):
    """custom_handler. Add handlers for other user actions like join, quit, part..
    :param action: str or list of strings with one or more of the possible actions
        Possible actions and function necessary arguments are:
        type             kwargs
        'privmsg' -> {'nick', 'channel', 'text'}
        'ping' -> {'ping'}
        'names' -> {'channel', 'names'}
        'channel' -> {'channel', 'channeldescription'}
        'join' -> {'nick', 'channel'}
        'quit' -> {'nick', 'text'}
        'part' -> {'nick', 'channel'}

    """

    def wrap_cmd(func):
        @wraps(func)
        def wrapped(*a, **bb):
            return func(*a, **bb)

        if isinstance(action, str):
            custom_handlers[action] = func
        if isinstance(action, list):
            for a in action:
                custom_handlers[a] = func
        return wrapped

    return wrap_cmd



command_prefix = "!"
_command_max_arguments = 10
_NonSpace = r"\S"
re_command = (
    lambda cmd, acccept_pms=True, pass_data=False, **kwargs: regex_cmd_with_messsage(
        f"^{command_prefix}{cmd}{f'(?: +({_NonSpace}+))?'*_command_max_arguments} *$",
        acccept_pms,
        pass_data,
        **kwargs,
    )
)

arg_commands_with_message = {}

simplify_arg_commands = True

def setSimplifyCommands(simplify):
    global simplify_arg_commands
    simplify_arg_commands = simplify


def arg_command(
    command,
    help="",
    command_help="",
    acccept_pms=True,
    pass_data=False,
    simplify=None,
    **kwargs,
):
    """Wrapper for setCommands.

    :param command: Command
    :param acccept_pms: bool. Should this command work with private messages?.
    param: simplify: Uses shortest prefixes for each command. If True the shortest differentiatable prefixes for the commands will work. Like if there is start and stop, !sta will call start and !sto will call stop. Instead of passing a function  directly you can pass in a dict like:
    param: help: Message to display on help command.
    param: command_help: Message to display on help command with this command's name as argument.
    """

    if simplify is None:
        simplify = simplify_arg_commands
    def wrap_cmd(func):
        @wraps(func)
        def wrapped(*a, **bb):
            return func(*a, **bb)

        arg_commands_with_message[command] = {
            "function": func,
            "acccept_pms": acccept_pms,
            "pass_data": pass_data,
            "help": help,
            "command_help": command_help,
            "simplify": simplify,
        }
        return wrapped

    return wrap_cmd


help_msg = {}
commands_help = {}
help_menu_separator = "\n"
help_on_private = False

def setHelpMenuSeparator(sep: str):
    """Sets the separator string between the help commands. If can contain a '\n'

    :param sep: separator
    :type sep: str
    """
    global help_menu_separator
    help_menu_separator = sep

def setHelpOnPrivate(is_private):
    """Defines if the help messages should be sent as private messages.
    This is useful to avoide flooding if the bots has many commands.

    :param is_private: if true they will be private (default False: display on the current channel)
    """
    global help_on_private
    help_on_private = is_private


def _reg_word(org, pref):
    opt_open = r"(?:"
    opt_close = r")?"
    return (
        re.escape(pref)
        + opt_open * (len([re.escape(c) for c in org[len(pref) :]]) > 0)
        + opt_open.join([re.escape(c) for c in org[len(pref) :]])
        + opt_close * len(org[len(pref) :])
    )

_defined_command_dict = {}
def setCommands(command_dict: dict, simplify=None, prefix="!"):
    """Defines commands for the bot from existing functions
    param: command_dict: Takes a dictionary of "command names": function's to call creating the commands for each of them.
    param: simplify: Uses shortest prefixes for each command. If True the shortest differentiatable prefixes for the commands will work. Like if there is start and stop, !sta will call start and !sto will call stop. Instead of passing a function  directly you can pass in a dict like:
    {"function": cb, "acccept_pms": True, "pass_data": True, "help": "This command starts the bot", "command_help": "Detailed help for this command in particular"}
    if needed. The help parameter if passed will define the 'help' command.
    """
    global command_prefix, help_msg, commands_help
    command_prefix = prefix

    if simplify is None:
        simplify = simplify_arg_commands

    if "help" in command_dict:
        logging.error("You should not redefine 'help'")

    def not_regex(c):
        if len(c) < 2:
            return True
        if isinstance(command_dict[c], dict) and "simplify" not in command_dict[c]:
            return not simplify
        if isinstance(command_dict[c], dict) and "simplify" in command_dict[c]:
            return not command_dict[c]["simplify"]
        return False

    _commands = findShortestPrefix([c for c in command_dict.keys() if not not_regex(c)])
    min_commands = []
    exclude_list = [c for c in command_dict.keys() if not_regex(c)]
    for cmd in command_dict:
        if cmd in exclude_list:
            min_commands.append(cmd)
        else:
            min_commands.append(_commands[cmd])

    regexps = [
        _reg_word(org, pref) if not not_regex(org) else re.escape(org)
        for org, pref in zip(command_dict.keys(), min_commands)
    ]

    for cmd, reg in zip(command_dict.keys(), regexps):
        cb = command_dict[cmd]
        # give preference if simplify comes in a dict
        simp = simplify and not not_regex(cmd)
        expression = reg if simp else cmd
        logging.debug("DEFINING %s", expression)
        logging.debug("simplify? %s", simplify)
        logging.debug("simp? %s", simp)

        if isinstance(cb, dict):
            re_command(
                expression,
                acccept_pms=True if not "acccept_pms" in cb else cb["acccept_pms"],
                pass_data=False if not "pass_data" in cb else cb["pass_data"],
            )(cb["function"])
            help_msg[cmd] = (
                f"{command_prefix}{cmd}: {cb['help']}" if "help" in cb else ""
            )

            if "command_help" in cb and cb["command_help"]:
                commands_help[cmd] = cb["command_help"]
            elif "help" in cb and cb["help"]:
                commands_help[cmd] = cb["help"]

        elif isinstance(cb, collections.abc.Callable):
            re_command(expression)(cb)
        else:
            logging.error(
                "You passed a wrong data type on setCommands for command: %s", cmd
            )
            sys.exit(1)

    _defined_command_dict = command_dict
    if help_msg or commands_help:
        _commands = findShortestPrefix(
            [c for c in command_dict.keys() if not not_regex(c)] + ["help"]
        )

        def help_menu(args, message):
            channel = message.channel
            if help_on_private:
                channel = message.sender_nick

            if args[1] in commands_help:
                return Message(channel, message=commands_help[args[1]])
            if help_msg:
                if "\n" in help_menu_separator:
                    after = help_menu_separator.split("\n")[0]
                    before = help_menu_separator.split("\n")[-1]
                    return [Message(channel, message=before + txt + after) for txt in help_msg.values()]
                else:
                    return help_menu_separator.join(help_msg.values())

        re_command(_reg_word("help", _commands["help"]))(help_menu)


def setPrefix(prefix):
    """setPrefix. Sets the prefix for arg commands

    :param prefix: str prefix for commands
    """
    global command_prefix
    command_prefix = prefix

def setParseOrderTopBottom(top_bottom:bool = True):
    """setParseOrder.
    :param top_bottom: bool -> if True then first defined regex expressions will overwrite last ones. Default is False
    """
    global parse_order
    parse_order = top_bottom

def setMaxArguments(n):
    """setMaxArguments.
    :param n: number of arguments for callbacks in arg_command decorator
    """
    global command_max_arguments
    command_max_arguments = n



# LOGGING SETUP


def setLogging(level, logfile=None):
    """Sets the loggins level of the logging module.

    :param level: int. level, (logging.DEBUG, logging.INFO, etc...)
    :param logfile: str. Path for file or empty for none.
    """
    global logger
    logging.basicConfig(
        level=level,
        filename=logfile,
        format="%(asctime)s::%(levelname)s -> %(message)s",
        datefmt="%I:%M:%S %p",
    )
    logger = logging.getLogger()
    logger.setLevel(level)


setLogging(logging.DEBUG)


def log(*args, level=logging.INFO):
    msg = " ".join([str(a) for a in list(args)])
    if type(level) == int:
        logger.log(level, msg)
    elif type(level) == str:
        getattr(logger, level)(msg)


def debug(*args, level=logging.DEBUG):
    msg = " ".join([str(a) for a in list(args)])
    logger.log(level, msg)


def warning(*args, level=logging.WARNING):
    msg = " ".join([str(a) for a in list(args)])
    logger.log(level, msg)



# Extras
def validateUrl(url):
    if has_validators:
        return validators.url(url)
    else:
        log("You do not have the validators module installed! run `pip install validators` to use this functionality")


def m2list(args):
    return [args[i] for i in range(1, _command_max_arguments) if args[i]]
