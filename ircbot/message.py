from __future__ import annotations

import logging
from collections.abc import Awaitable
from datetime import datetime
from typing import Callable, TypeAlias

from ircbot.format import Style

logger = logging.getLogger(__name__)


class MessageTags:
    def __init__(self, raw_tags: str = ""):
        self.raw_dict: dict[str, str | bool] = {}
        self.time: datetime | None = None
        self.account: str | None = None
        self.msgid: str | None = None
        self.bot: bool = False

        if raw_tags:
            self._parse_tags(raw_tags)

    def _parse_tags(self, raw_tags: str):
        for tag_pair in raw_tags.split(";"):
            if "=" in tag_pair:
                key, value = tag_pair.split("=", 1)
                self.raw_dict[key] = value
                self._set_common_tag(key, value)
            else:
                self.raw_dict[tag_pair] = True
                self._set_common_tag(tag_pair, True)

    def _set_common_tag(self, key: str, value: str | bool):
        if key == "time" and isinstance(value, str):
            try:
                self.time = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"Failed to parse timestamp: {value}")
        elif key == "account" and isinstance(value, str):
            self.account = value
        elif key == "msgid" and isinstance(value, str):
            self.msgid = value
        elif key == "bot" and isinstance(value, bool):
            self.bot = value


class RawMessage:
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Message(object):
    def __init__(
        self, channel="", sender_nick="", message="", is_private=False, strip=True, tags: MessageTags | None = None
    ):
        """Message.

        :param channel: Channel from/to which the message is sent or user/nick if private
        :param sender_nick: Whoever's nick the message came from. Only for received messages. Aliases for this are nick.
        :param message:str text of the message. Aliases: str, text, txt. For outgoing messages you can also set this to a Color object.
        :param is_private: If True the message came from a user
        :param strip: bool, should the message's text be stripped?
        :param tags: IRC message tags if present
        """
        self.channel = channel.strip()
        self.sender_nick = sender_nick.strip()
        self.nick = sender_nick.strip()
        if strip and isinstance(message, str):
            self.message = message.strip()
        else:
            self.message = message
        self.txt = self.text = self.message
        self.is_private = is_private
        self.tags = tags or MessageTags()


class ReplyIntent(object):
    def __init__(self, message: Sendable, func: Callable[[Message], Sendable | Awaitable[Sendable]]):
        """Handles Nick and channel specific itent to reply to a message with a custom callback.

        :param message: Message to send. You can use a message object if you want to change channel or make it a pm.
        :param func: Function to call passing the received full message string that the user will reply with. This is useful for building dialogs. This function must either return None, a message to send back (str or IrcBot.Message) or another ReplyIntent. It must receive one argument."""
        self.func = func
        self.message = message


Sendable: TypeAlias = str | Message | Style | list[str] | list[Message] | list[Style] | ReplyIntent
