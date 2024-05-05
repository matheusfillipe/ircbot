import logging
import re

has_validators = False
try:
    import validators

    has_validators = True
except:
    pass


logger = logging.getLogger()


def m2list(args: re.Match):
    """Convert a re.Match object to a list of match strings"""
    return [a for a in args.groups() if a]


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


def set_loglevel(level, logfile=None):
    """Sets the loggins level of the logging module.

    :param level: int. level, (logging.DEBUG, logging.INFO, etc...)
    :param logfile: str. Path for file or empty for none.
    """
    global logger
    logging.basicConfig(
        level=level,
        filename=logfile,
        format="%(asctime)s::%(levelname)s -> %(message)s",
        datefmt="%I:%M:%S %p",
    )
    logger = logging.getLogger()
    logger.setLevel(level)


def log(*args, level=logging.INFO):
    msg = " ".join([str(a) for a in list(args)])
    if type(level) == int:
        logger.log(level, msg)
    elif type(level) == str:
        getattr(logger, level)(msg)


def debug(*args, level=logging.DEBUG):
    msg = " ".join([str(a) for a in list(args)])
    logger.log(level, msg)


def warning(*args, level=logging.WARNING):
    msg = " ".join([str(a) for a in list(args)])
    logger.log(level, msg)


# Extras
def validate_url(url: str) -> bool:
    if has_validators:
        return validators.url(url)
    else:
        raise ImportError("The 'validators' module is not installed.")


set_loglevel(logging.INFO)
