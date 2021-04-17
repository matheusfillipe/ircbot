Help on module IrcBot.utils in IrcBot.bot:

NAME
    IrcBot.utils

FUNCTIONS
    debug(*args, level=10)
    
    log(*args, level=20)
    
    regex_cmd(filters, acccept_pms=True, **kwargs)
        regex_cmd. The function should take a match object from the re python library. Will not receive private messages, use regex_commands_with_message instead.
        :param filters: Regex expression
        :param acccept_pms: bool. Should this command work with private messages?.
        :param kwargs:
    
    regex_cmd_with_messsage(filters, acccept_pms=True, pass_data=False, **kwargs)
        regex_cmd_with_sender. The function should take a match object from the re python library and a IrcBot.Message as a second parameter.
        :param filters: regex filter
        :param acccept_pms: bool. Should this command work with private messages?.
        :param pass_data: If true function should accept an extra data argument.
        :param kwargs:
    
    setLogging(level, logfile=None)
        Sets the loggins level of the logging module.
        
        :param level: int. level, (logging.DEBUG, logging.INFO, etc...)
        :param logfile: str. Path for file or empty for none.
    
    url_handler(**kwargs)
        url_handler. The function should take a string that is the matched url
        :param kwargs:
    
    validateUrl(url)
    
    warning(*args, level=30)

DATA
    logger = <RootLogger root (DEBUG)>
    regex_commands = []
    regex_commands_accept_pm = []
    regex_commands_with_message = []
    regex_commands_with_message_accept_pm = []
    regex_commands_with_message_pass_data = []
    url_commands = []

FILE
    /home/matheus/.local/lib/python3.9/site-packages/IrcBot/utils.py


Attribute references
********************

An attribute reference is a primary followed by a period and a name:

   attributeref ::= primary "." identifier

The primary must evaluate to an object of a type that supports
attribute references, which most objects do.  This object is then
asked to produce the attribute whose name is the identifier.  This
production can be customized by overriding the "__getattr__()" method.
If this attribute is not available, the exception "AttributeError" is
raised.  Otherwise, the type and value of the object produced is
determined by the object.  Multiple evaluations of the same attribute
reference may yield different objects.

Related help topics: getattr, hasattr, setattr, ATTRIBUTEMETHODS, FLOAT,
MODULES, OBJECTS

