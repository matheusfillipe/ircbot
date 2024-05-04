# Simple echo bot example with random color echo because why not
import logging

from ircbot import Color, IrcBot, Message, utils

utils.set_loglevel(logging.DEBUG)
bot = (
    IrcBot("irc.dot.org.es", nick="echobot", channels=["#bots"])
    .set_prefix("'")
    .set_max_arguments(25)
    .set_simplify_commands(False)
)  # Accept 25 command arguments at max


@bot.arg_command("echo", "Echo command", "It will return all passed arguments colored: echo [arg1] [arg2] ....")
def echo(args, message):
    utils.log("echoing")
    return " ".join(utils.m2list(args))  # m2list converts a re.match to a list


@bot.arg_command("rainbow", "Echo but with multiple colors", "rainbow [text]")
def rainbow(args, message):
    utils.log("rainbowing")
    return "".join([Color(char, Color.random()).str for char in " ".join(utils.m2list(args))])


@bot.arg_command(
    "send",
    "Sends a delayed message to a user or channel",
    "This command can schedule the sending of a message: send [channel|user] [delay] [message]",
)
async def send(args, message):  # If a handler is async, its first argument will be the bot itself
    args = utils.m2list(args)
    if len(args) < 3:
        return "Check help send"
    if not args[1].isdigit():
        return "Delay argument should be integer and in seconds"
    utils.log("waiting")
    await bot.sleep(int(args[1]))  # Wait for the delay

    # Sends the message. The channel can be also a username for private messages
    utils.log("sending")
    await bot.send_message(Message(channel=args[0], message=" ".join(args[2:])))


@bot.arg_command("list", "Lists users on the chat")
async def list_u(args, message):
    names = bot.channel_names[message.channel]
    return [f"HELLO {', '.join(names)}", "I am glad to see you all!!!"]


# Handles user quit or exit chat
@bot.custom_handler(["part", "quit"])
def on_quit(nick, channel="", text=""):
    return f"Bye {nick}, I will miss you :(  oh it is too late now"


# Handles user join
@bot.custom_handler("join")
def on_enter(nick, channel):
    if nick == "echobot":  # Ignore myself ;)
        return None
    return f"Hello {nick} I am glad to see you!!!"


if __name__ == "__main__":
    bot.run()
