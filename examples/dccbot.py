#########################################################################
#  Matheus Fillipe -- 14, November of 2021                               #
#                                                                       #
#########################################################################
# A test for the Direct Client Connection file transfer                 #
#########################################################################

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum, auto
from functools import wraps
from pathlib import Path

import requests
from cachetools import TTLCache

from IrcBot.bot import Color, IrcBot, Message, persistentData, utils
from IrcBot.utils import debug, log

##################################################
# SETTINGS                                       #
##################################################

ADMINS = ["mattf"]
HOST = "irc.dot.org.es"
PORT = 6697
NICK = "FileServ"
CHANNELS = None
PREFIX = ""
DCC_HOST = "127.0.0.1"
STORAGE = "/home/matheus/tmp/trash/"
CMD_HELP = f"Syntax: /msg {NICK} %s"
TIMEOUT = 120

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


# Utils/Functions/Lib


class Folder:
    def __init__(self, nick):
        self.folder = Path(f"{STORAGE}/{nick}/")
        self.create_dir_if_not_exists()

    def create_dir_if_not_exists(self):
        self.folder.mkdir(exist_ok=True)

    def size(self) -> int:
        return sum(p.stat().st_size for p in self.folder.rglob("*"))

    def list(self) -> iter:
        return sorted(self.folder.iterdir(), key=os.path.getmtime)

    def exists(self, filename):
        return Path(str(self.folder) + f"/{filename}").is_file()


class ConfigOptions(Enum):
    NICK = auto()
    DISPLAY_PROGRESS = auto()
    QUOTA = auto()


table_columns = [f.name for f in ConfigOptions]
configs = persistentData(NICK + ".db", "users", table_columns)


@dataclass
class Config:
    nick: str
    display_progress: bool = True
    quota: int = 100  # MB

    def asdict(self) -> dict:
        return asdict(self)

    def save(self):
        for user in configs.data:
            if self.nick == user[ConfigOptions.NICK.name]:
                configs.update(user["id"], self.asdict())
                return
        log(f"Creating new config for user: {self.nick}")
        debug(f"{self.asdict()=}")
        configs.push(self.asdict())

    def folder(self) -> Folder:
        return Folder(self.nick)

    @classmethod
    def get_existing(cls, nick: str) -> Config:
        nick = nick.strip()
        for user in configs.data:
            if nick == user[ConfigOptions.NICK.name]:
                return Config.from_dict(user)

    @classmethod
    def from_dict(cls, d: dict) -> Config:
        return cls(**{k: v for k, v in d.items() if k in table_columns})

    @classmethod
    def get(cls, nick: str) -> Config:
        for user in configs.data:
            if nick == user[ConfigOptions.NICK.name]:
                return Config.from_dict(user)
        config = cls(nick)
        config.save()
        return config


def transfersh_upload(filepath):
    url = f"https://transfer.sh/{Path(filepath).name}"
    payload = open(filepath, "rb").read()
    headers = {"Content-Type": "image/jpeg"}
    response = requests.request("PUT", url, headers=headers, data=payload)
    return response.text


def reply(msg, txt):
    return Message(msg.nick, message=txt)


def progress_curve(filesize):
    notify_each_b = min(10, max(1, 10 - 10 * filesize // 1024 ** 3))
    return min([1, 2, 5, 10], key=lambda x: abs(x - notify_each_b))


def red(txt: str) -> str:
    return Color(txt, fg=Color.red).str + Color("", fg=Color.esc).str


nick_cache = {}


def is_admin(msg):
    if msg.nick in ADMINS:
        return True


async def is_identified(bot: IrcBot, nick: str) -> bool:
    global nick_cache
    nickserv = "NickServ"
    if nick in nick_cache and "status" in nick_cache[nick]:
        msg = nick_cache[nick]["status"]
    else:
        await bot.send_message(f"status {nick}", nickserv)
        # We need filter because multiple notices from nickserv can come at the same time
        # if multiple requests are being made to this function all together
        msg = await bot.wait_for(
            "notice",
            nickserv,
            timeout=5,
            cache_ttl=15,
            filter_func=lambda m: nick in m["text"],
        )
        nick_cache[nick] = TTLCache(128, 60)
        nick_cache[nick]["status"] = msg
    return msg.get("text").strip() == f"{nick} 3 {nick}" if msg else False


async def ask(
    bot: IrcBot,
    nick: str,
    question: str,
    expected_input=None,
    repeat_question=None,
    loop: bool = True,
    timeout_message: str = "Response timeout!",
):
    await bot.send_message(question, nick)
    resp = await bot.wait_for("privmsg", nick, timeout=10)
    while loop:
        if resp:
            if expected_input is None or resp.get("text").strip() in expected_input:
                break
            await bot.send_message(
                repeat_question if repeat_question else question, nick
            )
        else:
            await bot.send_message(timeout_message, nick)
        resp = await bot.wait_for("privmsg", nick, timeout=TIMEOUT)
    return resp.get("text").strip() if resp else None


def requires_ident():
    def wrapper(func):
        @wraps(func)
        async def wrapped(*a, **bb):
            if not await is_identified(a[0], a[2].nick):
                return "You cannot use this bot before you register your nick"
            return await func(*a, **bb)

        return wrapped

    return wrapper


# COMMANDS


@utils.arg_command("info", "Shows your personal preferences", CMD_HELP % "info")
@requires_ident()
async def info(bot: IrcBot, args, msg: Message):
    if is_admin(msg) and args[1]:
        if Config.get_existing(args[1]):
            msg.nick = args[1]
        else:
            return f"User not found: {args[1]}"
    return reply(
        msg,
        [
            f"{k}: {v} {'MB' if ConfigOptions.QUOTA.name.lower() == k else ''}"
            for k, v in Config.get(msg.nick).asdict().items()
        ]
        + [f"usage: {Folder(msg.nick).size()} MB"],
    )


@utils.arg_command(
    "quota", "ADMIN: Sets quota for user", CMD_HELP % "quota [nick] [value]"
)
def quota(args, msg: Message):
    if not is_admin(msg):
        return "You cannot use this command"
    if not args[1]:
        return "You must enter with a nick"
    config = Config.get_existing(args[1])
    if not config:
        return f"There is no user with that nickname: {args[1]}"
    if not args[2] or not args[2].isdigit():
        return "You must enter with a valid quota value"
    config.quota = int(args[2])
    config.save()
    return f"set quota: {config.quota} MB for {config.nick}"


@utils.arg_command("list", "List files you uploaded or received", CMD_HELP % "list")
def listdir(args, msg: Message):
    files = [f"{p.name} -- {p.stat().st_size}" for p in Folder(msg.nick).list()]
    if files:
        return reply(msg, files)
    return reply(msg, "You don't have any file yet")


@utils.arg_command("status", "Check if nick is identified", CMD_HELP % "list")
async def status(bot: IrcBot, args, msg: Message):
    return reply(msg, f"{args[1]} -> {await is_identified(bot, args[1])}")


@utils.arg_command(
    "delete", "Removes a file from your folder", CMD_HELP % "delete [filename]"
)
async def delete(bot: IrcBot, args, msg):
    pass


@utils.arg_command(
    "send", "Sends a file of your folder to some user", CMD_HELP % "send [filename]"
)
async def send(bot: IrcBot, args, msg):
    pass


@utils.arg_command(
    "prog",
    "Change the behaviour of the file upload/download progress messages",
    CMD_HELP % "noprog",
)
async def noprog(bot: IrcBot, args, msg):
    pass


@utils.arg_command("imgur", "Uploads image to imgur", CMD_HELP % "imgur [filename]")
async def imgur(bot: IrcBot, args, msg):
    pass


@utils.arg_command(
    "paste", "Uploads files to transfer.sh", CMD_HELP % "paste [filename]"
)
async def paste(bot: IrcBot, args, msg):
    pass


@utils.arg_command("test")
async def test(bot: IrcBot, args, msg):
    nick = msg.nick
    resp = await ask(
        bot,
        msg.nick,
        f"{nick}: say yes/no",
        ["yes", "no"],
        repeat_question="You must reply with yes or no",
    )
    return f"Your answer is: '{resp}'"


@utils.custom_handler("dccsend")
async def on_dcc_send(bot: IrcBot, **m):

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

    sendfile = "/media/matheus/Elements/OS's/debian-sid-hurd-i386-CD-1.iso"
    notify_each_b = progress_curve(Path(sendfile).stat().st_size)
    await bot.dcc_send(
        m["nick"],
        sendfile,
        progress_callback=lambda _, p: progress_handler(
            p, f"DOWNLOAD {Path(sendfile).name} %s%%"
        ),
    )


@utils.regex_cmd_with_messsage(r"\S+")
def not_found(m, msg):
    log(f"{msg.text=}")
    return reply(
        msg,
        f'{red("Unknown command or invalid syntax")}. Try "/msg {NICK} help" for help',
    )


@utils.custom_handler("dccreject")
def on_dcc_reject(**m):
    log(f"Rejected!!! {m=}")


async def on_run(bot: IrcBot):
    pass


if __name__ == "__main__":
    # print(transfersh_upload("/home/matheus/tmp/another.jpg"))
    bot = IrcBot(
        HOST, PORT, NICK, CHANNELS, dcc_host=DCC_HOST, use_ssl=True, tables=[configs]
    )
    bot.runWithCallback(on_run)
