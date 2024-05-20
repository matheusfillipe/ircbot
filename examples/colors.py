import logging
import random
from copy import copy

from ircbot import Color, IrcBot, utils
from ircbot.utils import debug, log

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = "irc.dot.org.es"
PORT = 6667
NICK = "uselessbot"
PASSWORD = ""
USERNAME = NICK
REALNAME = NICK
CHANNELS = ["#bots"]  # , "#lobby",]
ACCEPT_PRIVATE_MESSAGES = True
DBFILEPATH = NICK + ".db"

############################################################

utils.set_loglevel(LEVEL, LOGFILE)
bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)

gayColors = copy(Color.COLORS)
[gayColors.remove(k) for k in [Color.white, Color.gray, Color.light_gray, Color.black]]


@bot.regex_cmd_with_message("^gay (.+)$", ACCEPT_PRIVATE_MESSAGES)
def gay(args, message):
    # use .text or .str to extract string values
    return "".join([Color(c, random.choice(gayColors)).str for c in args[1]])


@bot.regex_cmd_with_message("^sep$", ACCEPT_PRIVATE_MESSAGES)
def separator(args, message):
    # you can also retunr a Color object or a list of colors
    return [
        Color(" " * 120, bg=Color.purple),
        Color(" " * 120, bg=Color.white),
        Color(" " * 120, bg=Color.light_green),
        Color(" " * 120, bg=Color.red),
    ]


##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    bot.run()
