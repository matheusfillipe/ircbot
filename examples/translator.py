import concurrent.futures
import logging
import os
from copy import deepcopy

from IrcBot.bot import Color, IrcBot, Message, ReplyIntent, utils
from IrcBot.utils import debug, log

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = "irc.dot.org.es"
PORT = 6667
NICK = "translator"
PASSWORD = ""
USERNAME = "translator"
REALNAME = "simple_bot"
FREENODE_AUTH = True
SINGLE_CHAN = True
CHANNELS = ["#bots"]
ACCEPT_PRIVATE_MESSAGES = True
DBFILEPATH = NICK + ".db"
PROXIES = []

# A maximum of simultaneously auto translations for each users
MAX_AUTO_LANGS = 2
MAX_BABEL_MSG_COUNTER = 20

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
    "^@help babel.*$": [
        "@babel [dest_iso_code] You will receve translations of this chat in the specified language as a PM from me.",
        "@babel off  Disables babel mode.",
        "Notice that this mode won't last forever, you have to be active on the channel to keep babel mode active.",
    ],
    "^@help.*": [
        "@: Manually sets the target language for the current line, like so: @es Hello friends. This should translate 'Hello friends' to Spanish. The source language is detected automatically.",
        "Language iso codes: http://ix.io/2HAN, or https://cloud.google.com/translate/docs/languages",
        "@auto: automatically translate everything you send. Use '@help auto' for more info.",
        "@babel: automatically translate a chat and sends every message to you as a PM. Use '@help babel' for more info.",
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


babel_users = {}


@utils.regex_cmd_with_messsage("^@babel (.*)$", ACCEPT_PRIVATE_MESSAGES)
def babel(m, message):
    global babel_users
    dst = m.group(1).strip()
    nick = message.sender_nick
    channel = message.channel
    if channel not in babel_users:
        babel_users[channel] = {}
    if dst == "off":
        if nick in babel_users[channel]:
            del babel_users[channel][nick]
            return f"<{message.nick}> Babel mode disabled"
        else:
            return f"<{message.nick}> You do not have babel mode enabled"
    if dst not in LANGS:
        return f"<{message.nick}> {dst} is not a valid language code!"
    babel_users[channel][nick] = {"channel": channel, "dst": dst, "counter": 0}
    return f"<{message.nick}> Babel mode enabled. You will now receive translations in {dst} as private messages for this channel: {channel}"


def babel_warning(m, message, babel_nick, dst, src="en"):
    translated_msg = str(trans(m, message, dst, src))
    if translated_msg and translated_msg != "None":
        return Message(
            message=f"<{babel_nick}> {translated_msg}",
            channel=babel_nick,
            is_private=True,
        )


COLORS = [
    Color.red,
    Color.navy,
    Color.yellow,
    Color.orange,
    Color.magenta,
    Color.maroon,
    Color.blue,
    Color.green,
    Color.purple,
    Color.light_gray,
    Color.cyan,
    Color.light_green,
    Color.green,
]


def colorize(text):
    # use hash and colors to colorize text
    return Color(text, COLORS[hash(text.casefold()) % len(COLORS)]).str + Color.esc


def babel_message(m, message, babel_nick, dst, src="en"):
    translated_msg = str(trans(m, message, dst, src))
    if translated_msg and translated_msg != "None":
        return Message(
            message=f"  \x02({colorize(message.channel)}) <{colorize(message.nick)}>\x02 {translated_msg}",
            channel=babel_nick,
            is_private=True,
        )


@utils.regex_cmd_with_messsage("^(.*)$", ACCEPT_PRIVATE_MESSAGES)
async def process_auto(bot: IrcBot, m, message):
    global babel_users
    channel = message.channel

    if channel not in babel_users:
        babel_users[channel] = {}

    # reset babel counter on activity
    if (
        message.channel in babel_users or message.channel == NICK
    ) and message.nick in babel_users[message.channel]:
        babel_users[message.channel][message.nick]["counter"] = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_translations = {}
        if message.nick in auto_nicks and message.channel in auto_nicks[message.nick]:
            future_translations.update(
                {
                    executor.submit(translate, m, message, au["dst"], au["src"]): m[1]
                    for au in auto_nicks[message.nick][message.channel]
                }
            )

        # Send translations for babel users of this channel
        BABEL_WARN_THRESHOLD = 5
        for babel_nick in babel_users[message.channel]:
            babel_users[message.channel][babel_nick]["counter"] += 1
            dst = babel_users[message.channel][babel_nick]["dst"]
            if babel_users[channel][babel_nick]["counter"] >= MAX_BABEL_MSG_COUNTER:
                del babel_users[channel][babel_nick]
                future_translations.update(
                    {
                        executor.submit(
                            babel_warning,
                            f"You've been inactive for too long! You will no longer receive translations for {message.channel}",
                            message,
                            babel_nick,
                            dst,
                            "en",
                        ): f"babel_over: {m[1]}"
                    }
                )
            elif (
                babel_users[channel][babel_nick]["counter"]
                >= MAX_BABEL_MSG_COUNTER - BABEL_WARN_THRESHOLD
            ):
                future_translations.update(
                    {
                        executor.submit(
                            babel_warning,
                            f"You will stop receiving translations for {message.channel} in {BABEL_WARN_THRESHOLD} messages. Say something here or on that channel.",
                            message,
                            babel_nick,
                            dst,
                            "en",
                        ): f"babel_warning: {m[1]}"
                    }
                )

            future_translations.update(
                {
                    executor.submit(
                        babel_message,
                        m,
                        message,
                        babel_nick,
                        dst,
                    ): f"babel_warning: {m[1]}"
                }
            )

        for future in concurrent.futures.as_completed(future_translations):
            text = future_translations[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.info("%r generated an exception: %s" % (text, exc))
            else:
                await bot.send_message(data)


if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
