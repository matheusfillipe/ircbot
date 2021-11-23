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
from time import time
from typing import Tuple

import requests
from cachetools import TTLCache

from IrcBot.bot import Color, IrcBot, Message, persistentData, utils
from IrcBot.dcc import DccServer
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
IMGUR_CLIENT_ID = ""

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

TO SEND FILES:
/dcc send FileServ /path/to/file
/dcc send -passive FileServ /path/to/file

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

    def exists(self, filename: str) -> bool:
        return Path(str(self.folder) + f"/{filename}").is_file()

    def path(self, filename: str) -> Path:
        return Path(str(self.folder) + f"/{filename}")

    def download_path(self, filename: str) -> str:
        if not self.exists(filename):
            return str(self.folder) + f"/{filename}"
        return self.path("_" + filename)


class ConfigOptions(Enum):
    nick = auto()
    display_progress = auto()
    quota = auto()


table_columns = [f.name for f in ConfigOptions]
configs = persistentData(NICK + ".db", "users", table_columns)


@dataclass
class Config:
    nick: str
    display_progress: bool = True
    quota: int = 100  # MB

    def asdict(self) -> dict:
        return asdict(self)

    @classmethod
    def _get_data_by_nick(cls, nick):
        return configs.db.getByKeyWithId(ConfigOptions.nick.name, nick)

    def save(self):
        if user := self._get_data_by_nick(self.nick):
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
        if user := cls._get_data_by_nick(nick):
            return Config.from_dict(user)

    @classmethod
    def from_dict(cls, d: dict) -> Config:
        return cls(**{k: v for k, v in d.items() if k in table_columns})

    @classmethod
    def get(cls, nick: str) -> Config:
        if user := cls._get_data_by_nick(nick):
            return Config.from_dict(user)
        config = cls(nick)
        config.save()
        return config


def transfersh_upload(filepath) -> str:
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
            if (
                expected_input is None
                or resp.get("text").strip().casefold() in expected_input
            ):
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


async def send_file(bot: IrcBot, nick: str, file: Path):
    notify_each_b = progress_curve(file.stat().st_size)
    config = Config.get(nick)

    async def progress_handler(p, message):
        if not config.display_progress:
            return
        percentile = int(p * 100)
        if percentile % notify_each_b == 0:
            await bot.send_message(message % percentile, nick)

    await bot.send_message(f"Type '/dcc get FileServ {file.name}' to download it", nick)
    await bot.dcc_send(
        nick,
        str(file),
        progress_callback=lambda _, p: progress_handler(
            p, f"DOWNLOAD {file.name} %s%%"
        ),
    )
    await bot.send_message("Submission of {file.name} was completed", nick)


def check_nick_has_file(nick: str, filename: str) -> Tuple[str, Path]:
    if not filename:
        return "You must pass a filename. Check 'list'", None
    folder = Folder(nick)
    if not folder.exists(filename):
        return f"This file doesn't exist ({filename}). Check 'list'", None
    return None, folder.path(filename)


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
            f"{k}: {v} {'MB' if ConfigOptions.quota.name == k else ''}"
            for k, v in Config.get(msg.nick).asdict().items()
        ]
        + [f"usage: {round(Folder(msg.nick).size() / 1048576, 2)} MB"],
    )


@utils.arg_command(
    "quota", "ADMIN: Sets quota for user", CMD_HELP % "quota [nick] [value]"
)
@requires_ident()
async def quota(bot: IrcBot, args, msg: Message):
    if not is_admin(msg):
        return "You cannot use this command"
    if not args[1]:
        return "You must pass in a nick"
    config = Config.get_existing(args[1])
    if not config:
        return f"There is no user with that nickname: {args[1]}"
    if not args[2] or not args[2].isdigit():
        return "You must pass in a valid quota value"
    config.quota = int(args[2])
    config.save()
    return f"set quota: {config.quota} MB for {config.nick}"


@utils.arg_command("list", "List files you uploaded or received", CMD_HELP % "list")
@requires_ident()
async def listdir(bot: IrcBot, args, msg: Message):
    files = [
        f"{p.name} -- {round(p.stat().st_size / 1048576, 2)} MB"
        for p in Folder(msg.nick).list()
    ]
    if files:
        return reply(msg, files)
    return reply(msg, "You don't have any file yet")


@utils.arg_command(
    "move",
    "Renames a file from your folder",
    CMD_HELP % "move [filename] [new_filename]",
)
@requires_ident()
async def rename(bot: IrcBot, args, msg):
    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    if not args[2]:
        return "You must pass in a new filename for this file"

    folder = Folder(msg.nick)
    if folder.exists(args[2]):
        resp = await ask(
            bot,
            msg.nick,
            f"The destiny file {args[2]} already exists, do you want to replace it with {args[1]} (y/n)?",
            expected_input=["y", "n"],
            repeat_question="Please respond with 'y' or 'n'",
        )
        if resp == "n":
            return "Aborting"

    file.rename(folder.path(args[2]))
    return f"Moved {args[1]} to {args[2]}"


@utils.arg_command(
    "delete", "Removes a file from your folder", CMD_HELP % "delete [filename]"
)
@requires_ident()
async def delete(bot: IrcBot, args, msg):
    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    resp = await ask(
        bot,
        msg.nick,
        f"Are you sure you want to remove {file.name} (y/n)?",
        expected_input=["y", "n"],
        repeat_question="Please type 'y' or 'n'",
    )
    if resp == "n":
        return "Aborting"
    file.unlink()
    return f"{file} removed!"


@utils.arg_command(
    "send",
    "Sends a file of your folder to some user",
    CMD_HELP % "send [filename] [nick]",
)
@requires_ident()
async def send(bot: IrcBot, args, msg):
    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    if not args[2]:
        return "Please pass in a nick to send the file to"

    # Check if nick is on the network and measure ping
    nick = args[2]
    now = time()
    await bot.send_raw(f"PING {nick}")
    notice = await bot.wait_for(
        "pong",
        nick,
        timeout=5,
        filter_func=lambda m: nick.strip().casefold() == m["nick"].strip().casefold(),
    )
    if not notice:
        return f"The nick {nick} is not available or timed out"

    ping = round(- now + time(), 4)
    await bot.send_message(f"Sending {file.name} to {nick}. Ping: {ping}s", msg.nick)
    await send_file(bot, nick, file)


@utils.arg_command(
    "get", "Receives a file from your folder", CMD_HELP % "get [filename]"
)
@requires_ident()
async def get(bot: IrcBot, args, msg):
    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    await send_file(bot, msg.nick, file)


@utils.arg_command(
    "prog",
    "Change the behaviour of the file upload/download progress messages",
    CMD_HELP % "noprog",
)
@requires_ident()
async def noprog(bot: IrcBot, args, msg):
    config = Config.get(msg.nick)
    nick = msg.nick
    resp = await ask(
        bot,
        msg.nick,
        f"{nick}: Respond with 'd' to disable or 'e' to enable to progress messages",
        ["d", "e"],
        repeat_question="You must reply with either e or d",
    )
    config.display_progress = resp == "e"
    config.save()
    return f"Set progress display to: '{config.display_progress}'"


@utils.arg_command("imgur", "Uploads image to imgur", CMD_HELP % "imgur [filename]")
@requires_ident()
async def imgur(bot: IrcBot, args, msg):
    def error_out():
        if msg.nick in ADMINS:
            return "You need the pyimgur module to use this: pip install pyimgur"
        return "Currently disabled"

    if not IMGUR_CLIENT_ID:
        error_out()

    try:
        import pyimgur
    except ModuleNotFoundError:
        error_out()

    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    size = file.stat().st_size
    img_exts = ["JPEG", "PNG", "GIF", "APNG", "TIFF"]
    anim_exts = ["MP4", "MPEG", "AVI", "WEBM"]
    ext = file.suffix.replace(".", "").upper()

    # Validation
    if ext not in img_exts + anim_exts:
        return (
            f"{file.name} does not have a accepted extension for imgur ({file.suffix})"
        )
    if ext in img_exts and size > 20971520:
        return "Your file is too big for imgur (image > 20MB)"
    if ext in anim_exts and size > 209715200:
        return "Your file is too big for imgur (animation > 200MB)"

    filename = str(file)
    im = pyimgur.Imgur(IMGUR_CLIENT_ID)
    uploaded_image = im.upload_image(filename, title="FileServ upload")
    return uploaded_image.link


@utils.arg_command(
    "paste", "Uploads files to transfer.sh", CMD_HELP % "paste [filename]"
)
@requires_ident()
async def paste(bot: IrcBot, args, msg):
    error, file = check_nick_has_file(msg.nick, args[1])
    if error:
        return error
    return transfersh_upload(str(file))


@utils.regex_cmd_with_messsage(r"\S+")
@requires_ident()
async def not_found(bot: IrcBot, m, msg):
    log(f"{msg.text=}")
    return reply(
        msg,
        f'{red("Unknown command or invalid syntax")}. Try "/msg {NICK} help" for help',
    )


@utils.custom_handler("dccsend")
async def on_dcc_send(bot: IrcBot, **m):
    nick = m["nick"]
    if not await is_identified(bot, nick):
        await bot.dcc_reject(DccServer.SEND, nick, m["filename"])
        await bot.send_message(
            "You cannot use this bot before you register your nick", nick
        )
        return

    notify_each_b = progress_curve(m["size"])

    config = Config.get(nick)

    async def progress_handler(p, message):
        if not config.display_progress:
            return
        percentile = int(p * 100)
        if percentile % notify_each_b == 0:
            await bot.send_message(message % percentile, m["nick"])

    folder = Folder(nick)
    if folder.size() + int(m["size"]) > int(Config.get(nick).quota) * 1048576:
        await bot.send_message(
            Message(
                m["nick"],
                message="Your quota has exceeded! Type 'info' to check, 'list' to see your files and 'delete [filename]' to free some space",
                is_private=True,
            )
        )
        return
    path = folder.download_path(m["filename"])
    await bot.dcc_get(
        str(path),
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


@utils.custom_handler("dccreject")
def on_dcc_reject(**m):
    log(f"Rejected!!! {m=}")


async def on_run(bot: IrcBot):
    log("STARTED!")


if __name__ == "__main__":
    bot = IrcBot(
        HOST, PORT, NICK, CHANNELS, dcc_host=DCC_HOST, use_ssl=True, tables=[configs]
    )
    bot.runWithCallback(on_run)
