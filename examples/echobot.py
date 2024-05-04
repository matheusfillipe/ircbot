# Simple echo bot example with random color echo because why not
from ircbot import Color, IrcBot, utils

bot = IrcBot("irc.dot.org.es", nick="echobot", use_ssl=True, port=6697)


@bot.arg_command("echo")
def echo(args, message):
    return Color(" ".join(utils.m2list(args)), Color.random())


@bot.regex_cmd_with_messsage("^hi$", False)
def hi(args, message):
    return "hello!"


async def on_connect():
    await bot.join("#bots")
    await bot.send_message("Hello smelly nerds!", "#bots")


if __name__ == "__main__":
    bot.run_with_callback(on_connect)

# Type any string starting matching "echo" as a command like '!echo hahaha', !e how are you?' , '!ech ha!'
