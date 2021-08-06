import random

from aixapi import AIxResource
from IrcBot.bot import Color, IrcBot, utils

TEST = False
NICK = "ken"

# Get one at: https://apps.aixsolutionsgroup.com/
API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

INITIALIZER = f"""\
{{0}}: Hello ken! How are you?
{NICK}: Hi {{0}}! I am fine thanks, how are you?
{{0}}: I am fine thanks! What are you doing today?
{NICK}: Not much, just chatting.
{{0}}: Can you help me something. What is the square root of 2?
{NICK}: Yes I can! It is about 1.41
{{0}}: Thanks!
{NICK}: No problem! You can ask me anything!
{{0}}: Thats because we are friends!
{NICK}: Yes we are friends!
{{0}}: \
"""
TEMP = 0.7
TOP_P = 1.0
RESP_L = 2048
MAX_LEN = 4098  # This is the bot memory in characteres

GREETINGS = [
    "'sup?",
    "how does it go?",
    "ahoy!",
    "good day",
    "What's in the bag?",
    "what's the dizzle?",
    "how's it going?",
    "what ho?",
    "what's cooking?",
    "hello!",
]


class AiResource:
    __resource = None

    def __init__(self, resource, chatter):
        assert type(resource) == AIxResource
        self.__resource = resource
        self.chatter = str(chatter)
        self.log = INITIALIZER.format(self.chatter)

    def prompt(self, text):
        self.log += " " + str(text.replace("\\n", "\n"))
        while len(self.log) > MAX_LEN:
            self.log = "\n".join(self.log.split("\n")[:-1])

        response = self.__resource.compose(
            prompt=self.log,
            response_length=RESP_L,
            temperature=TEMP,
            top_p=TOP_P,
            stop_sequence=self.chatter + ":",
        )

        text_response = str(response.get("data", dict()).get("text"))

        self.log += str(text_response)
        while len(self.log) > MAX_LEN:
            self.log = "\n".join(self.log.split("\n")[1:])

        return text_response


def test():
    aix_resource = AIxResource(API_KEY)
    instance = AiResource(aix_resource, str(input("Your name: ")))
    while True:
        question = str(input(">> "))
        response = instance.prompt(question)
        print("OUT >> ", NICK, ":", response)
        print("-" * 25)


conversations = {}
utils.setPrefix("'")

@utils.regex_cmd_with_messsage(f"^\s*{NICK}:?\s*(.*)\s*$", False)
def respond(args, message):
    nick = message.sender_nick
    text = args[1].strip()
    text = text + "." if not (text.endswith(".") or text.endswith("!") or text.endswith("?")) else text
    if nick not in conversations:
        aix_resource = AIxResource(API_KEY)
        instance = AiResource(aix_resource, nick)
        conversations[nick] = instance
    return (
        f"{message.sender_nick}: "
        + conversations[nick]
        .prompt(text)
        .replace(f"{nick}:", "")
        .replace(f"{NICK}:", "")
        .strip()
    )

@utils.arg_command(
    "restart", help="restart our conversation and starts a fresh one(messy)", simplify=False
)
def restart(args, message):
    nick = message.sender_nick
    if nick not in conversations:
        aix_resource = AIxResource(API_KEY)
        instance = AiResource(aix_resource, nick)
        conversations[nick] = instance
    conversations[
        nick
    ].log = f"""\
    {nick}: \
    """
    return f"{message.sender_nick}: CONVERSATION RESTARTED"


@utils.arg_command("reset", help="Wipes our conversation", simplify=False)
def reset(args, message):
    nick = message.sender_nick
    if nick not in conversations:
        return "You didn't start a conversation with me"
    else:
        del conversations[nick]
        return f"{message.sender_nick}: CONVERSATION RESET"


@utils.arg_command(
    "log",
    help="Logs our whole conversation(spam alert! You better use this on a private message)",
    simplify=False,
)
def log(args, message):
    nick = message.sender_nick
    if nick not in conversations:
        return "You didn't start a conversation with me"
    else:
        return (
            ["STARTING LOG", "-" * 10]
            + [f">> {line}" for line in conversations[nick].log.split("\n")]
            + ["-" * 10]
        )


@utils.custom_handler("join")
def onEnter(nick, channel):
    print("OnEnter")
    if nick == NICK:
        print("Return by nick")
        return

    if nick not in conversations:
        print("Return by greeting")
        greeting = GREETINGS[random.randint(0, len(GREETINGS) - 1)]
        return f"{nick}: " + greeting

    print("Return by death")
    return (
        f"{nick}: Hi again! "
        + conversations[nick]
        .log.split("\n")[-1]
        .replace(f"{nick}:", "")
        .replace(f"{NICK}:", "")
        .strip()
    )


async def onConnect(bot: IrcBot):
    await bot.join("#bots")
    await bot.send_message("Hello everyone!", "#bots")


if __name__ == "__main__":
    if TEST:
        test()
    else:
        bot = IrcBot("irc.libera.org", nick=NICK)
        bot.runWithCallback(onConnect)

