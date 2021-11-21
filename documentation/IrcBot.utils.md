#### `arg_command`

help="",
command_help="",
acccept_pms=True,
pass_data=False,
simplify=None,
**kwargs,


#### `custom_handler(action, **kwargs)`

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

#### `debug(*args, level=logging.DEBUG)`

logger.log(level, msg)


warning(*args, level=logging.WARNING):
msg = " ".join([str(a) for a in list(args)])
logger.log(level, msg)


tras
validateUrl(url):
if has_validators:
return validators.url(url)
else:
log(
    "You do not have the validators module installed! run `pip install validators` to use this functionality"
)


m2list(args):
return [args[i] for i in range(1, _command_max_arguments) if args[i]]


#### `log(*args, level=logging.INFO)`

if type(level) == int:
logger.log(level, msg)
elif type(level) == str:
getattr(logger, level)(msg)


debug(*args, level=logging.DEBUG):
msg = " ".join([str(a) for a in list(args)])
logger.log(level, msg)


warning(*args, level=logging.WARNING):
msg = " ".join([str(a) for a in list(args)])
logger.log(level, msg)


tras
validateUrl(url):
if has_validators:
return validators.url(url)
else:
log(
    "You do not have the validators module installed! run `pip install validators` to use this functionality"
)


m2list(args):
return [args[i] for i in range(1, _command_max_arguments) if args[i]]


#### `m2list(args)`



#### `regex_cmd_with_messsage(filters, acccept_pms=True, pass_data=False, **kwargs)`

re python library and a IrcBot.Message as a second parameter.

:param filters: regex filter
:param acccept_pms: bool. Should this command work with private messages?.
:param pass_data: If true function should accept an extra data argument.
:param kwargs:

#### `regex_cmd(filters, acccept_pms=True, **kwargs)`

library. Will not receive private messages, use regex_commands_with_message
instead.

:param filters: Regex expression
:param acccept_pms: bool. Should this command work with private messages?.
:param kwargs:

#### `setCommands(command_dict: dict, simplify=None, prefix="!")`

param: command_dict: Takes a dictionary of "command names": function's to call creating the commands for each of them.
param: simplify: Uses shortest prefixes for each command. If True the shortest differentiatable prefixes for the commands will work. Like if there is start and stop, !sta will call start and !sto will call stop. Instead of passing a function  directly you can pass in a dict like:
{"function": cb, "acccept_pms": True, "pass_data": True, "help": "This command starts the bot", "command_help": "Detailed help for this command in particular"}
if needed. The help parameter if passed will define the 'help' command.

#### `setHelpBottom(txt: str)`


:param txt: Text to display after command descriptions
:type txt: str

#### `setHelpHeader(txt: str)`


:param txt: Text to display before command descriptions
:type txt: str

#### `setHelpMenuSeparator(sep: str)`

'\n'.

:param sep: separator
:type sep: str

#### `setHelpOnPrivate(is_private)`

useful to avoide flooding if the bots has many commands.

:param is_private: if true they will be private (default False: display on the current channel)

#### `setLogging(level, logfile=None)`


:param level: int. level, (logging.DEBUG, logging.INFO, etc...)
:param logfile: str. Path for file or empty for none.

#### `setMaxArguments(n)`


:param n: number of arguments for callbacks in arg_command decorator

#### `setParseOrderTopBottom(top_bottom: bool = True)`


:param top_bottom: bool -> if True then first defined regex expressions will overwrite last ones. Default is False

#### `setPrefix(prefix)`


:param prefix: str prefix for commands

#### `setSimplifyCommands(simplify)`

simplify_arg_commands = simplify


arg_command(
command,
help="",
command_help="",
acccept_pms=True,
pass_data=False,
simplify=None,
**kwargs,


#### `setSingleMatch(singleMatch: bool)`

:param singleMatch: If true there will be only one match per command. Defaults to False (all matches will be called)
:type singleMatch: bool

#### `url_handler(**kwargs)`


:param kwargs:

#### `validateUrl(url)`

return validators.url(url)
else:
log(
    "You do not have the validators module installed! run `pip install validators` to use this functionality"
)


m2list(args):
return [args[i] for i in range(1, _command_max_arguments) if args[i]]


#### `warning(*args, level=logging.WARNING)`

logger.log(level, msg)


tras
validateUrl(url):
if has_validators:
return validators.url(url)
else:
log(
    "You do not have the validators module installed! run `pip install validators` to use this functionality"
)


m2list(args):
return [args[i] for i in range(1, _command_max_arguments) if args[i]]
