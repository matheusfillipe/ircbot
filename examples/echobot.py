# Simple echo bot example with random color echo because why not
from IrcBot.bot import IrcBot, utils, Color

@utils.arg_command("echo")
def echo(args, message):
    return Color(" ".join(utils.m2list(args)), Color.random())

async def onConnect(bot: IrcBot):
    await bot.join("#bots")

if __name__ == "__main__":
    bot = IrcBot("irc.dot.org.es", nick="echobot")
    bot.runWithCallback(onConnect)

# Type any string starting matching "echo" as a command like '!echo hahaha', !e how are you?' , '!ech ha!'
