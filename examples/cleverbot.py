# Cleverbot irc bot using https://github.com/matheusfillipe/cleverbot_scraper
# pip3 install cleverbot-scraper

import logging
import shlex
import subprocess
import sys

from IrcBot.bot import IrcBot, utils
from IrcBot.utils import debug, log

from cleverbot import Cleverbot

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
# LEVEL = logging.INFO
ADMIN = "mattf"
PREFIX = "-"
HOST = 'irc.dot.org.es'
PORT = 6667
NICK = 'ken'
PASSWORD = None
USERNAME = NICK
REALNAME = NICK
CHANNELS = ["#romanian", "#bots"]
# CHANNELS = ["#bots"]
MASTER = True


if len(sys.argv) >= 2:
    NICK = sys.argv[1]
    MASTER = False

if len(sys.argv) >= 3:
    CHANNELS = [sys.argv[2]]

##################################################

sessions = {}
def reply(session: str, text: str) -> str:
    global sessions
    if session not in sessions:
        sessions[session] = Cleverbot()
    return sessions[session].send(text)

@utils.regex_cmd_with_messsage(fr"(?i)^((?:.*\s)?{NICK}([\s|,|\.|\;|\?|!|:]*)(?:\s.*)?)$", False)
def mention(args, message):
    text = args[1].strip()
    last = args[2] if args[2] else ""
    text.replace(f" {NICK}{last}", " ")
    nick = message.sender_nick
    session = f'{NICK}_{nick}'
    return f"{nick}: {reply(session, text)}"


@utils.arg_command("restart")
def restart(args, message):
    if message.sender_nick == ADMIN and MASTER:
        subprocess.Popen("pm2 restart 22", shell=True)

pids = {}
@utils.arg_command("del")
def _del(args, message):
    nicks = utils.m2list(args)
    output = []
    if message.sender_nick == ADMIN:
        if NICK in nicks:
            sys.exit(0)
    if message.sender_nick == ADMIN and MASTER:
        for nick in nicks:
            if nick not in pids:
                output.append(f"{message.sender_nick}: {nick} is not in use!")
                continue
            pids[nick].kill()
            pids.pop(nick)
    return output

@utils.arg_command("add")
def add(args, message):
    nicks = utils.m2list(args)
    if message.sender_nick == ADMIN and MASTER:
        for nick in nicks:
            if nick in pids:
                return f"{message.sender_nick}: {nick} is already in use!"
        for nick in nicks:
            pids[nick] = subprocess.Popen(f"python3 /home/mattf/projects/ircbots/cbbot.py {shlex.quote(nick)} '{message.channel}'", stdout=subprocess.PIPE, shell=True)


##################################################
# RUNNING THE BOT                                #
##################################################

async def onConnect(bot: IrcBot):
    for channel in CHANNELS:
        await bot.join(channel)
    await bot.send_message("Hello everyone !!!")

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    utils.setPrefix(PREFIX)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.runWithCallback(onConnect)
