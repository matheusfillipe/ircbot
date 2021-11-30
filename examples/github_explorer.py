import itertools
import logging
from IrcBot.bot import IrcBot, utils, Color, Message
from github import Github

NICK="_githubbot"
HOST="irc.example.org"
CHANNELS=["#bots", "#test"]

gh = Github("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

utils.setPrefix(":")
utils.setLogging(logging.DEBUG)
utils.setMaxArguments(25) # Accept 25 command arguments at max
utils.setSimplifyCommands(False)


def is_mine(message):
    return message.sender_nick == NICK.split("/")[0]

def shell(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode()
    except Exception as e:
        print("Shell command erroed: ", e)
        print(cmd)


@utils.arg_command("gh", "Searches my github repositories", "gh [query]")
def my_search_gh(args, message):
    query = " ".join(utils.m2list(args))
    res = []
    for repo in gh.get_user().get_repos():
        if query.casefold() in repo.name.casefold() and gh_owner == repo.owner.login:
            res.append(repo.html_url)
    return res

@utils.arg_command("fgh", "Searches my github repositories and a file on it", "gh [repo] [filename]")
def my_search_gh(args, message):
    query = args[1]
    file = args[2]
    urls = []
    results = []
    for repo in gh.get_user().get_repos():
        if query.casefold() in repo.name.casefold() and gh_owner == repo.owner.login:
            contents = repo.get_contents("")
            results.append(repo.html_url)
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                if file.casefold() in file_content.name.casefold():
                    urls.append(file_content.html_url)
    if urls:
        return urls
    return "File not found, repo: " + ", ".join(results)


@utils.arg_command("gl", "Searches my gitlab repositories", "gl [query]")
def my_search_gl(args, message):
    query = " ".join(utils.m2list(args)).strip().casefold()
    res = []
    for repo in gl.projects.list(owned=True, all=True):
        log(repo.name.casefold())
        if query.casefold() in repo.name.casefold():
            res.append(repo.web_url)
    return res

@utils.arg_command("fgl", "Searches my gitlab repositories and a file on it", "fgl [repo] [filename]")
def my_search_gh(args, message):
    query = args[1]
    file = args[2]
    results = []
    urls = []
    for repo in gl.projects.list(owned=True, all=True):
        if query.casefold() in repo.name.casefold():
            results.append(repo.web_url)
            # get default branch for url
            for branch in repo.branches.list():
                if branch.attributes['default']:
                    break
            content = repo.repository_tree(recursive=True, all=True)
            for file_content in content:
                if file and file.casefold() in file_content['name'].casefold():
                    urls.append(f"{repo.web_url}/-/blob/{branch.name}/{file_content['path']}")
    if urls:
        return urls
    return "File not found, repo(s): " + ", ".join(results)

search_last_result = None
search_last_index = 0

def gh_repotimedelta(repo):
    try:
        commit = repo.get_commits()[0]
        return datetime.utcnow() - datetime.strptime(commit.last_modified, '%a, %d %b %Y %H:%M:%S GMT')
    except GithubException:
        return datetime.utcnow() - datetime(1970, 1, 1)

def ghsearch_format(repo):
    delta = gh_repotimedelta(repo)
    minimum = "years" if delta.days > 365 else "days"
    delta = humanize.precisedelta(delta, minimum_unit=minimum, format="%d")
    return f"{repo.html_url} - {repo.stargazers_count}🌟 - modified {delta} ago."

def gh_search(query, _next=False):
    global search_last_result, search_last_index
    if _next and search_last_result:
        search_last_index += GH_LIST_LEN
        return [ghsearch_format(repo) for repo in search_last_result[search_last_index:GH_LIST_LEN + search_last_index]]

    repolist = gh.search_repositories(query=query)
    search_last_result = repolist
    repolist = list(itertools.islice(repolist, GH_LIST_LEN))
    search_last_index = 0
    return [ghsearch_format(repo) for repo in repolist]

@utils.arg_command("next", "next page of results for github search")
def next_page(args, message):
    return gh_search(None, True)

@utils.arg_command("lang", "github language search")
def f1(args, message):
    args = utils.m2list(args)
    query = " ".join(args[1:])
    return gh_search(f"{query} language:{args[0]}")

@utils.arg_command("user", "List repos of a user on github")
def f2(args, message):
    args = utils.m2list(args)
    return gh_search(f"user:{args[0]}")

@utils.arg_command("s", "Search on github")
def fs(args, message):
    args = utils.m2list(args)
    query = " ".join(args)
    return gh_search(f"{query}")

@utils.arg_command("gr", "github jepo info")
def grepo(args, message):
    try:
        repo = gh.get_repo(args[1])
    except GithubException:
        return f"<{message.nick}> Repo not found!"
    return ghsearch_format(repo)

@utils.arg_command("forks", "Searches for forks or repository")
def forks(args, message):
    MAX_REPOS = 500
    try:
        repo = gh.get_repo(args[1])
    except GithubException:
        return f"<{message.nick}> Repo not found!"

    if repo.forks == 0:
        return "This repo has no forks!"
    def last_modified(r):
        if r.last_modified:
            return datetime.utcnow() - datetime.strptime(r.last_modified, '%a, %d %b %Y %H:%M:%S GMT')
        return gh_repotimedelta(r)

    def get_forks(r):
        repos = []
        for fork in itertools.islice(r.get_forks(), MAX_REPOS):
            repos.append(fork)
            try:
                repos += get_forks(fork)
            except GithubException:
                continue
        return repos

    repolist = get_forks(repo)
    rs = sorted(repolist, key=lambda r: r.stargazers_count, reverse=True)
    trs = []
    if len(repolist) < MAX_REPOS:
        trs = [r for r in sorted(repolist, key=last_modified)[:GH_LIST_LEN] if r not in rs]
    return [ghsearch_format(r) for r in rs[:GH_LIST_LEN] + trs]


if __name__ == "__main__":
    bot = IrcBot(HOST, nick=NICK, channels=CHANNELS)
    bot.run()
