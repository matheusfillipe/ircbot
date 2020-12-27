# Simple IRC Bot Framework

## What is this?

This is a simple irc bot framework that uses trio for async callback processing and allows you to
use persistent data based on user's nick and channels. The callbacks for
commands are defined by regular expressions. You might want to take a look on
the examples folder.

## How to install 

`pip install re-ircbot`

Then take one of the examples and start modifying!

## Basic usage 

### Define commands
Commands are defines with regexes using a decorator around the callback
function. Everything is async. Either user the utils.regex_cmd for
simplicity or utils.regex_cmd_with_messsage if you need to know info about the
sender and if it is a private chat.


```
    @utils.regex_cmd("^!command$")
    def handler(m):
        return "hi!"
```

The first argument of a handler function will always be a Match object: https://docs.python.org/3/library/re.html#match-objects


```
    @utils.regex_cmd_with_messsage("^who is (.*)$")
    def whoami(m, message):
        m = m.group(1)
        return f"You are {message.sender_nick} and I have no idea who {m} is"
```

With regex_cmd_with_messsage there will be 2 arguments for the handler function which are the Match and the message object. The important parameters of Message are sernder_nick, channel, message, is_private.

The callback/handler functions can return a string or a list of strings to be sent back by the bot, a Message object, a ReplyIntent or None to send nothing.

### Launch the bot
```
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
```

### Data permanency 
Data permanency is based on sqlite3. Define a variable like:

```
people = persistentData("filename.db", "table_name" , ["name", "age", "nickname"])
```

The first two arguments are self explanatory. The last is a list of columns that the table will have and that you will be able to acces through people.data, e.g. `people.data[0]["name"]` to see the name of the first registered person. people.data will be a list of dicts with the given keys/columns.

Then pass it to the bot constructor as the tables argument. Notice it takes a list since you might want to have multiple of these.:

```
bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD, tables=[people])
```

### Wait for user response

Still continuing the data permanency example, you can now modify the variable on callback functions by either using the push, pop or update methods:

```
    @utils.regex_cmd_with_messsage("^!register (.*) (.*) (.*)$") # name, age, nickname
    def handler(omsg, message):
        people.push([m.group(1), m.group(2), m.group(3)])
        # or 
        #people.push({"name": m.group(1), "age": m.group(2),"nickname": m.group(3)})
        return Message(channel=message.)

    @utils.regex_cmd_with_messsage("^!register.*$") 
    def register(m, message):
        return ReplyIntent("Enter your name, age and nickname", lambda msg: handler(original_message, msg))
```
The regexes are matched in the other they are declared and there will be only one callback for each user input, which corresponds to the first defined callback that is matched. Like in this case the handler function will run directly if some user sends "!register name 23 nickname" but the register function won't run. If they were in swapped order then register would just always run. 

A ReplyIntent means that the next message this same user sends will be handled with the passed in function. This function will just receive the string message that is sent by the user next. You can specify a different channel, user, by passing in a Message object with the desired parameters fo the ReplyIntent first argument.

### Tips and tricks (logging, async, etc)
None, strings, a list of strings and Message can be used on the same places through this library.

* None: Means no message to send, like if you just `return` on some function
* str:  If you want to just send a string or fstring
* [str1, str2, ...]: To send multiple messages.
* Message: If you want to specify the channel, or send a private message.
* ReplyIntent: If you want to set a callback for the next user message and
    stablish a dialog.

Everything is asynchronously handled so you might not want to user something
besides the push, pop and update methods for the data permanency functions and
also not try to send messages manually.

Echo bot.
```
def echo(msg):
    if msg == "stop":
        return
    return ReplyIntent(msg, echo)

@utils.regex_cmd_with_messsage(getcmd("^!include.*$", ACCEPT_PRIVATE_MESSAGES)
def include(m, message):
    return ReplyIntent(Message(channel=message.sender_nick, sender_nick=message.sender_nick, message="Hello! echo mode activated"), echo)
```
## TODO

1. SASL AUTHENTICATION



