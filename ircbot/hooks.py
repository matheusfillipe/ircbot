# TODO: Use self typehints instead of class
import importlib.util
import inspect
import logging
import os
import re
from collections.abc import Callable
from functools import wraps
from typing import Awaitable, Literal, TypeAlias, get_args

from typing_extensions import Self

from ircbot.message import Message, Sendable
from ircbot.shortest_prefix import find_shortest_prefix
from ircbot.utils import debug, log


def md5_file(file):
    import hashlib

    with open(file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _reg_word(org, pref):
    opt_open = r"(?:"
    opt_close = r")?"
    return (
        re.escape(pref)
        + opt_open * (len([re.escape(c) for c in org[len(pref) :]]) > 0)
        + opt_open.join([re.escape(c) for c in org[len(pref) :]])
        + opt_close * len(org[len(pref) :])
    )


Actions = Literal["privmsg", "ping", "names", "channel", "join", "quit", "part", "dccsend"]

Regex: TypeAlias = str | re.Pattern
HookReturn = Sendable | Awaitable[Sendable | None] | None
RegexCallback = Callable[[re.Match], HookReturn]
RegexWithMessageCallback = Callable[[re.Match, Message], HookReturn]
UrlCallback = Callable[[str], HookReturn]
ArgCommandCallback = Callable[[re.Match, Message], HookReturn]


class HookHandler:
    """Defines the behavior of the bot"""

    def __init__(self):
        self.parse_order = False

        # COMMAND DECORATORS
        self.regex_commands: list[dict[Regex, Callable]] = []
        self.regex_commands_accept_pm: list[bool] = []

        self.regex_commands_with_message: list[dict[Regex, RegexWithMessageCallback]] = []
        self.regex_commands_with_message_accept_pm: list[bool] = []
        self.regex_commands_with_message_pass_data: list[bool] = []

        self.url_commands: list[UrlCallback] = []
        self.custom_handlers: dict[str, Callable] = {}
        self.arg_commands_with_message = {}

        # HOT RELOAD
        self.hot_reload_env = os.environ.get("IRCBOT_HOT_RELOAD", "False").lower() in ["true", "1", "yes", "on"]
        self.hot_reload_files = set()
        self.hot_reload_hash_map = {}

        # ARGUMENTS
        self.single_match: bool = False
        self.command_prefix: str = "!"
        self._command_max_arguments: int = 25
        self.simplify_arg_commands: bool = True

        # HELP
        self.help_msg_header: list[str] = []
        self.help_msg: dict[str, str] = {}
        self.help_msg_bottom: list[str] = []
        self.commands_help = {}
        self.help_menu_separator: str = "\n"
        self.help_on_private: bool = False

        self._defined_command_dict = {}

    def regex_cmd(self, filters: Regex, acccept_pms: bool = True, **kwargs):
        """regex_cmd. The function should take a match object from the re python
        library. Will not receive private messages, use regex_commands_with_message
        instead.

        :param filters: Regex expression
        :param acccept_pms: bool. Should this command work with private messages?.
        :param kwargs:
        """

        def wrap_cmd(func: RegexCallback):
            @wraps(func)
            def wrapped(*a, **bb):
                return func(*a, **bb)

            self._add_hot_reload(func)
            self.regex_commands.append({filters: func})
            self.regex_commands_accept_pm.append(acccept_pms)
            return wrapped

        return wrap_cmd

    def regex_cmd_with_messsage(self, filters: Regex, acccept_pms: bool = True, pass_data: bool = False, **kwargs):
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

            self._add_hot_reload(func)
            self.regex_commands_with_message.append({filters: func})
            self.regex_commands_with_message_accept_pm.append(acccept_pms)
            self.regex_commands_with_message_pass_data.append(pass_data)
            return wrapped

        return wrap_cmd

    def url_handler(self, **kwargs):
        """url_handler. The function should take a string that is the matched url.

        :param kwargs:
        """

        def wrap_cmd(func: UrlCallback):
            @wraps(func)
            def wrapped(*a, **bb):
                return func(*a, **bb)

            self._add_hot_reload(func)
            self.url_commands.append(func)
            return wrapped

        return wrap_cmd

    def custom_handler(self, action: Actions | list[Actions], **kwargs):
        """custom_handler. Add handlers for other user actions like join, quit,
        part..

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
            'dccsend' -> {'nick', 'filename', 'ip', 'port', 'size'}
        """

        def wrap_cmd(func):
            @wraps(func)
            def wrapped(*a, **bb):
                return func(*a, **bb)

            accepted_actions = set(get_args(Actions))
            if isinstance(action, str):
                if action not in accepted_actions:
                    raise ValueError(f"Invalid action {action}")
                self.custom_handlers[action] = func
            if isinstance(action, list) or isinstance(action, set):
                for a in action:
                    if a not in accepted_actions:
                        raise ValueError(f"Invalid action {a}")
                    self.custom_handlers[a] = func
            return wrapped

        return wrap_cmd

    def re_command(self, cmd, acccept_pms=True, pass_data=False, **kwargs):
        non_space: str = r"\S"
        return self.regex_cmd_with_messsage(
            rf"^{re.escape(self.command_prefix)}{cmd}{f'(?: +({non_space}+))?'*self._command_max_arguments} *$",
            acccept_pms,
            pass_data,
            **kwargs,
        )

    def set_simplify_commands(self, simplify: bool) -> Self:
        self.simplify_arg_commands = simplify
        return self

    def arg_command(
        self,
        command: str,
        help: str = "",
        command_help: str = "",
        acccept_pms: bool = True,
        pass_data: bool = False,
        simplify: bool | None = None,
        alias: str | list[str] | None = None,
        **kwargs,
    ):
        """Wrapper for setCommands.

        :param command: Command
        :param acccept_pms: bool. Should this command work with private messages?.
        param: simplify: Uses shortest prefixes for each command. If True the shortest differentiatable prefixes for the commands will work. Like if there is start and stop, !sta will call start and !sto will call stop. Instead of passing a function  directly you can pass in a dict like:
        param: help: Message to display on help command.
        param: command_help: Message to display on help command with this command's name as argument.
        alias: str or list of strings with aliases for this command
        """

        aliases = []
        if isinstance(alias, str):
            aliases = [alias]
        elif alias is None:
            aliases = []

        if simplify is None:
            simplify = self.simplify_arg_commands

        def wrap_cmd(func: ArgCommandCallback):
            @wraps(func)
            def wrapped(*a, **bb):
                return func(*a, **bb)

            self._add_hot_reload(func)
            self.arg_commands_with_message[command] = {
                "function": func,
                "acccept_pms": acccept_pms,
                "pass_data": pass_data,
                "help": help,
                "command_help": command_help,
                "simplify": simplify,
            }

            for a in aliases:
                debug(f"Adding alias {a} for {command}")
                self.arg_commands_with_message[a] = self.arg_commands_with_message[command]

            return wrapped

        return wrap_cmd

    def set_help_menu_separator(self, sep: str) -> Self:
        """Sets the separator string between the help commands. If can contain a
        '\n'.

        :param sep: separator
        :type sep: str
        """
        self.help_menu_separator = sep
        return self

    def set_help_on_private(self, is_private: bool) -> Self:
        """Defines if the help messages should be sent as private messages. This is
        useful to avoide flooding if the bots has many commands.

        :param is_private: if true they will be private (default False: display on the current channel)
        """
        self.help_on_private = is_private
        return self

    def set_help_header(self, txt: str) -> Self:
        """Adds some text to the help message before the command descriptions.

        :param txt: Text to display before command descriptions
        :type txt: str
        """
        if isinstance(txt, str):
            self.help_msg_header = [txt]
        elif isinstance(txt, list):
            self.help_msg_header = txt
        else:
            raise BaseException("You must pass wither a list of strings or a string")
        return self

    def set_help_bottom(self, txt: str) -> Self:
        """Adds some text to the help message after the command descriptions.

        :param txt: Text to display after command descriptions
        :type txt: str
        """
        if isinstance(txt, str):
            self.help_msg_bottom = [txt]
        elif isinstance(txt, list):
            self.help_msg_bottom = txt
        else:
            raise BaseException("You must pass wither a list of strings or a string")
        return self

    def set_commands(self, command_dict: dict, simplify: bool | None = None, prefix: str = "!"):
        """Defines commands for the bot from existing functions
        param: command_dict: Takes a dictionary of "command names": function's to call creating the commands for each of them.
        param: simplify: Uses shortest prefixes for each command. If True the shortest differentiatable prefixes for the commands will work. Like if there is start and stop, !sta will call start and !sto will call stop. Instead of passing a function  directly you can pass in a dict like:
        {"function": cb, "acccept_pms": True, "pass_data": True, "help": "This command starts the bot", "command_help": "Detailed help for this command in particular"}
        if needed. The help parameter if passed will define the 'help' command.
        """
        self.command_prefix = prefix

        if simplify is None:
            simplify = self.simplify_arg_commands

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

        _commands = find_shortest_prefix([c for c in command_dict.keys() if not not_regex(c)])
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
                self.re_command(
                    expression,
                    acccept_pms=True if "acccept_pms" not in cb else cb["acccept_pms"],
                    pass_data=False if "pass_data" not in cb else cb["pass_data"],
                )(cb["function"])
                self.help_msg[cmd] = f"{self.command_prefix}{cmd}: {cb['help']}" if "help" in cb else ""

                if "command_help" in cb and cb["command_help"]:
                    self.commands_help[cmd] = cb["command_help"]
                elif "help" in cb and cb["help"]:
                    self.commands_help[cmd] = cb["help"]

            elif isinstance(cb, Callable):
                self.re_command(expression)(cb)
            else:
                raise BaseException(f"Invalid command definition for {cmd}")

        self._defined_command_dict = command_dict
        if self.help_msg or self.commands_help:
            _commands = find_shortest_prefix([c for c in command_dict.keys() if not not_regex(c)] + ["help"])

            def help_menu(args, message):
                channel = message.channel
                if self.help_on_private:
                    channel = message.sender_nick

                if args[1] in self.commands_help:
                    return Message(channel, message=self.commands_help[args[1]])
                if self.help_msg:
                    if "\n" in self.help_menu_separator:
                        before = self.help_menu_separator.split("\n")[0]
                        after = self.help_menu_separator.split("\n")[-1]
                        return (
                            self.help_msg_header
                            + [Message(channel, message=after + txt + before) for txt in self.help_msg.values()]
                            + self.help_msg_bottom
                        )
                    else:
                        return (
                            self.help_menu_separator.join(self.help_msg_header)
                            + self.help_menu_separator.join(self.help_msg.values())
                            + self.help_menu_separator.join(self.help_msg_bottom)
                        )

            self.re_command(_reg_word("help", _commands["help"]))(help_menu)

    def set_prefix(self, prefix) -> Self:
        """setPrefix. Sets the prefix for arg commands.

        :param prefix: str prefix for commands
        """
        self.command_prefix = prefix
        return self

    def set_single_match(self, _single_match: bool) -> Self:
        """Defines if there will be only one command handler called. If false all regex and arg_commands will be matched against the user input.
        :param singleMatch: If true there will be only one match per command. Defaults to False (all matches will be called)
        :type singleMatch: bool
        """
        self.single_match = _single_match
        return self

    def set_parser_order(self, top_bottom: bool = True) -> Self:
        """setParseOrder.

        :param top_bottom: bool -> if True then first defined regex expressions will overwrite last ones. Default is False
        """
        self.parse_order = top_bottom
        return self

    def set_max_arguments(self, n: int) -> Self:
        """setMaxArguments.

        :param n: number of arguments for callbacks in arg_command decorator
        """
        self._command_max_arguments = n
        return self

    def _add_hot_reload(self, func):
        """Adds full path to file of function to hot_reload_files set."""
        module_path = inspect.getfile(func)
        self.hot_reload_files.add(module_path)

    def _hot_reload(self):
        """Reloads all files in hot_reload_files setting regex_commands, regex_commands_with_message, url_commands, custom_handlers"""
        state = [
            self.regex_commands,
            self.regex_commands_accept_pm,
            self.regex_commands_with_message,
            self.regex_commands_with_message_accept_pm,
            self.regex_commands_with_message_pass_data,
            self.url_commands,
            self.arg_commands_with_message,
            self.custom_handlers,
        ]
        initial_state = []
        for s in state:
            initial_state.append(s.copy())
            s.clear()

        for file in self.hot_reload_files:
            # skip current file
            if file == __file__:
                continue
            log(f"Reloading {file}")
            try:
                module_name = os.path.basename(file).split(".")[0]
                spec = importlib.util.spec_from_file_location(module_name, file)
                if spec is None:
                    log(f"Error reloading {file}: spec is None")
                    continue
                else:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

            except Exception as e:
                log(f"Error reloading {file}: {e}")
                for i, s in enumerate(state):
                    s.clear()
                    s = initial_state[i]
                raise e

    def _hot_reload_if_changed(self):
        """Checks if any of the files in hot_reload_files has changed and if so
        Only works if hot_reload_env is True.

        :return: True if any file has changed
        """
        if self.hot_reload_env:
            for module_path in self.hot_reload_files:
                new_hash = md5_file(module_path)
                current_hash = self.hot_reload_hash_map.get(module_path, None)
                self.hot_reload_hash_map[module_path] = new_hash
                if new_hash != current_hash and current_hash is not None:
                    log(f"Reloading due changes to {module_path}")
                    self._hot_reload()
                    return True
        return False
