from multiprocessing.connection import Connection

import pytest
from ircbot.client import IrcBot
from ircbot.message import Message, MessageTags, ReplyIntent


def _run_bot(bot: IrcBot, on_start=None):
    try:
        if on_start is None:
            bot.run()
        else:
            bot.run(on_start)
    except ConnectionResetError:
        # TODO: This will happen sometimes
        pass


def _test_connection(bot: IrcBot, watcher: Connection):
    async def on_start():
        assert bot.is_running_with_callback
        await bot.send_message("Hello, world!")
        await bot.wait_for_messages_sent()
        bot.close()

    _run_bot(bot, on_start)
    if watcher.poll(5):
        assert "Hello, world!" in watcher.recv().text
    else:
        pytest.fail("No message received")


def test_connection(bot: IrcBot, watcher: Connection):
    _test_connection(bot, watcher)


def test_ssl_connection(ssl_ircbot: IrcBot, watcher: Connection):
    _test_connection(ssl_ircbot, watcher)


def test_reply_intent(bot: IrcBot, watcher: Connection):
    async def callback(message):
        return "response"

    @bot.regex_cmd_with_message(r"^command_test_reply_intent$", True)
    def command_test_reply_intent(args, message):
        return ReplyIntent(Message(channel=message.channel, message="Reply intent test"), callback)

    async def on_start():
        watcher.send("command_test_reply_intent")
        await bot.sleep(3)
        watcher.send("request")
        await bot.sleep(3)
        bot.close()

    _run_bot(bot, on_start)

    if watcher.poll(3):
        messages = []
        while watcher.poll():
            messages.append(watcher.recv().text)
        assert "Reply intent test" in messages
        assert "response" in messages
    else:
        pytest.fail("No message received")


@pytest.mark.parametrize(
    "raw_tags,expected_account,expected_bot,expected_msgid,expected_has_time",
    [
        # Basic tags with account and timestamp
        ("time=2025-08-30T16:41:14.234Z;account=testuser", "testuser", False, None, True),
        # Tags with bot flag
        ("time=2025-08-30T16:41:14.234Z;account=testuser;bot", "testuser", True, None, True),
        # Tags with msgid
        ("account=mattf;msgid=abc123;time=2025-08-30T16:41:14.234Z", "mattf", False, "abc123", True),
        # Boolean tag only
        ("bot", None, True, None, False),
        # No account tag
        ("time=2025-08-30T16:41:14.234Z;msgid=xyz789", None, False, "xyz789", True),
        # Empty tags
        ("", None, False, None, False),
    ],
)
def test_message_tags_integration(raw_tags, expected_account, expected_bot, expected_msgid, expected_has_time):
    """Test that MessageTags integration works with various tag combinations"""
    # Test Message objects with tags
    tags = MessageTags(raw_tags)
    message = Message("channel", "nick", "test message", tags=tags)

    assert message.tags.account == expected_account
    assert message.tags.bot == expected_bot
    assert message.tags.msgid == expected_msgid
    assert (message.tags.time is not None) == expected_has_time


@pytest.mark.parametrize(
    "irc_message,expected_message_data,expected_account,expected_bot",
    [
        # Tagged message with account
        (
            "@time=2025-08-30T16:41:14.234Z;account=testuser :user!host PRIVMSG #channel :hello",
            ":user!host PRIVMSG #channel :hello",
            "testuser",
            False,
        ),
        # Tagged message with bot flag
        (
            "@account=botuser;bot :botuser!host PRIVMSG #channel :automated message",
            ":botuser!host PRIVMSG #channel :automated message",
            "botuser",
            True,
        ),
        # Untagged message
        (":user!host PRIVMSG #channel :normal message", ":user!host PRIVMSG #channel :normal message", None, False),
        # Empty tags
        ("@ :user!host PRIVMSG #channel :test", ":user!host PRIVMSG #channel :test", None, False),
    ],
)
def test_bot_message_parsing(irc_message, expected_message_data, expected_account, expected_bot):
    """Test that IrcBot can parse various IRC message formats with tags"""
    bot = IrcBot("test.server.com", nick="testbot")
    message_data, parsed_tags = bot._parse_message_with_tags(irc_message)

    assert message_data == expected_message_data

    if irc_message.startswith("@"):
        # Tagged message should have parsed tags (even if empty)
        assert parsed_tags is not None
        assert parsed_tags.account == expected_account
        assert parsed_tags.bot == expected_bot
    else:
        # Untagged message should have no tags
        assert parsed_tags is None
