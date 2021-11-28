import logging
import os
from copy import deepcopy

from IrcBot.bot import IrcBot, Message, ReplyIntent, utils
from IrcBot.utils import debug, log

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = "irc.server.com"
PORT = 6665
NICK = "translator"
PASSWORD = ""
USERNAME = "translator"
REALNAME = "simple_bot"
FREENODE_AUTH = True
SINGLE_CHAN = True
CHANNELS = ["#english", "#spanish"]  # , "#lobby",]
ACCEPT_PRIVATE_MESSAGES = True
DBFILEPATH = NICK + ".db"
PROXIES = []

# A maximum of simultaneously auto translations for each users
MAX_AUTO_LANGS = 2

INFO_CMDS = {
    r"^@linux.*$": "The OS this bot runs on",
    "^@rules.*$": [
        f"1. You can only have {MAX_AUTO_LANGS} auto translations active simultaneously",
        "2. Do not use this bot to spam",
    ],
    "^@help auto.*$": [
        "@auto [src_iso_code] [dest_iso_code] Sets the automatic translation from the source language to the target language as specified in the command.",
        "@auto show Displays the current source and target language or languages in place in the channel.",
        "@auto off [dest_iso_code] Disables automatic translation to the specified target language.",
        "@auto off Clears all rules for automatic translations in the channel.",
    ],
    "^@help.*": [
        "@: Manually sets the target language for the current line, like so: @es Hello friends. This should translate 'Hello friends' to Spanish. The source language is detected automatically.",
        "Language iso codes: http://ix.io/2HAN, or https://cloud.google.com/translate/docs/languages",
        "@auto: automatically translate everything you send. Use '@help auto' for more info.",
    ],
    #    r"^(.*) linux ": "Do you mean the best OS?",
    #    r"^(.*) vim ": "Do you mean the best Text editor???",
}


# Useful if connecting to freenode from a blacklisted ip that will require SASL
USE_SASL = False

# Uncoment to use password from environment PW variable, like if you run:
# `PW=mypw python bot.py`

LANGS = [l.strip() for l in open("google_iso_lang_codes.txt").readlines()]

# PASSWORD=os.environ['PW']

utils.setParseOrderTopBottom()
##################################################
# BOT COMMANDS DEFINITIONS                       #
##################################################

from google_trans_new import google_trans_new, google_translator

auto_nicks = {}

for r in INFO_CMDS:

    @utils.regex_cmd(r, ACCEPT_PRIVATE_MESSAGES)
    def info_cmd(m, regexp=r):
        return INFO_CMDS[regexp]


def trans(m, message, dst, src="auto"):
    if type(m) != str:
        m = m.group(1)
    logging.info("Translating: " + m)
    proxy_index = None
    while proxy_index is None or proxy_index < len(PROXIES):
        translator = google_translator(
            proxies={"http": PROXIES[proxy_index]} if proxy_index is not None else None
        )
        try:
            if translator.detect(m)[0] == dst:
                return
            if src != "auto" and translator.detect(m)[0] != src:
                return
            msg = translator.translate(m, lang_tgt=dst, lang_src=src)
            return msg
        except google_trans_new.google_new_transError as e:
            import sys
            import traceback

            print(
                traceback.format_exception(type(e), e, e.__traceback__),
                file=sys.stderr,
                flush=True,
            )
            print("-" * 80)
            proxy_index = 0 if proxy_index is None else proxy_index
            proxy_index += 1
            print(f"Failed... Trying proxy: {PROXIES[proxy_index]}")


def translate(m, message, dst, src="auto"):
    translated_msg = str(trans(m, message, dst, src))
    if translated_msg and translated_msg != "None":
        return f"  <{message.sender_nick} ({dst.upper()})> {translated_msg}"


@utils.regex_cmd_with_messsage("^@(\S?\S?)\s(.*)$", ACCEPT_PRIVATE_MESSAGES)
def translate_cmd(m, message):
    text = m.group(2)
    lang = m.group(1)
    if lang not in LANGS:
        return f"<{message.nick}> {lang} is not a valid langauge code!"
    if len(lang) != 2:
        lang = "en"
    return translate(text, message, lang)


@utils.regex_cmd_with_messsage("^@auto (.*)$", ACCEPT_PRIVATE_MESSAGES)
def auto_conf(m, message):
    src = m.group(1).strip()
    if src == "show":
        if message.nick in auto_nicks and message.channel in auto_nicks[message.nick]:
            langs = []
            for au in auto_nicks[message.nick][message.channel]:
                langs.append(f"{au['src']}->{au['dst']}")
            return f"<{message.nick}> {'; '.join(langs)}"
        else:
            return f"<{message.nick}> You don't have any auto rule set on this channel."

    if src == "off":
        if message.nick in auto_nicks and message.channel in auto_nicks[message.nick]:
            for au in deepcopy(auto_nicks[message.nick][message.channel]):
                auto_nicks[message.nick][message.channel].remove(au)
            return f"<{message.nick}> all of yours auto translate rules were cleaned for this channel!"
        else:
            return f"<{message.nick}> You don't have any auto rule set on this channel."


@utils.regex_cmd_with_messsage("^@auto (.*) (.*)$", ACCEPT_PRIVATE_MESSAGES)
def auto(m, message):
    src = m.group(1).strip()
    dst = m.group(2).strip()

    if src == "off":
        if message.nick in auto_nicks and message.channel in auto_nicks[message.nick]:
            for au in deepcopy(auto_nicks[message.nick][message.channel]):
                ct = 0
                if au["dst"] == dst:
                    auto_nicks[message.nick][message.channel].remove(au)
                    ct += 1
            if ct:
                return f"<{message.nick}> Cleaned auto translations for {dst}"
            else:
                return f"<{message.nick}> {dst} is not set for you"
        else:
            return f"<{message.nick}> You don't have any auto rule set on this channel."

    if len(dst) != 2 or len(src) != 2:
        return f"<{message.nick}> Please enter two ISO codes separated by spaces that have two letters. Like `@auto en es`. See here -> https://cloud.google.com/translate/docs/languages"

    if message.nick not in auto_nicks:
        auto_nicks[message.nick] = {}
    if message.channel not in auto_nicks[message.nick]:
        auto_nicks[message.nick][message.channel] = []
    if len(auto_nicks[message.nick][message.channel]) >= MAX_AUTO_LANGS:
        return f"<{message.nick}> You have you reached the maximum of {MAX_AUTO_LANGS} allowed simultaneously auto translations"

    if src not in LANGS:
        return f"<{message.nick}> {src} is not a valid language code!"
    if dst not in LANGS:
        return f"<{message.nick}> {dst} is not a valid language code!"
    au = {
        "channel": message.channel,
        "nick": message.sender_nick,
        "src": src,
        "dst": dst,
    }
    if au in auto_nicks[message.nick][message.channel]:
        return f"<{message.nick}> Skipping existing rule!"
    auto_nicks[message.nick][message.channel].append(au)
    return f"<{message.nick}> rule added!"


@utils.regex_cmd_with_messsage("^(.*)$", ACCEPT_PRIVATE_MESSAGES)
def process_auto(m, message):
    if message.nick in auto_nicks and message.channel in auto_nicks[message.nick]:
        msgs = []
        for au in auto_nicks[message.nick][message.channel]:
            print(f"TRANSLATING: {au=}")
            msgs.append(translate(m, message, au["dst"], au["src"]))
        return msgs


if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
