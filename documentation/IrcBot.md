Help on module IrcBot.bot in IrcBot:

NAME
    IrcBot.bot - # -*- coding: utf-8 -*-

CLASSES
    builtins.object
        IrcBot
        Message
        ReplyIntent
        dbOperation
        persistentData
        tempData
    
    class IrcBot(builtins.object)
     |  IrcBot(host, port=6665, nick='bot', channels=[], username=None, password='', nickserv_auth=False, use_sasl=False, tables=[])
     |  
     |  IrcBot.
     |  
     |  Methods defined here:
     |  
     |  __del__(self)
     |  
     |  __init__(self, host, port=6665, nick='bot', channels=[], username=None, password='', nickserv_auth=False, use_sasl=False, tables=[])
     |      Creates a bot instance joining to the channel if specified
     |      
     |      :param host: str. Server hostname. ex: "irc.freenode.org"
     |      :param port: int. Server port. default 6665
     |      :param nick: str. Bot nickname. If this is set but username is not set then this will be used as the username for authentication if password is set.
     |      :param channel: List of strings of channels to join or string for a single channel. You can leave this empty can call .join manually.
     |      :param username: str. Username for authentication.
     |      :param password: str. Password for authentication.
     |      :param nickserv_auth: bool. Authenticate with 'PRIVMSG NickServ :IDENTIFY' . Should work in most servers.
     |      :param use_sasl: bool. Use sasl autentication. (Still not working. Don't use this!)
     |      :param tables: List of persistentData to be registered on the bot.
     |  
     |  async check_tables(self)
     |  
     |  close(self)
     |      Stops the bot and loop if running.
     |  
     |  async connect(self)
     |  
     |  async data_handler(self, s, data)
     |  
     |  async db_operation_loop(self)
     |  
     |  fetch_tables(self)
     |  
     |  async join(self, channel)
     |      joins a channel.
     |      :param channel: str. Channel name. Include the '#', eg. "#lobby"
     |  
     |  async message_task_loop(self)
     |  
     |  async process_result(self, result, channel, sender_nick, is_private)
     |  
     |  run(self)
     |  
     |  async run_bot_loop(self, s)
     |      Starts main bot loop waiting for messages.
     |  
     |  async send_message(self, message, channel=None)
     |      Sends a text message.
     |      :param message: Can be a str, a list of str or a IrcBot.Message object. 
     |      :param channel: Can be a str or a list of str. By default it is all channels the bot constructor receives. Instead of the channel name you can pass in a user nickname to send a private message.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Message(builtins.object)
     |  Message(channel='', sender_nick='', message='', is_private=False)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, channel='', sender_nick='', message='', is_private=False)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class ReplyIntent(builtins.object)
     |  ReplyIntent(message, func)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, message, func)
     |      __init__.
     |      :param message: Message to send. You can use a message object if you want to change channel or make it a pm.
     |      :param func: Function to call passing the received full message string that the user will reply with. This is useful for building dialogs. This function must either return None, a message to send back (str or IrcBot.Message) or another ReplyIntent. It must receive one argument.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class dbOperation(builtins.object)
     |  dbOperation(data={}, id={}, op=0)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, data={}, id={}, op=0)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  ADD = 1
     |  
     |  REMOVE = -1
     |  
     |  UPDATE = 0
    
    class persistentData(builtins.object)
     |  persistentData(filename, name, keys)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, filename, name, keys)
     |      __init__.
     |      
     |      :param name: Name of the table
     |      :param keys: List of strings. Names for each column
     |      :param blockDB: If true the database connection will be kept open. This can increase performance but you will have to shut down the bot in case you want to edit the database file manually. 
     |      
     |      You can have acess to the data list with self.data
     |  
     |  clear(self)
     |      Clear all the proposed modifications.
     |  
     |  fetch(self)
     |      fetches the list of dicts/items with ids.
     |  
     |  initDB(self, filename)
     |  
     |  pop(self, id)
     |      Removes the row based on the id. (You can see with self.data)
     |      :param id: int
     |  
     |  push(self, items)
     |      push. Add new items to the table
     |      :param items: list or single dict.
     |  
     |  update(self, id, item)
     |      update.
     |      :param id: id of item to update, change.
     |      :param item: New item to replace with. This dict doesn't need to have all keys/columns, just the ones to be changed.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class tempData(builtins.object)
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Initializes a temporary data object that can be retrieved from the same user and channel.
     |  
     |  get(self, msg)
     |      Returns data for user channel of the given message.
     |      :param msg: Message object
     |  
     |  pop(self, msg)
     |      Deletes data for user channel of the given message.
     |      :param msg: Message object
     |  
     |  push(self, msg, data)
     |      Stores any data for the current nick and channel.
     |      :param msg: Message object
     |      :param data: Value to store (Any)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

DATA
    BUFFSIZE = 2048
    logger = <RootLogger root (DEBUG)>

FILE
    /home/matheus/.local/lib/python3.9/site-packages/IrcBot/bot.py


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

