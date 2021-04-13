from IrcBot.bot import IrcBot, utils, Color
from IrcBot.utils import log, debug
import logging, random
from copy import copy
import chess

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = 'irc.freenode.org'
PORT = 6667
NICK = 'chessbot'
PASSWORD = ''
USERNAME = NICK
REALNAME = NICK
CHANNELS = ["#bots"]  # , "#lobby",]
ACCEPT_PRIVATE_MESSAGES = True
PREFIX = ';'
DBFILEPATH = NICK+".db"

############################################################

gayColors = copy(Color.COLORS)
[gayColors.remove(k) for k in [Color.white, Color.gray, Color.light_gray, Color.black]]

@utils.regex_cmd_with_messsage(f"^{PREFIX}gay (.+)$", ACCEPT_PRIVATE_MESSAGES)
def gay(args, message):
    # use .text or .str to extract string values
    return "".join([Color(c, random.choice(gayColors)).str for c in args[1]])

@utils.regex_cmd_with_messsage(f"^{PREFIX}sep$", ACCEPT_PRIVATE_MESSAGES)
def separator(args, message):
    # You can also retunr a Color object or a list of colors
    return [
        Color(" "*120, bg=Color.purple),
        Color(" "*120, bg=Color.white),
        Color(" "*120, bg=Color.light_green),
        Color(" "*120, bg=Color.red),
    ]

remap = {
    "R": "♜",
    "N": "♞",
    "B": "♝",
    "Q": "♛",
    "K": "♚",
    "P": "♟︎",
    ".": "♟︎",
}

BG = [Color.maroon, Color.gray]
FG = [Color.white, Color.black]
board = chess.Board()

@utils.regex_cmd_with_messsage(f"^{PREFIX}board$", ACCEPT_PRIVATE_MESSAGES)
def print_board(args, message):
    global FG, BG, board
    # You can also retunr a Color object or a list of colors
    label = "     A   B   C   D   E   F   G   H  "
    lines = str(board).split('\n')
    R=[]
    bgi=1
    row=8
    R.append(label)
    for l in lines:
        colors=[]
        for c in l:
            if not c.upper() in remap:
                continue
            if c.upper() == c:
                piece = Color(f" {remap[c.upper()]} ", bg=BG[bgi], fg=FG[0] if c != "." else BG[bgi])
            else:
                piece = Color(f" {remap[c.upper()]} ", bg=BG[bgi], fg=FG[1] if c != "." else BG[bgi])
            colors.append(piece)
            bgi = not bgi
        bgi = not bgi
        R.append(str(row) + " " + "".join([c.str for c in colors]) + " " + Color(str(row)).str)
        row-=1
    R.append(label)
    return R

@utils.regex_cmd_with_messsage(f"^{PREFIX}reset$", ACCEPT_PRIVATE_MESSAGES)
def reset(args, message):
    global FG, BG, board
    BG = [Color.maroon, Color.gray]
    FG = [Color.white, Color.black]
    board = chess.Board()
    return print_board(None, None)

def endGame(msg):
    board = chess.Board()
    return [msg, print_board(None, None)]

@utils.regex_cmd_with_messsage(f"^{PREFIX}help$", ACCEPT_PRIVATE_MESSAGES)
def help(args, message):
    return f"({message.nick}) possible moves are: " + ", ".join([m.uci() for m in list(board.legal_moves)])

@utils.regex_cmd_with_messsage(f"^{PREFIX}move (.+)$", ACCEPT_PRIVATE_MESSAGES)
def move(args, message):
    global board
    try:
        uci = chess.Move.from_uci(args[1])
    except:
        return f"({message.nick}) Use uic moves like e2e4, c8c4, etc..."
    if uci not in board.legal_moves:
        return [f"({message.nick}) Invalid move!", print_board(None, None)]

    board.push_uci(args[1])
    if board.is_stalemate():
        return endGame("STALEMATE!")
    if board.is_checkmate():
        return endGame("CHECKMATE!")
    if board.is_check():
        return ["CHECK...", print_board(None, None)]

    return print_board(None, None)

@utils.regex_cmd_with_messsage(f"^{PREFIX}colors ?(.*)$", ACCEPT_PRIVATE_MESSAGES)
def colors(args, message):
    global FG, BG, board
    av_colors_str = f"({message.nick}) The available colors are: " + ", ".join(Color.colors())
    pieces_str = "pieces"
    board_str = "board"
    usage_str = f"({message.nick}) Usage: colors [{pieces_str}|{board_str}] [color1] [color2]"
    if not args[1]:
        return av_colors_str
    args = args[1].split()
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
    return print_board(None, None)


##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD)
    bot.run()
