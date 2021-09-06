import itertools
import logging
from IrcBot.bot import IrcBot, utils, Color, Message
from github import Github

NICK="_githubbot"
HOST="irc.example.org"
CHANNELS=["#bots", "#test"]

gh = Github("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

utils.setPrefix("=")
utils.setLogging(logging.DEBUG)
utils.setMaxArguments(25) # Accept 25 command arguments at max
utils.help_on_private=True

def gh_search(query):
    repolist = gh.search_repositories(query=query)   
    repolist = list(itertools.islice(repolist, 10))
    return [repo.html_url for repo in repolist]

@utils.arg_command("lang", "language search")
def f1(args, message):
    args = utils.m2list(args)
    query = " ".join(args[1:])
    return gh_search(f"{query} language:{args[0]}")

@utils.arg_command("user", "List repos of a user")
def f2(args, message):
    args = utils.m2list(args)
    return gh_search(f"user:{args[0]}")

@utils.arg_command("s", "Search")
def fs(args, message):
    args = utils.m2list(args)
    query = " ".join(args)
    return gh_search(f"{query}")

if __name__ == "__main__":
    bot = IrcBot(HOST, nick=NICK, channels=CHANNELS)
    bot.run()
