#########################################################################
#  Matheus Fillipe -- 22, April of 2021                                 #
#                                                                       #
#########################################################################
#  Description: A simple chess game that allows players in different    #
#  channels to have multiple games at the same time and also provides   #
#  a cpu player using stockfish.                                        #
#                                                                       #
#########################################################################

import json
import logging
import re
from copy import copy
from datetime import datetime

import chess
import chess.engine

from IrcBot.bot import Color, IrcBot, Message, persistentData, utils
from IrcBot.utils import debug, log

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = "irc.dot.org.es"
PORT = 6667
NICK = "chessbot"
PASSWORD = ""
CHANNELS = ["#bots"]  # , "#lobby",]
PREFIX = ";"
STOCKFISH = "/usr/bin/stockfish"
EXPIRE_INVITE_IN = 60  # secods
DEFAULT_PREF = {"fg":[Color.white, Color.black], "bg":[Color.maroon, Color.gray], "label":"   A  B  C  D  E  F  G  H   "}

############################################################

utils.setLogging(LEVEL, LOGFILE)
utils.setPrefix(PREFIX)


### Data permanency
db_columns = ["nick", "checkmates", "stalemates", "draws", "games", "losses", "prefs"]
db_handler = persistentData(NICK + ".db", "users", db_columns)

def get_data(nick):
    for user in db_handler.data:
        if nick == user[db_columns[0]]:
            return user


def create_data(nick):
    default_data = {
        "nick": nick,
        "checkmates": 0,
        "stalemates": 0,
        "draws": 0,
        "games": 0,
        "losses": 0,
        "prefs": json.dumps(DEFAULT_PREF)
    }
    db_handler.push(default_data)
    return default_data

def increment_data(nick, column):
    data = get_data(nick)
    if data is None:
        data = {
            "nick": nick,
            "checkmates": 0,
            "stalemates": 0,
            "draws": 0,
            "games": 0,
            "losses": 0,
            "prefs": json.dumps(DEFAULT_PREF)
        }
        data.update({column: 1})
        db_handler.push(data)
        log("Creating player data")
    else:
        data.update({column: data[column] + 1})
        db_handler.update(data['id'], data)
        log("incrementing player data")

def update_data(nick, data):
    for user in db_handler.data:
        if nick == user[db_columns[0]]:
            user.update(data)
            db_handler.update(user['id'], user)
            return True

####################################################################################
# Player logics

remap = {
    "R": "♜",
    "N": "♞",
    "B": "♝",
    "Q": "♛",
    "K": "♚",
    "P": "♟︎",
    ".": "♟︎",
}

engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")


def cpuPlay(board: chess.Board):
    global engine
    result = engine.play(board, chess.engine.Limit(time=0.1))
    board.push(result.move)
    return result.move


class Game:
    BG_CLASSIC = [Color.maroon, Color.gray]
    FG_CLASSIC = [Color.white, Color.black]
    BG_MODERN = [Color.purple, Color.red]
    FG_MODERN = [Color.white, Color.yellow]

    LABEL = [
        "   A  B  C  D  E  F  G  H   ",
        "     A   B   C   D   E   F   G   H  ",
    ]

    PREF = DEFAULT_PREF

    def __init__(self, p1, p2):
        self.board = chess.Board()
        self.player = False
        self.nicks = [p1, p2]
        self.p1 = p1
        self.p2 = p2
        self.prefs = {
            self.p1: Game.PREF,
            self.p2: Game.PREF,
        }
        self.history = []

    def loadprefs(self):
        pref1 = get_data(self.p1)
        pref2 = get_data(self.p2)
        pref1 = pref1['prefs'] if pref1 else None
        pref2 = pref2['prefs'] if pref2 else None
        self.prefs = {
            self.p1: json.loads(pref1) if pref1 else Game.PREF,
            self.p2: json.loads(pref2) if pref2 else Game.PREF,
        }

    def who(self):
        return self.nicks[self.player]

    def pop(self):
        self.board.pop()
        self.player = not self.player
        self.history.pop()

    def move(self, uic):
        self.board.push_uci(uic)
        self.player = not self.player
        self.history.append(uic)

    def utf8_board(self, nick):
        self.loadprefs()
        R = []
        bgi = 1
        row = 8
        label = self.prefs[nick]["label"]
        BG = self.prefs[nick]["bg"]
        FG = self.prefs[nick]["fg"]
        R.append(label)
        for l in str(self.board).split("\n"):
            colors = []
            for c in l:
                if not c.upper() in remap:
                    continue
                if c.upper() == c:
                    piece = Color(
                        f" {remap[c.upper()]} ",
                        bg=BG[bgi],
                        fg=FG[0] if c != "." else BG[bgi],
                    )
                else:
                    piece = Color(
                        f" {remap[c.upper()]} ",
                        bg=BG[bgi],
                        fg=FG[1] if c != "." else BG[bgi],
                    )
                colors.append(piece)
                bgi = not bgi
            bgi = not bgi
            colors[-1].str = colors[-1].str[:-1]
            R.append(
                str(row) + " " + "".join([c.str for c in colors]) + " \003 " + str(row)
            )
            row -= 1
        R.append(label)
        return R


def set_prefs(nick, **kwargs):
    """set_prefs.

    :param nick:
    :param kwargs: fg, bg, label
    """
    for user in db_handler.data:
        if nick == user[db_columns[0]]:
            data = json.loads(user.get('prefs'))
            data.update(kwargs)
            user.update({"prefs": json.dumps(data)})
            db_handler.update(user['id'], user)
            return True
    default = Game.PREF
    default.update(kwargs)
    db_handler.push(
        {
            "nick": nick,
            "checkmates": 0,
            "stalemates": 0,
            "draws": 0,
            "games": 0,
            "losses": 0,
            "prefs": json.dumps(default)
        }
    )
    return False


class BotState:
    def __init__(self):
        self.games = {}   # {nick: {channel: {selected: index, games: [game1, game2]},..}, ...}
        self.invites = {}  # {nick: {channel: {nick1: time,  nick2: time },channel2 ...}}

    def has_invited(self, nick, against_nick, channel):
        if against_nick in self.invites and channel in self.invites[against_nick]:
            if nick in self.invites[against_nick][channel]:
                return True
        return None

    def invite(self, nick, against_nick, channel):
        if self.has_invited(nick, against_nick, channel):
            return None
        if not against_nick in self.invites:
            self.invites[against_nick] = {}
        if not channel in self.invites[against_nick]:
            self.invites[against_nick][channel] = {}
        self.invites[against_nick][channel][nick] = datetime.now().timestamp()
        return True

    def remove_invite(self, nick, against_nick, channel):
        if self.has_invited(nick, against_nick, channel):
            self.invites[against_nick][channel].pop(nick)
            return True
        return None

    def _add_game(self, nick, against_nick, channel, new_game):
        if not nick in self.games:
            self.games[nick] = {}
        if not channel in self.games[nick]:
            self.games[nick][channel] = {"selected": 0, "games": []}
        self.games[nick][channel]["games"].append(new_game)
        self.games[nick][channel][
            "selected"
        ] = -1  # len(self.games[nick][channel]['games']) - 1

    def add_game(self, nick, against_nick, channel):
        if against_nick != NICK and not self.remove_invite(nick, against_nick, channel):
            return None
        new_game = Game(nick, against_nick)
        self._add_game(nick, against_nick, channel, new_game)
        self._add_game(against_nick, nick, channel, new_game)
        return new_game

    def has_any_game(self, nick, channel):
        return nick in self.games and channel in self.games[nick]

    def has_game_with(self, nick, against_nick, channel):
        if not self.has_any_game(nick, channel):
            return None
        for i, game in enumerate(self.games[nick][channel]["games"]):
            if nick in [game.p1, game.p2] and against_nick in [game.p1, game.p2]:
                return i
        return None

    def get_games(self, nick, channel=None):
        if channel and self.has_any_game(nick, channel):
            return self.games[nick][channel]["games"]
        if not channel and nick in self.games:
            games = []
            for chan in self.games[nick]:
                games += self.games[nick][chan]["games"]
            return games
        return None

    def get_selected_game(self, nick, channel):
        if not self.has_any_game(nick, channel):
            return None
        games = self.games[nick][channel]
        return games["games"][games["selected"]]

    def select_game(self, nick, against_nick, channel):
        games = self.get_games(nick, channel)
        if games:
            for game in games:
                if game.p2 == against_nick:
                    self.games[nick][channel]["selected"] = self.games[nick][channel][
                        "games"
                    ].index(game)
                    return game
        return None

    def end_game(self, nick, against_nick, channel):
        game: Game = self.has_game_with(nick, against_nick, channel)
        if game is None:
            return None
        if self.games[nick][channel]["selected"] == game:
            self.games[nick][channel]["selected"] = -1
        del self.games[nick][channel]["games"][game]
        self.end_game(against_nick, nick, channel)
        return True

# IRC Bot commands

botState = BotState()


def print_board(args, message: Message, notsave=False):
    nick = message.nick
    if not nick in botState.games:
        return "You aren't currently in any game. Type start [nick] to start a new game with a player"

    game = botState.get_selected_game(nick, message.channel)
    if game:
        return game.utf8_board(nick)
    return "You don't have any game selected on this channel"


async def start(bot, args, message):
    names = bot.channel_names[message.channel]
    nick = message.nick
    if not args[1]:
        return f"<{message.nick}> Usage: {PREFIX}start [nick] or start {NICK} to play against the cpu."
    if not args[1] in names:
        return f"The name {args[1]} is not on this channel or is invalid"
    if args[1] == message.nick:
        return f"<{args[1]}> Play with yourself using your own imagination!"
    if botState.has_invited(message.nick, args[1], message.channel):
        return f"<{message.nick}> You already invited {args[1]} for a game."
    if botState.has_game_with(message.nick, args[1], message.channel):
        return (
            f"<{message.nick}> You are already in a game with {args[1]} on this channel"
        )
    if args[1] == NICK:
        game = botState.add_game(message.nick, args[1], message.channel)
        increment_data(game.p1, "games")
        increment_data(game.p2, "games")
        return ["Starting CPU game"] + game.utf8_board(nick)

    botState.invite(nick, args[1], message.channel)
    return f"<{args[1]}> {nick} is challenging you to a chess game. Use `{PREFIX}accept {nick}` to accept within the next {EXPIRE_INVITE_IN} seconds."


def accept(args, message):
    if not args[1]:
        return f"<{message.nick}> Usage: {PREFIX}accept [nick]"
    game = botState.add_game(args[1], message.nick, message.channel)
    if game is None:
        return f"<{message.nick}> You have no invitation from {args[1]} on this channel"

    increment_data(game.p1, "games")
    increment_data(game.p2, "games")
    return [f"<{message.nick}> Starting game with {args[1]}"] + game.utf8_board(game.p1)

def score(args, message):
    nick = args[1] if args[1] else message.nick
    data = copy(get_data(nick))
    if data is None:
        return f"<{message.nick}> I don't know nothing about you yet...." if not args[1] else "<{message.nick}> I don't know nothing about {nick} yet...."
    data.pop("prefs")
    data.pop("id")
    data.pop("nick")
    data['unfinished'] = data['games']-data['checkmates']-data['stalemates']-data['draws']-data['losses']
    return f"<{nick}> has: {', '.join([f'{n}: {v}' for n,v in data.items()])}"

def getMoves(uic, board):
    possible_moves = [m.uci() for m in list(board.legal_moves)]
    r_moves = []
    for mov in possible_moves:
        if mov.startswith(uic.lower()):
            r_moves.append(mov)
    return r_moves


def move(args, message):
    try:
        uci = chess.Move.from_uci(args[1])
    except:
        uci = None

    game: Game = botState.get_selected_game(message.nick, message.channel)
    if game is None:
        return f"<{message.nick}> You don't have any game selected"
    if game.nicks[game.player] != message.nick:
        return f"<{message.nick}> It is not your move!"
    board = game.board
    if uci not in board.legal_moves:
        if args[1] and len(args[1]) == 2 and re.match(r"^[a-h][1-8]$", args[1]):
            p_moves = getMoves(args[1], board)
            if len(p_moves) == 0:
                return f"({message.nick}) There are no possible moves for {args[1]}"
            return (
                f"({message.nick}) possible moves for {args[1].lower()} are: "
                + ", ".join(p_moves)
            )
        return f"({message.nick}) Invalid move! Use uic moves like e2e4, c8c4, a7a8q, etc..."

    game.move(args[1])

    def endGame(msg):
        textboard = game.utf8_board(game.nicks[game.player])
        botState.end_game(message.nick, game.nicks[game.player], message.channel)
        return [msg] + textboard + [f"{message.nick} wins"]

    def checkBoard():
        if board.is_game_over():
            against_nick = game.nicks[game.player]
            if board.is_variant_draw():
                increment_data(game.p1, "draws")
                increment_data(game.p2, "draws")
                return endGame("DRAW!")
            if board.is_stalemate():
                increment_data(message.nick, "stalemates")
                increment_data(against_nick, "losses")
                return endGame("STALEMATE!")
            if board.is_checkmate():
                increment_data(message.nick, "checkmates")
                increment_data(against_nick, "losses")
                return endGame("CHECKMATE!")
            increment_data(message.nick, "checkmates")
            increment_data(against_nick, "losses")
            return ["END...", game.utf8_board(game.nicks[game.player])]

    end = checkBoard()
    if end:
        return end

    if game.nicks[game.player] == NICK:
        if board.is_check():
            b1 = ['CHECK']
            b1 += game.utf8_board(game.nicks[game.player])
        else:
            b1 = game.utf8_board(game.nicks[game.player])

        uic = cpuPlay(game.board)
        game.player = not game.player
        game.history.append(uic)
        end = checkBoard()
        if end:
            return end

    if board.is_check():
        return ["CHECK"] + [f"It is {game.who()}'s time!"] + [game.utf8_board(game.nicks[game.player])]
    return [f"It is {game.who()}'s time!"] + game.utf8_board(game.nicks[game.player])


def label(args, message):
    if not args[1] or not args[1].isdigit():
        return f"<{message.nick}> Usage: {PREFIX}label [1|2]"
    n = int(args[1])
    if n > len(Game.LABEL) or n <= 0:
        return [
            f"<{message.nick}> There are only {len(Game.LABEL)} possible labels. Usage: {PREFIX}label [1|2]"
        ] + [f"{i+1}: {l}" for i, l in enumerate(Game.LABEL)]

    set_prefs(message.nick, label=Game.LABEL[n-1])
    game: Game = botState.get_selected_game(message.nick, message.channel)
    return (
        ["The label preference was set!"] + game.utf8_board(message.nick)
        if game
        else []
    )


def colors(args, message):
    av_colors_str = f"({message.nick}) The available colors are: " + ", ".join(
        Color.colors()
    )
    pieces_str = "pieces"
    board_str = "board"
    usage_str = (
        f"({message.nick}) Usage: colors [{pieces_str}|{board_str}] [color1] [color2]"
    )
    if not args[1]:
        return av_colors_str
    args = [args[i] for i in range(1, 4)]
    a = False
    if args[0] == "classic":
        BG = [Color.maroon, Color.gray]
        FG = [Color.white, Color.black]
        a = True
    if args[0] == "modern":
        BG = [Color.purple, Color.red]
        FG = [Color.white, Color.yellow]
        a = True
    if not a:
        if len(args) != 3:
            return usage_str
        elm, c1, c2 = args
        if not c1 in Color.colors() or not c2 in Color.colors():
            return [f"({message.nick}) Invalid colors!", av_colors_str]
        if elm == pieces_str:
            FG = [getattr(Color, c) for c in [c1, c2]]
        elif elm == board_str:
            BG = [getattr(Color, c) for c in [c2, c1]]
        else:
            return usage_str

    set_prefs(message.nick, fg=FG, bg=BG)
    game: Game = botState.get_selected_game(message.nick, message.channel)
    return (
        ["The color preference was set!"] + game.utf8_board(message.nick)
        if game
        else []
    )


def hint(args, message):
    game: Game = botState.get_selected_game(message.nick, message.channel)
    if game is None:
        return f"<{message.nick}> You don't have any game selected"
    board = game.board
    if args[1] and len(args[1]) == 2:
        return (
            f"({message.nick}) possible moves for {args[1].lower()} are: "
            + ", ".join(getMoves(args[1], board))
        )
    if args[1]:
        return "Pass in a board position like: hint e2, or no arguments to see all possible moves"
    possible_moves = [m.uci() for m in list(board.legal_moves)]
    return f"({message.nick}) possible moves are: " + ", ".join(possible_moves)


def undo(args, message):
    game: Game = botState.get_selected_game(message.nick, message.channel)
    against_nick = game.p2 if game.p1 == message.nick else game.p1
    if game is None:
        return f"<{message.nick}> You don't have any game selected"
    game.pop()
    if against_nick == NICK:
        game.pop()
    return [f"<{message.nick}> it is {game.nicks[game.player]}'s move"] + game.utf8_board(message.nick)


utils.setCommands(
    {
        "board": {
            "function": print_board,
            "help": "Displays the board",
            "command_help": "",
        },
        "move": {
            "function": move,
            "help": "Moves a piece",
            "command_help": f"Makes an uic movement: move [column][row][column][row]. e.g.: {PREFIX}m e2e4",
        },
        "colors": {
            "function": colors,
            "help": "Changes the board or pieces colors",
            "command_help": f"{PREFIX}colors [pieces|board] [color1] [color2]",
        },
        "undo": {
            "function": undo,
            "help": "Undoes the last move",
            "command_help": "",
        },
        "hint": {
            "function": hint,
            "help": "Get posible movements",
            "command_help": "",
        },
        "score": {
            "function": score,
            "help": "Player's status",
            "command_help": f"{PREFIX}score [nick]"
        },
        "label": {
            "function": label,
            "help": "Changes the top and bottom row of letters",
            "command_help": f"{PREFIX}label [1|2]"
        },
        "start": {
            "function": start,
            "help": "Starts a new game",
            "command_help": f"{PREFIX}start [nick] or start {NICK} to play against the cpu."
        },
        "accept": {
            "function": accept,
            "help": "Accepts a game request",
            "command_help": f"{PREFIX}accept [nick]"
        }
    },
    prefix=PREFIX
)


@utils.arg_command("who", "Whose move is it")
def who(args, message):
    game = botState.get_selected_game(message.nick, message.channel)
    if game:
        return f"<{message.nick}> it is {game.nicks[game.player]}'s move"
    return f"<{message.nick}> You are not on any game"

@utils.arg_command("invitations", "Check if someone started a game with you")
def invites(args, message):
    if not message.nick in botState.invites and message.channel in botState.invites[message.nick][message.channel]:
        return f"<{message.nick}> You don't have any game invitation here"
    names = list(botState.invites[message.nick][message.channel].keys())
    return f"<{message.nick}> You have game invitations from: " + ", ".join(names)

@utils.arg_command("history", "Display history of moves")
def history(args, message):
    game = botState.get_selected_game(message.nick, message.channel)
    if game:
        return f"<{message.nick}> {', '.join([str(m) for m in game.history])}"
    return f"<{message.nick}> You are not on any game"

@utils.arg_command("games", "Current games", "Displays your current games.")
def games(args, message):
    if not botState.has_any_game(message.nick, message.channel):
        return f"<{message.nick}> You don't have nay game on this channel."
    games = botState.get_games(message.nicks, message.channel)
    return f"<{message.nick}> Your games on this channel are against: " + ", ".join([g.p1 if g.p2 == message.nick else g.p2 for g in games])

@utils.arg_command("select", "Select/change between games", f"{PREFIX}select [nick]")
def select(args, message):
    if not args[1]:
        return f"<{message.nick}> Usage: {PREFIX}select [nick]"
    if not botState.has_game_with(message.nick, args[1], message.channel):
        return f"<{message.nick}> You do not have any game with {args[1]}"
    game = botState.select_game(message.nick, args[1], message.channel)
    return game.utf8_board(message.nick)

@utils.custom_handler(["part", "quit"])
def onQuit(nick, channel="", text=""):
    return f"Bye {nick}, I will miss you :(  oh it is too late now"


@utils.custom_handler("join")
def onEnter(nick, channel):
    if nick == NICK:  # Ignore myself ;)
        return
    if botState.has_any_game(nick, channel):
        games = botState.get_games(nick, channel)
        msg = []
        for game in games:
            if game.nicks[game.player] == nick:
                msg.append(f"<{nick}> you have a game with {game.nicks[not game.player]} and it is your turn")
            else:
                msg.append(f"<{nick}> you have a game with {game.nicks[game.player]}")
        return msg


async def onRun(bot: IrcBot):
    if isinstance(bot.channels, list):
        for channel in bot.channels:
            await bot.send_message(Color("CHESS BOT INITIALIZED", Color.light_green, Color.black).str, channel)
    else:
        await bot.send_message(Color("CHESS BOT INITIALIZED", Color.light_green, Color.black).str)

    while True:
        for nick in botState.invites:
            for channel in botState.invites[nick]:
                for against_nick in botState.invites[nick][channel]:
                    now = datetime.now().timestamp()
                    if now - botState.invites[nick][channel][against_nick] > EXPIRE_INVITE_IN:
                        botState.invites[nick][channel].pop(against_nick)
                        await bot.send_message(f"<{against_nick}> Your game request to {nick} has expired!", channel)
        await bot.sleep(.5)


##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD, tables=[db_handler])
    bot.runWithCallback(onRun)
