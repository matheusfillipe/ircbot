from IrcBot.bot import IrcBot, utils, Color
from IrcBot.utils import log, debug
import logging, random, re, chess
from copy import copy

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = 'irc.server.org'
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
LABEL = [
    "   A  B  C  D  E  F  G  H   ",
    "     A   B   C   D   E   F   G   H  ",
]

PREF = {}
TURN = False
PLAYER = ["", ""]

@utils.regex_cmd_with_messsage(f"^{PREFIX}(board|b) ?(\S)?$", ACCEPT_PRIVATE_MESSAGES)
def print_board(args, message, notsave=False):
    global FG, BG, board
    lines = str(board).split('\n')
    if args and not args[2] is None and type(args[2])==str and args[2].isdigit():
        i = int(args[2])
        if i >= len(LABEL):
            return f"Choose a number less than {len(LABEL)}"
        label = LABEL[i]
        if not notsave:
            PREF[message.nick] = i
    elif message and message.nick in PREF:
        label = LABEL[PREF[message.nick]]
    else:
        label = LABEL[0]
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
        colors[-1].str = colors[-1].str[:-1]
        R.append(str(row) + " " + "".join([c.str for c in colors]) + " \003 " + str(row))
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
    return f"({message.nick}) possible commands are: help, board, move|m, hint, undo, colors" 

def getMoves(uic):
    global board
    possible_moves = [m.uci() for m in list(board.legal_moves)]
    r_moves = []
    for mov in possible_moves:
        if mov.startswith(uic.lower()):
            r_moves.append(mov)
    return r_moves

@utils.regex_cmd_with_messsage(f"^{PREFIX}hint ?(.*)$", ACCEPT_PRIVATE_MESSAGES)
def hint(args, message):
    possible_moves = [m.uci() for m in list(board.legal_moves)]
    if args[1] and len(args[1]) == 2:
        return f"({message.nick}) possible moves for {args[1].lower()} are: " + ", ".join(getMoves(args[1]))
    elif args[1]:
        return "Pass in a board position like: hint e2, or no arguments to see all possible moves"
    return f"({message.nick}) possible moves are: " + ", ".join(possible_moves)

@utils.regex_cmd_with_messsage(f"^{PREFIX}undo$", ACCEPT_PRIVATE_MESSAGES)
def undo(args, message):
    global board, TURN
    TURN = not TURN
    board.pop()
    return print_board(None, None)

@utils.regex_cmd_with_messsage(f"^{PREFIX}(move|m) ?(.+)?$", ACCEPT_PRIVATE_MESSAGES)
def move(args, message):
    global board, TURN, PLAYER, PREF
    try:
        uci = chess.Move.from_uci(args[2])
    except:
        uci=None

    if uci not in board.legal_moves:
        if args[2] and len(args[2]) == 2 and re.match(r'^[a-h][1-8]$', args[2]):
            p_moves = getMoves(args[2])
            if len(p_moves) == 0:
                return f"({message.nick}) There are no possible moves for {args[2]}"
            return f"({message.nick}) possible moves for {args[2].lower()} are: " + ", ".join(p_moves)
        return f"({message.nick}) Invalid move! Use uic moves like e2e4, c8c4, etc..."

    board.push_uci(args[2])
    if board.is_variant_draw():
        return endGame("DRAW!")
    if board.is_stalemate():
        return endGame("STALEMATE!")
    if board.is_checkmate():
        return endGame("CHECKMATE!")
    if board.is_check():
        return ["CHECK...", print_board(None, None)]

    PLAYER[TURN] = message.nick
    TURN = not TURN
    if PLAYER[TURN] in PREF:
        return print_board(["", "", str(PREF[PLAYER[TURN]])], None, notsave=True)
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
    if c1 == c2:
        return f"({message.nick}) Do not use equal colors ;)"
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
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, USERNAME, PASSWORD, accept_join_from=["mattf"])
    bot.run()
