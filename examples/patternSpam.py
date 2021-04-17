from IrcBot.bot import IrcBot, utils, Color
from IrcBot.utils import log, debug
from copy import copy
import logging
import random

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.ERROR
HOST = 'irc.dot.org.es'
PORT = 6667
NICK = '|'
PASSWORD = ''
USERNAME = NICK
REALNAME = NICK
CHANNELS = ["#races"]  # , "#lobby",]
ACCEPT_PRIVATE_MESSAGES = True
PREFIX = ';'
DBFILEPATH = NICK+".db"

############################################################


utils.command_prefix = PREFIX
waitForStart = True


@utils.command("start", ACCEPT_PRIVATE_MESSAGES)
def start(args, message):
    global waitForStart
    waitForStart = False
    return [args[i] for i in range(1, utils.command_max_arguments)]


@utils.command("stop", ACCEPT_PRIVATE_MESSAGES)
def stop(args, message):
    global waitForStart
    waitForStart = True

# Loop initialization


async def mainLoop(bot: IrcBot):
    global waitForStart
    await bot.send_message(Color("HELLO!!!!!", Color.red, Color.black))
    while True:
        l = 1
        r = 14
        w = 15
        c = True # Direction (true = right)
        while not waitForStart:
            await bot.send_message(Color(l*"  ", bg=Color.red).str + Color("          ", bg=Color.black).str + Color(r*"  ", bg=Color.red).str)
            if c:
                l += 1
                r = w-l
            else:
                l -= 1
                r = w-l
            if l == w or l == 1:
                c = not c
            await bot.sleep(.5)
        await bot.sleep(1)


##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.runWithCallback(mainLoop)
