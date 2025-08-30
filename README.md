[![Pypi](https://badge.fury.io/py/re-ircbot.svg)](https://pypi.org/project/re-ircbot/)
[![Chat with me on irc](https://img.shields.io/badge/-IRC-gray?logo=gitter)](https://mangle.ga/irc)

# re-ircbot, a simple irc bot library

This is a simple irc bot library that uses trio for async callback processing and allows you to
use persistent data based on user's nick and channels. The callbacks for commands are defined by regular expressions. 

It even features hot reloading for the best development experience! You might want to take a look on the examples folder.

## How to install 

`pip3 install re-ircbot`

Then take one of the examples and start modifying!

## Basic usage 

### Define regex commands

Commands are defines with regexps using a decorator around the callback
function. Everything is async. Either user the utils.regex_cmd for
simplicity or utils.regex_cmd_with_messsage if you need to know info about the
sender and if it is a private chat.


```python
    @utils.regex_cmd("^!command$")
    def handler(m):
        return "hi!"

    @utils.regex_cmd("^lol$")
    def lol(m):
        return "YOU SHALL NOT SAY LOL"
```

The first argument of a handler function will always be a Match object: https://docs.python.org/3/library/re.html#match-objects


```python
    @utils.regex_cmd_with_messsage("^who is (.*)$")
    def whoami(m, message):
        m = m.group(1)
        return f"You are {message.sender_nick} and I have no idea who {m} is"
```

With regex_cmd_with_messsage there will be 2 arguments for the handler function which are the Match and the message object. The important parameters of Message are sender_nick, channel, message, is_private.

The callback/handler functions can g a string, Message objects, Color objects or a list of any of those, to be sent back by the bot, a Message object, a ReplyIntent or None to send nothing.

### Define simple argument commands

If all you want is a bot that take simple commands like `!start` `!help` etc... You can use the `utils.arg_command` decorator:

```python
@utils.arg_command("test", "Oh this is just some test", "This command is used for like testing")
def extra(args, message):
    return Color("Random", Color.random())
```

Where you can define the command `test` and with that you are also adding it to the help menu(`utils.help_menu`) and defining the message to display for `help test`. This will automatically create the help command. args there is still a regex match object, so the arguments start from 1, like if you call `test a b c` args[1] is a, args[2] is b and so on.

You can also use the `utils.setCommands` function to add commands all together from defined functions by passing in a dict. To change the commands prefix use `utils.setPrefix`. Both setCommands and the arg_command wrapper will use `simplify=True` by default, which means the bot will accept the minimal prefix versions of the defined commands. 

Look at the examples to learn more.

### Launch the bot
```python
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
```
### Colors

You can use the Color class from IrcBot. 

* Color(text, fg, bg) Colorize text with the fg foreground and bg backdround
* Color.COLORS is the list of number codes for colors
* Color.random() gs a random color
* Color.str string version of the Color. Useful if you want to combine this with other Colors or text 

### Data permanency 
Data permanency is based on sqlite3. Define a variable like:

```python
people = persistentData("filename.db", "table_name" , ["name", "age", "nickname"])
```

The first two arguments are self explanatory. The last is a list of columns that the table will have and that you will be able to access through people.data, e.g. `people.data[0]["name"]` to see the name of the first registered person. people.data will be a list of dicts with the given keys/columns.

Then pass it to the bot constructor as the tables argument. Notice it takes a list since you might want to have multiple of these.:

```python
bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD, tables=[people])
```

### Wait for user response

Still continuing the data permanency example, you can now modify the variable on callback functions by either using the push, pop or update methods:

```python
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
The regexps are matched in the other they are declared and there will be only one callback for each user input, which corresponds to the first defined callback that is matched. Like in this case the handler function will run directly if some user sends "!register name 23 nickname" but the register function won't run. If they were in swapped order then register would just always run. 

A ReplyIntent means that the next message this same user sends will be handled with the passed in function. This function will just receive the string message that is sent by the user next. You can specify a different channel, user, by passing in a Message object with the desired parameters for the ReplyIntent first argument.

### Run independently of user input

You can call an async function after the bot connects and join a channel if it was passed to the Bot's constructor. This way you can get the bot respond independently, like send messages even if not command or regexp was sent by a user. To do this, instead of calling `bot.run()` do `bot.runWithCallback(asyncFun)`:

```python
(...)
async def asyncFun(bot):
    await bot.sleep(1) # Not necessary, I am just showing you can wait for 1 second like this
    await bot.join("#somechannel")
    await bot.send_message("Hello guys!!!!")

bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
bot.runWithCallback(mainLoop)
```
Take a look at the patternSpam.py example for more details.

### wait_for (event)

You can also use async handlers to await for user input using the bot's method `wait_for`. Here is an example to check and await for user's input:

```python
async def ask(
    bot: IrcBot,
    nick: str,
    question: str,
    expected_input=None,
    repeat_question=None,
    loop: bool = True,
    timeout_message: str = "Response timeout!",
):
    await bot.send_message(question, nick)
    resp = await bot.wait_for("privmsg", nick, timeout=10)
    while loop:
        if resp:
            if expected_input is None or resp.get("text").strip() in expected_input:
                break
            await bot.send_message(repeat_question if repeat_question else question, nick)
        else:
            await bot.send_message(timeout_message, nick)
            break
        resp = await bot.wait_for("privmsg", nick, timeout=600)
    return resp.get('text').strip() if resp else None


@utils.arg_command("test")
async def test(bot: IrcBot, args, msg):
    nick = msg.nick
    resp = await ask(bot, msg.nick, f"{nick}: say yes/no", ["yes", "no"], repeat_question="You must reply with yes or no")
    return f"Your answer is: '{resp}'"

```

Notice that awaiting for `resp = await bot.wait_for("privmsg", nick, timeout=10)` will pause the execution until either a matching event from `nick` of type `privmsg` (which means both channel messages or DM's) arrives or the timeout happens. 

Here is another example of using wait_for to detect if a user is identified with the nickserv:

``` python
async def is_identified(bot: IrcBot, nick):
    global nick_cache
    nickserv = "NickServ"
    await bot.send_message(f"status {nick}", nickserv)
    msg = await bot.wait_for(
        "notice",
        nickserv,
        timeout=5,
        cache_ttl=60,
        # We need filter because multiple notices from nickserv can come at the same time
        # if multiple requests are being made to this function all together
        filter_func=lambda m: nick in m["text"],
    )
    return msg.get("text").strip() == f"{nick} 3 {nick}" if msg else False
```

Here we used a lower timeout because nickserv should reply faster than any user, the `cache_ttl` option will keep results cached for the given time, and `filter_func` must be a callable to be ran against any matched event (even if it is a cached result). The event will be only considered valid `if filter_func` (is True).

### Middlewares

Currently simple middlewares are supported for every event handler (regex or command). A middleware is an async function that will take the bot instance and the Message and this method will run before every handler. You can decide to proceed and call the handler if this method returns `True` or deny it if it returns `False` or `None`. On that case execution will be stopped.

The method used to add a middleware function is: `bot.add_middleware(callback)`.

Here is an example for not letting the bot respond to other bots by checking the "+B" mode flag:

```python
# define some handlers here with utils.arg_commands_with_message 
# or utils.regex_commands_with_message or whatever....

async def check_no_bot(bot: IrcBot, message: Message):
    await bot.send_raw(f"WHO {message.nick}")
    resp = await bot.wait_for("who", message.nick, timeout=10, cache_ttl=10)
    if "B" in resp["modes"]:
        return False
    return True

async def on_connect(bot: IrcBot):
    await bot.send_raw(f"MODE {bot.nick} +B")

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD, strip_messages=False, use_ssl=SSL)
    bot.add_middleware(check_no_bot)
    bot.runWithCallback(on_connect)
```


## Tips and tricks (logging, async, etc)

First of all: currently it is only possible to have one bot only per python call. This means you should define only one bot per file.

None, strings, a list of strings and Message can be used on the same places through this library.

* None: Means no message to send, like if you just `return` on some function
* str:  If you want to just send a string or f-string
* [str1, str2, ...]: To send multiple messages as separated messages.
* Message: If you want to specify the channel, or send a private message.
* ReplyIntent: If you want to set a callback for the next user message and
    establish a dialog.
* Color: To send a colored message.

Everything is asynchronously handled so you might not want to user something
besides the push, pop and update methods for the data permanency functions and
also not try to send messages manually.

Echo bot.
```python
def echo(msg):
    if msg == "stop":
        return
    return ReplyIntent(msg, echo)

@utils.regex_cmd_with_messsage(getcmd("^!include.*$", ACCEPT_PRIVATE_MESSAGES)
def include(m, message):
    return ReplyIntent(Message(channel=message.sender_nick, sender_nick=message.sender_nick, message="Hello! echo mode activated"), echo)
```

## Hot reload

You can hot reload your bot with a command like:

```python
@utils.arg_command("reload")
async def reload(bot, args, message):
    await bot.hot_reload()
    return "Reloaded"
```

Or you can have it automatically track file changes using the environment variable `IRCBOT_HOT_RELOAD` for example:

```bash
IRCBOT_HOT_RELOAD=true python examples/hotreload.py                                                                                                                           <<<
```

On this mode it will automatically check and refresh when a new command is issued. Make sure to only use this in development mode!


## FAQ

Don't know how to use re match objects? convert it to a list with: `utils.m2list(args)`

To add a color with a string use `color.str + another_string`

Q. **Why aren't my regex expressions being matched?**

The regex commands you defined last will be matched first. That said, check up
the documentation for python's re module. Also notice that regex expressions do
not work for utils.arg_command or using setCommands, they commands will be
escaped by re.escape.

Q. **Can I use async functions on my callbacks?**

Yes, you can use any of the decorators with async functions as well

Q. **What happens if i send colored messages?**

Currently they will be simply treated as normal text. This bot does not care
about user input colors but it can still send colored messages.

Q. **Why my async callback doesn't work? (or how does it even work)**

Compared to non async callback functions, if you try to use an async callback
like in one of util's wrappers, you will need to pass an extra argument in the
first position that is 'bot', an IrcBot object which represents the current
bot. With this you can use IrcBot's methods within a callback function like for
a command or custom_handler.

Q. **How can I add actions for user, join, part etc.**

Take a look at the utils.custom_handler decorator.


## ROADMAP

For version 2.0:

1. [ ] SASL AUTHENTICATION
2. [x] Handle weird character's on input (Colors, fonts, underlines, glyphs etc)
3. [x] Convert utils to an actual class that can be used as a context
4. [x] Dcc file transfer

