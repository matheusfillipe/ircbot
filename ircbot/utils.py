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
