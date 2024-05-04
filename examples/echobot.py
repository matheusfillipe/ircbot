# Simple echo bot example with random color echo because why not
from ircbot import IrcBot, utils, Color

@utils.arg_command("echo")
def echo(args, message):
    return Color(" ".join(utils.m2list(args)), Color.random())

async def on_connect(bot: IrcBot):
    await bot.join("#bots")

if __name__ == "__main__":
    bot = IrcBot("irc.dot.org.es", nick="echobot", use_ssl=True, port=6697)
    bot.run_with_callback(on_connect)

# Type any string starting matching "echo" as a command like '!echo hahaha', !e how are you?' , '!ech ha!'
