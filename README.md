# Simple IRC Bot Framework

## What is this?

Just a experimental and simple irc base bot designed to make it easy to add
commands and that also shows previews for urls. A demo can be seen on the ##0dev freenode channel.


## How to add/edit commands?

Just go to commands.py.

INFO_CMDS is a dict that has regex expressions as keys
for that will match and return the static text at value. This is useful for
creating like the rules commands and whatever will return just static text.

With the `@utils.regex_cmd` decorator you can match regular expressions and run
whatever you want with the received message that is the argument this function
will receive. This handler function has to either return a string, that will be
the delivered message, or a list of strings that will be multiple messages to
be send.



## TODO

1. Support for private messages
2. Data permanency.



