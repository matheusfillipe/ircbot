from IrcBot.bot import IrcBot, utils
from IrcBot.utils import log, debug
import logging
import os
from copy import deepcopy

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = 'irc.server.com'
PORT = 6665
NICK = 'translator'
PASSWORD = ''
USERNAME = 'translator'
REALNAME = 'simple_bot'
FREENODE_AUTH = True
SINGLE_CHAN = True
CHANNELS = ["#english",  "#spanish"]  # , "#lobby",]
ACCEPT_PRIVATE_MESSAGES = True
DBFILEPATH = NICK+".db"

# A maximum of 3 simultaneously auto translations for each users
MAX_AUTO_LANGS = 3

INFO_CMDS={
     r"^!linux.*$": "The OS this bot runs on",
     "^!rules.*$" : [f"1. You can only have {MAX_AUTO_LANGS} auto translations active simultaneously", "2. Do not use this bot to spam"],
    "^!help auto.*$": ["!auto [src_iso_code] [dest_iso_code] Sets the automatic translation from the source language to the target language as specified in the command.",
             "!auto show Displays the current source and target language or languages in place in the channel.",
             "!auto off [dest_iso_code] Disables automatic translation to the specified target language.",
             "!auto off Clears all rules for automatic translations in the channel."],
    "^!help.*": ["@: Manually sets the target language for the current line, like so: @es Hello friends. This should translate 'Hello friends' to Spanish. The source language is detected automatically.",
                  "Language iso codes: http://ix.io/2HAN, or https://cloud.google.com/translate/docs/languages",
                  "!auto: automatically translate everything you send. Use '!help auto' for more info."],
 
#    r"^(.*) linux ": "Do you mean the best OS?",
#    r"^(.*) vim ": "Do you mean the best Text editor???",
}


# Useful if connecting to freenode from a blacklisted ip that will require SASL
USE_SASL = False
utils.setParseOrderTopBottom()

# Uncoment to use password from environment PW variable, like if you run:
# `PW=mypw python bot.py`

#PASSWORD=os.environ['PW']


##################################################
# BOT COMMANDS DEFINITIONS                       #
##################################################

from google_trans_new import google_translator

auto_translate = []
auto_nicks = []

for r in INFO_CMDS:
    @utils.regex_cmd(r, ACCEPT_PRIVATE_MESSAGES)
    def info_cmd(m, regexp=r):
        return INFO_CMDS[regexp]

def translate(m, message, dst, src="auto"):
    if type(m) != str:
        m = m.group(1)
    logging.info("Translating: " + m)
    translator = google_translator()
    if translator.detect(m)[0] == dst:
        return
    msg = translator.translate(m, lang_tgt=dst, lang_src=src)
    return f"{message.sender_nick} ({dst.upper()}) ->  {str(msg)}"
 
@utils.regex_cmd_with_messsage("^@(.*)$", ACCEPT_PRIVATE_MESSAGES)
def translate_cmd(m, message):
    m = m.group(1)
    lang = m.split(" ")[0]
    if len(lang) == 2:
        m = " ".join(m.split(" ")[1:])
    else:
        lang = "en"
    return translate(m, message, lang)

@utils.regex_cmd_with_messsage("^!auto (.*)$", ACCEPT_PRIVATE_MESSAGES)
def auto_conf(m, message):
    src = m.group(1).strip()
    if src == "show":
        if message.nick in auto_nicks:
            langs=[]
            for au in auto_translate:
                if message.channel == au["channel"] and message.nick == au["nick"]:
                    langs.append(f"{au['src']}->{au['dst']}")

            return f"{message.nick}: {'; '.join(langs)}"

    if src == "off":
            auto_nicks.remove(message.nick)
            for au in deepcopy(auto_translate):
                if message.channel == au["channel"] and message.nick == au["nick"]:
                    auto_translate.remove(au)
            return f"{message.nick}: Cleaned all auto translations that were set"


@utils.regex_cmd_with_messsage("^!auto (.*) (.*)$", ACCEPT_PRIVATE_MESSAGES)
def auto(m, message):
    src = m.group(1).strip()
    dst = m.group(2).strip()

    if src == "off":
        debug("Turning off", dst)
        for au in deepcopy(auto_translate):
            ct = 0
            if message.channel == au["channel"] and message.nick == au["nick"] and au["dst"] == dst:
                auto_translate.remove(au)
                ct+=1
        if ct:
            return f"{message.nick}: Cleaned auto translations for {dst}"
        else:
            return f"{message.nick}: {dst} is not set for you"

    if len(dst) != 2 or len(src) != 2:
        return f"{message.sender_nick}: Please enter two ISO codes separated by spaces that have two letters. Like `!auto en es`. See here -> https://cloud.google.com/translate/docs/languages"

    if message.nick in auto_nicks and len([au for au in auto_translate if au["nick"] == message.nick]) >= MAX_AUTO_LANGS:
        return f"{message.nick}: You have you reached the maximum of {MAX_AUTO_LANGS} allowed simultaneously auto translations"

    auto_translate.append({"channel": message.channel, "nick": message.sender_nick, "src": src, "dst": dst})
    if not message.nick in auto_nicks:
        auto_nicks.append(message.nick)
    return f"{message.sender_nick}: rule added!"


@utils.regex_cmd_with_messsage("^(.*)$", ACCEPT_PRIVATE_MESSAGES)
def process_auto(m, message):
    if message.nick in auto_nicks:
        msgs = []
        for au in auto_translate:
            if message.channel == au["channel"] and message.nick == au["nick"]:
                msgs.append(translate(m, message, au["dst"], au["src"]))
        return msgs       
    

##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
