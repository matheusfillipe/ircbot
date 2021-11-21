#########################################################################
#  Matheus Fillipe -- 14, November of 2021                               #
#                                                                       #
#########################################################################
# A test for the Direct Client Connection file transfer                 #
#########################################################################
import logging
from pathlib import Path

import requests

from IrcBot.bot import Color, IrcBot, Message, persistentData, utils
from IrcBot.dcc import DccHelper
from IrcBot.utils import log

##################################################
# SETTINGS                                       #
##################################################

HOST = "irc.dot.org.es"
PORT = 6697
NICK = "FileServ"
CHANNELS = None
PREFIX = ""
DCC_HOST = "127.0.0.1"
STORAGE = "/home/matheus/tmp/trash/"
CMD_HELP = f"Syntax: /msg {NICK} %s"

utils.setLogging(logging.DEBUG)
utils.setPrefix(PREFIX)
utils.setSingleMatch(True)
utils.setParseOrderTopBottom(False)
utils.setHelpOnPrivate(True)
utils.setHelpMenuSeparator("\n-->  ")
utils.setHelpHeader(
    f"""
--------------------------------------------------------------
FileServ allows you to send, store, paste, and receive
files with the server storage or acting as a relay
between two users that can't use DCC directly because they
are both firewalled.

USAGE:
/msg {NICK} [command] [arguments]
e.g. : /msg FileServ help list


COMMANDS:
""".split(
        "\n"
    )
)
utils.setHelpBottom(["", "-" * 62])


def transfersh_upload(filepath):
    url = f"https://transfer.sh/{Path(filepath).name}"
    payload = open(filepath, "rb").read()
    headers = {"Content-Type": "image/jpeg"}
    response = requests.request("PUT", url, headers=headers, data=payload)
    return response.text


def get_size(folder: str) -> int:
    return sum(p.stat().st_size for p in Path(folder).rglob("*"))


def reply(msg, txt):
    return Message(msg.nick, message=txt)


@utils.arg_command("list", "List files you updloaded or received", CMD_HELP % "list")
def listdir(args, msg: Message):
    return reply(msg, "Nothing yet")


@utils.arg_command("status", "Check if nick is identified", CMD_HELP % "list")
async def status(bot: IrcBot, args, msg: Message):
    return reply(msg, f"{args[1]} -> {await is_identified(bot, args[1])}")


def progress_curve(filesize):
    notify_each_b = min(10, max(1, 10 - 10 * filesize // 1024 ** 3))
    return min([1, 2, 5, 10], key=lambda x: abs(x - notify_each_b))


async def is_identified(bot: IrcBot, nick):
    nickserv = "NickServ"
    await bot.send_message(f"status {nick}", nickserv)
    # We need filter because multiple notices from nickserv can come at the same time
    # if multiple requests are being made to this function all together
    msg = await bot.wait_for(
        "notice", nickserv, timeout=5, cache_ttl=15, filter_func=lambda m: nick in m["text"]
    )
    return msg.get("text").strip() == f"{nick} 3 {nick}" if msg else False


@utils.arg_command("test")
async def test(bot: IrcBot, args, msg):
    nick = msg.nick
    await bot.send_message(f"{nick}: say yes/no", nick)
    while True:
        resp = await bot.wait_for("privmsg", nick, timeout=10)
        if resp:
            if resp.get('text').strip() in ["yes", "no"]:
                break
            else:
                await bot.send_message(f"Invalid response! {nick}: say yes/no", nick)
        else:
            await bot.send_message("Response timeout!", nick)
            return
    await bot.send_message(f"{nick}: you said `{resp['text']}`", nick)


@utils.custom_handler("dccsend")
async def on_dcc_send(bot: IrcBot, **m):
    sendfile = "/media/matheus/Elements/OS's/debian-sid-hurd-i386-CD-1.iso"

    notify_each_b = progress_curve(m["size"])

    async def progress_handler(p, message):
        percentile = int(p * 100)
        if percentile % notify_each_b == 0:
            await bot.send_message(message % percentile, m["nick"])

    path = f"/home/matheus/tmp/test_{m['filename']}"
    await bot.dcc_get(
        path,
        m,
        progress_callback=lambda _, p: progress_handler(
            p, f"UPLOAD {Path(m['filename']).name} %s%%"
        ),
    )
    await bot.send_message(
        Message(
            m["nick"], message=f"{m['filename']} has been received!", is_private=True
        )
    )
    notify_each_b = progress_curve(Path(sendfile).stat().st_size)
    await bot.dcc_send(
        m["nick"],
        sendfile,
        progress_callback=lambda _, p: progress_handler(
            p, f"DOWNLOAD {Path(sendfile).name} %s%%"
        ),
    )


@utils.regex_cmd_with_messsage("\S+")
def not_found(m, msg):
    log(f"{msg.text=}")
    return reply(
        msg, f'Unknown command or invalid syntax. Try "/msg {NICK} help" for help'
    )


@utils.custom_handler("dccreject")
def on_dcc_reject(**m):
    log(f"Rejected!!! {m=}")


async def on_run(bot: IrcBot):
    pass


if __name__ == "__main__":
    # print(transfersh_upload("/home/matheus/tmp/another.jpg"))
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, dcc_host=DCC_HOST, use_ssl=True)
    bot.runWithCallback(on_run)
