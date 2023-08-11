from IrcBot.bot import IrcBot, utils, Color

# This is the same as the echo bot but with a reload command

@utils.arg_command("echo")
def echo(args, message):
    return Color("noooh", Color.random())

@utils.regex_cmd("^hi")
def hi(*args):
    return "Hi!"

@utils.arg_command("reload")
async def reload(bot, args, message):
    await bot.hot_reload()
    return "Reloaded"

utils.setPrefix(r"echobot\s+")

async def onConnect(bot: IrcBot):
    await bot.join("#bots")

if __name__ == "__main__":
    bot = IrcBot("irc.dot.org.es", nick="echobot")
    bot.runWithCallback(onConnect)
