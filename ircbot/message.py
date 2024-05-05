from typing import TypeAlias

from ircbot.format import Style


class RawMessage:
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Message(object):
    def __init__(self, channel="", sender_nick="", message="", is_private=False, strip=True):
        """Message.

        :param channel: Channel from/to which the message is sent or user/nick if private
        :param sender_nick: Whoever's nick the message came from. Only for received messages. Aliases for this are nick.
        :param message:str text of the message. Aliases: str, text, txt. For outgoing messages you can also set this to a Color object.
        :param is_private: If True the message came from a user
        :param strip: bool, should the message's text be stripped?
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


class ReplyIntent(object):
    def __init__(self, message, func):
        """__init__.

        :param message: Message to send. You can use a message object if you want to change channel or make it a pm.  :param func: Function to call passing the received full message string that the user will reply with. This is useful for building dialogs. This function must either return None, a message to send back (str or IrcBot.Message) or another ReplyIntent. It must receive one argument."""
        self.func = func
        self.message = message


Sendable: TypeAlias = str | Message | Style | list[str] | list[Message] | list[Style] | ReplyIntent
