<!-- markdownlint-disable -->

<a href="../../documentation/IrcBot/bot#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `IrcBot.bot`




**Global Variables**
---------------
- **BUFFSIZE**
- **MAX_MESSAGE_LEN**


---

<a href="../../documentation/IrcBot/bot/BotConnectionError#L35"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `BotConnectionError`








---

<a href="../../documentation/IrcBot/bot/Color#L38"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Color`
Colorcodes enum. 

<a href="../../documentation/IrcBot/bot/__init__#L78"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(text, fg='00', bg=None)
```








---

<a href="../../documentation/IrcBot/bot/colors#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `colors`

```python
colors()
```

Returns the color names. 

---

<a href="../../documentation/IrcBot/bot/random#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `random`

```python
random()
```






---

<a href="../../documentation/IrcBot/bot/dbOperation#L102"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `dbOperation`




<a href="../../documentation/IrcBot/bot/__init__#L107"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(data={}, id={}, op=0)
```









---

<a href="../../documentation/IrcBot/bot/tempData#L113"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `tempData`




<a href="../../documentation/IrcBot/bot/__init__#L114"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__()
```

Initializes a temporary data object that can be retrieved from the same user and channel. 




---

<a href="../../documentation/IrcBot/bot/get#L134"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get`

```python
get(msg)
```

Returns data for user channel of the given message. 

:param msg: Message object 

---

<a href="../../documentation/IrcBot/bot/pop#L127"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `pop`

```python
pop(msg)
```

Deletes data for user channel of the given message. 

:param msg: Message object 

---

<a href="../../documentation/IrcBot/bot/push#L119"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `push`

```python
push(msg, data)
```

Stores any data for the current nick and channel. 

:param msg: Message object :param data: Value to store (Any) 


---

<a href="../../documentation/IrcBot/bot/persistentData#L142"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `persistentData`




<a href="../../documentation/IrcBot/bot/__init__#L143"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(filename, name, keys)
```

__init__. 

:param name: Name of the table :param keys: List of strings. Names for each column :param blockDB: If true the database connection will be kept open. This can increase performance but you will have to shut down the bot in case you want to edit the database file manually. 

You can have acess to the data list with self.data 




---

<a href="../../documentation/IrcBot/bot/clear#L198"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `clear`

```python
clear()
```

Clear all the proposed modifications. 

---

<a href="../../documentation/IrcBot/bot/fetch#L164"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `fetch`

```python
fetch()
```

fetches the list of dicts/items with ids. 

---

<a href="../../documentation/IrcBot/bot/initDB#L161"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `initDB`

```python
initDB(filename)
```





---

<a href="../../documentation/IrcBot/bot/pop#L180"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `pop`

```python
pop(id)
```

Removes the row based on the id. (You can see with self.data) 

:param id: int 

---

<a href="../../documentation/IrcBot/bot/push#L169"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `push`

```python
push(items)
```

push. Add new items to the table. 

:param items: list or single dict. 

---

<a href="../../documentation/IrcBot/bot/update#L188"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `update`

```python
update(id, item)
```

update. 

:param id: id of item to update, change. :param item: New item to replace with. This dict doesn't need to have all keys/columns, just the ones to be changed. 


---

<a href="../../documentation/IrcBot/bot/IrcBot#L203"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IrcBot`
IrcBot. 

<a href="../../documentation/IrcBot/bot/__init__#L206"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(
    host,
    port=6667,
    nick='bot',
    channels=[],
    username=None,
    password='',
    server_password='',
    use_sasl=False,
    use_ssl=False,
    delay=False,
    accept_join_from=[],
    tables=[],
    custom_handlers={},
    strip_messages=True
)
```

Creates a bot instance joining to the channel if specified. 

:param host: str. Server hostname. ex: "irc.freenode.org" :param port: int. Server port. default 6665 :param nick: str. Bot nickname. If this is set but username is not set then this will be used as the username for authentication if password is set. :param channel: List of strings of channels to join or string for a single channel. You can leave this empty can call .join manually. :param username: str. Username for authentication. :param password: str. Password for authentication. :param server_password: str. Authenticate with the server. :param use_sasl: bool. Use sasl autentication. (Still not working. Don't use this!) :param delay: int. Delay after nickserv authentication :param accept_join_from: str. Who to accept invite command from ([]) :param tables: List of persistentData to be registered on the bot. :param strip_messages: bool. Should messages be stripped (for *_with_message decorators) :param custom_handlers:{type: function, ...} Dict with function values to be called to handle custom server messages. Possible types (keys) are: type             kwargs 'privmsg' -> {'nick', 'channel', 'text'} 'ping' -> {'ping'} 'names' -> {'channel', 'names'} 'channel' -> {'channel', 'channeldescription'} 'join' -> {'nick', 'channel'} 'quit' -> {'nick', 'text'} 'part' -> {'nick', 'channel'} 




---

<a href="../../documentation/IrcBot/bot/check_reconnect#L456"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `check_reconnect`

```python
check_reconnect()
```





---

<a href="../../documentation/IrcBot/bot/check_tables#L552"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `check_tables`

```python
check_tables()
```





---

<a href="../../documentation/IrcBot/bot/close#L894"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `close`

```python
close()
```

Stops the bot and loop if running. 

---

<a href="../../documentation/IrcBot/bot/connect#L373"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `connect`

```python
connect()
```





---

<a href="../../documentation/IrcBot/bot/data_handler#L620"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `data_handler`

```python
data_handler(s, data)
```





---

<a href="../../documentation/IrcBot/bot/db_operation_loop#L571"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `db_operation_loop`

```python
db_operation_loop()
```





---

<a href="../../documentation/IrcBot/bot/fetch_tables#L562"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `fetch_tables`

```python
fetch_tables()
```





---

<a href="../../documentation/IrcBot/bot/join#L477"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `join`

```python
join(channel)
```

joins a channel. 

:param channel: str. Channel name. Include the '#', eg. "#lobby" 

---

<a href="../../documentation/IrcBot/bot/list_channels#L485"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `list_channels`

```python
list_channels()
```

list_channels of the irc server. 

They will be available as a list of strings under: bot.server_channels 

---

<a href="../../documentation/IrcBot/bot/list_names#L495"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `list_names`

```python
list_names(channel)
```

Lists users nicks in channel.  Also check bot.channel_names for a non sanitized version(like starting with ~ & % @ + for operators, moderators, etc; if you want to detect them) 

:param channel:str channel name 

---

<a href="../../documentation/IrcBot/bot/message_task_loop#L538"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `message_task_loop`

```python
message_task_loop()
```





---

<a href="../../documentation/IrcBot/bot/ping_confirmation#L354"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ping_confirmation`

```python
ping_confirmation(s)
```





---

<a href="../../documentation/IrcBot/bot/process_result#L595"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `process_result`

```python
process_result(result, channel, sender_nick, is_private)
```





---

<a href="../../documentation/IrcBot/bot/run#L340"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `run`

```python
run(async_callback=None)
```

Simply starts the bot 

param: async_callback: async function to be called. 

---

<a href="../../documentation/IrcBot/bot/runWithCallback#L322"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `runWithCallback`

```python
runWithCallback(async_callback)
```

starts the bot with an async callback. 

Useful if you want to use bot.send without user interaction. param: async_callback: async function to be called. 

---

<a href="../../documentation/IrcBot/bot/run_bot_loop#L582"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `run_bot_loop`

```python
run_bot_loop(s)
```

Starts main bot loop waiting for messages. 

---

<a href="../../documentation/IrcBot/bot/send_message#L508"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `send_message`

```python
send_message(message, channel=None)
```

Sends a text message. The message will be enqueued and sent whenever the messaging loop arrives on it. 

:param message: Can be a str, a list of str or a IrcBot.Message object. :param channel: Can be a str or a list of str. By default it is all channels the bot constructor receives. Instead of the channel name you can pass in a user nickname to send a private message. 

---

<a href="../../documentation/IrcBot/bot/send_raw#L469"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `send_raw`

```python
send_raw(data: str)
```

send_raw. Sends a string to the irc server 

:param data: :type data: str 

---

<a href="../../documentation/IrcBot/bot/sleep#L347"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `sleep`

```python
sleep(time)
```

Waits for time. 

Asynchronous wrapper for trip.sleep 

---

<a href="../../documentation/IrcBot/bot/start_with_callback#L330"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `start_with_callback`

```python
start_with_callback()
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
