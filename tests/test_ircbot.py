from multiprocessing.connection import Connection
from unittest.mock import MagicMock

import pytest
from ircbot.client import IrcBot
from ircbot.message import Message, ReplyIntent


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
