<!-- markdownlint-disable -->

<a href="../../documentation/IrcBot/message#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `IrcBot.message`






---

<a href="../../documentation/IrcBot/message/Message#L1"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Message`




<a href="../../documentation/IrcBot/message/__init__#L2"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(channel='', sender_nick='', message='', is_private=False, strip=True)
```

Message. 

:param channel: Channel from/to which the message is sent or user/nick if private :param sender_nick: Whoever's nick the message came from. Only for received messages. Aliases for this are nick. :param message:str text of the message. Aliases: str, text, txt. For outgoing messages you can also set this to a Color object. :param is_private: If True the message came from a user :param strip: bool, should the message's text be stripped? 





---

<a href="../../documentation/IrcBot/message/ReplyIntent#L22"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ReplyIntent`




<a href="../../documentation/IrcBot/message/__init__#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(message, func)
```

__init__. 

:param message: Message to send. You can use a message object if you want to change channel or make it a pm. :param func: Function to call passing the received full message string that the user will reply with. This is useful for building dialogs. This function must either return None, a message to send back (str or IrcBot.Message) or another ReplyIntent. It must receive one argument. 







---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
