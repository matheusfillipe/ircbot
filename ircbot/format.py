import random
import re


class Style:
    reset = "\x0F"
    str: str


class TextStyle(Style):
    """Text styles enum.
    https://modern.ircdocs.horse/formatting
    """

    bold = "\x02"
    italic = "\x1D"
    underline = "\x1F"
    strikethrough = "\x1E"
    monospace = "\x11"

    def __init__(self, text: str, style: str):
        self.text = "{}{}{}".format(style, text, self.reset)
        self.str = self.text + self.reset

    def __str__(self):
        return self.str


class Color(Style):
    """Colorcodes enum."""

    esc = "\003"
    white = "00"
    black = "01"
    navy = "02"
    green = "03"
    red = "04"
    maroon = "05"
    purple = "06"
    orange = "07"
    yellow = "08"
    light_green = "09"
    teal = "10"
    cyan = "11"
    blue = "12"
    magenta = "13"
    gray = "14"
    light_gray = "15"

    COLORS = [
        "00",
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
    ]

    def __init__(self, text: str, fg: str, bg: str | None = None):
        if bg is not None:
            self.text = "{}{},{}{}".format(self.esc, fg, bg, text)
        else:
            self.text = "{}{}{}".format(self.esc, fg, text)
        self.str = self.text + Color.esc

    @classmethod
    def random(cls):
        return random.choice(cls.COLORS)

    @classmethod
    def colors(cls):
        """Returns the color names."""
        return [
            k
            for k in Color.__dict__
            if not (k.startswith("_") or k in ["esc", "COLORS", "colors", "getcolors", "random"])
        ]

    def __str__(self):
        return self.str


def irc_sanitize_nick(s: str) -> str:
    nick = s.strip().casefold()
    nick = re.sub(r"\s+", "_", nick)
    nick = re.sub(r"[^a-z0-9_]", "", nick)
    nick = nick.lstrip("_").rstrip("_")
    return nick


def truncate_words(content: str, length: int = 10, suffix: str = "...") -> str:
    """Truncates a string after a certain number of words."""
    split = content.split()
    if len(split) <= length:
        return " ".join(split[:length])
    return " ".join(split[:length]) + suffix


def truncate(content: str, length: int = 440, suffix: str = "...", sep: str = " ") -> str:
    """Truncates a string after a certain number of characters.

    Function always tries to truncate on a word boundary.
    """
    if len(content) <= length:
        return content

    return content[:length].rsplit(sep, 1)[0] + suffix


def split_in_lines(content: str, length: int = 440) -> list[str]:
    """Turns a long string into a list of strings with a maximum length respecting word boundaries."""
    lines = []
    while len(content) > length:
        line = content[:length]
        last_space = line.rfind(" ")
        if last_space == -1:
            last_space = length
        lines.append(content[:last_space].strip())
        content = content[last_space:].strip()
    lines.append(content)
    return lines


def format_line_breaks(content: str, length: int = 440) -> list[str]:
    """Turns a long string into a list of strings with a maximum length respecting word boundaries and turning
    newlines into new messages.
    """
    lines = []
    for line in content.split("\n"):
        lines.extend(split_in_lines(line, length))
    return lines


def markdown_to_irc(content: str, syntax_highlighting: bool = False) -> str:
    """Converts markdown to IRC format."""

    translation_map = {
        "**": TextStyle.bold,
        "*": TextStyle.bold,
        "__": TextStyle.underline,
        "_": TextStyle.italic,
        "~~": TextStyle.strikethrough,
        "~": TextStyle.strikethrough,
    }

    translation_map = {re.escape(k): v for k, v in translation_map.items()}

    def highlight_code(content: str, lang: str = "bash") -> str:
        if not syntax_highlighting:
            return content

        try:
            import pygments
            from pygments import formatters, lexers
            from pygments.util import ClassNotFound
        except ImportError:
            raise ImportError("You need to install pygments to use syntax highlighting. pip install pygments")
        try:
            Lexer = lexers.find_lexer_class_by_name(lang)
        except ClassNotFound:
            Lexer = lexers.TextLexer

        return pygments.highlight(content, Lexer(), formatters.IRCFormatter(bg="dark"))

    def replace_simple(text: str) -> str:
        for k, v in translation_map.items():
            regex = re.compile(f"{k}(.+?){k}")
            text = regex.sub(f"{v}\\1{TextStyle.reset}", text)
        return text

    output = ""
    for i, part in enumerate(content.split("```")):
        if i % 2 == 0:
            for i, inner in enumerate(part.split("`")):
                if i % 2 == 0:
                    output += replace_simple(inner)
                else:
                    output += Color(f" {inner} ", fg=Color.light_gray, bg=Color.black).str
        else:
            lang, code = part.split("\n", 1)
            highlighted_text = highlight_code(code, lang.strip() or "bash")

            # We need to restore the unclosed escape sequences for each of the lines
            color = ""
            for line in highlighted_text.split("\n"):
                if color:
                    line = color + line

                output += line + "\n"

                for i, char in enumerate(line):
                    if char == Color.esc:
                        match = re.search(r"\x03\d{1,2}(,\d{1,2})?.*$", line[i:])
                        if match:
                            color = f"\x03{match[0]}{match[1] or ''}"
                        else:
                            color = ""

    return output
