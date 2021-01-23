# -*- coding: utf-8 -*-

#########################################################################
#  Matheus Fillipe -- 13, December of 2020                              #
#                                                                       #
#########################################################################
#  Description: Simple bot framework that will handle the very basic.   #
#                                                                       #
#                                                                       #
#########################################################################
#  Depends on: `pip3 install -r requirements.txt`                       #
#                                                                       #
#########################################################################


import socket
import re
import traceback
import trio
from copy import deepcopy
from IrcBot import utils
from IrcBot.utils import log, debug, logger
from IrcBot.sqlitedb import DB

utils = utils

BUFFSIZE = 2048

class dbOperation(object):
    ADD = 1
    UPDATE = 0
    REMOVE = -1
    def __init__(self, data = {}, id = {}, op = UPDATE):
        self.data = data
        self.id = id
        self.op = op

class tempData(object):
    def __init__(self):
        """Initializes a temporary data object that can be retrieved from the same user and channel.
        """
        self.data = {}

    def push(self, msg, data):
        """Stores any data for the current nick and channel.
        :param msg: Message object
        :param data: Value to store (Any)
        """
        self.data[(msg.channel, msg.sender_nick)] = data

    def pop(self, msg):
        """Deletes data for user channel of the given message.
        :param msg: Message object
        """
        del self.data[(msg.channel, msg.sender_nick)]

    def get(self, msg):
        """Returns data for user channel of the given message.
        :param msg: Message object
        """
        return self.data[(msg.channel, msg.sender_nick)]



class persistentData(object):
    def __init__(self, filename, name, keys):
        """__init__.

        :param name: Name of the table
        :param keys: List of strings. Names for each column
        :param blockDB: If true the database connection will be kept open. This can increase performance but you will have to shut down the bot in case you want to edit the database file manually. 

        You can have acess to the data list with self.data
        """
        self.name = name
        self.keys = keys
        self.filename = filename
        self.blockDB = False
        self._queue = []
        self.data = []
        self.initDB(filename)
        self.fetch()

    def initDB(self, filename):
        self.db = DB(filename, self.name, self.keys, self.blockDB)

    def fetch(self):
        """fetches the list of dicts/items with ids."""
        self.data = self.db.getAllWithId()
        return self.data

    def push(self, items):
        """push. Add new items to the table
        :param items: list or single dict.
        """
        if type(items) == list:
            for item in items:
                self.push(item)
        else:
            self._queue.append(dbOperation(data=items, op=dbOperation.ADD))


    def pop(self, id):
        """Removes the row based on the id. (You can see with self.data)
        :param id: int
        """
        assert type(id)==int, "id needs to be an int!"
        self._queue.append(dbOperation(id=id, op=dbOperation.REMOVE))

    def update(self, id, item):
        """update.
        :param id: id of item to update, change.
        :param item: New item to replace with. This dict doesn't need to have all keys/columns, just the ones to be changed.
        """
        assert type(item) == dict , "item must be either list or dict"
        assert type(id)==int, "id needs to be an int!"
        self._queue.append(dbOperation(id=id, data=item, op=dbOperation.update))

    def clear(self):
        """Clear all the proposed modifications.
        """
        self._queue = []
            

        
class Message(object):
    def __init__(self, channel='', sender_nick='', message='', is_private=False):
        self.channel = channel.strip()
        self.sender_nick = sender_nick.strip()
        self.nick = sender_nick.strip()
        self.message = message.strip()
        self.txt = self.text = self.message
        self.is_private = is_private

class ReplyIntent(object):
    def __init__(self, message, func):
        """__init__.
        :param message: Message to send. You can use a message object if you want to change channel or make it a pm.
        :param func: Function to call passing the received full message string that the user will reply with. This is useful for building dialogs. This function must either return None, a message to send back (str or IrcBot.Message) or another ReplyIntent. It must receive one argument. 
        """
        self.func = func
        self.message = message


class IrcBot(object):
    """IrcBot."""

    def __init__(self, host, port=6665, nick="bot", channels=[], username=None, password='', nickserv_auth=False, use_sasl=False, tables=[]):
        """Creates a bot instance joining to the channel if specified

        :param host: str. Server hostname. ex: "irc.freenode.org"
        :param port: int. Server port. default 6665
        :param nick: str. Bot nickname. If this is set but username is not set then this will be used as the username for authentication if password is set.
        :param channel: List of strings of channels to join or string for a single channel. You can leave this empty can call .join manually.
        :param username: str. Username for authentication.
        :param password: str. Password for authentication.
        :param nickserv_auth: bool. Authenticate with 'PRIVMSG NickServ :IDENTIFY' . Should work in most servers.
        :param use_sasl: bool. Use sasl autentication. (Still not working. Don't use this!)
        :param tables: List of persistentData to be registered on the bot.
        """

        self.nick = nick
        self.password = password
        self.username = username
        self.host = host
        self.port = port
        self.channels = channels
        self.nickserv_auth = nickserv_auth
        self.use_sasl = use_sasl
        self.tables = tables

        self.send_message_channel, self.receive_message_channel = trio.open_memory_channel(0)
        self.send_db_operation_channel, self.receive_db_operation_channel = trio.open_memory_channel(0)
        self.replyIntents = {}

        if not self.username:
            self.username = self.nick

        trio.run(self.connect)

    async def connect(self):
        remote_ip = socket.gethostbyname(self.host)
        log('ip of irc server is:', remote_ip)
        s = await trio.open_tcp_stream(remote_ip, self.port)
        log('connected to: ', self.host, self.port)

        async with s:
            if self.use_sasl:
                await s.send_all(("CAP REQ :sasl").encode())

            nick_cr = ('nick ' + self.nick + '\r\n').encode()
            await s.send_all(nick_cr)
            pw_cr = ('PASS' + self.password + '\r\n').encode()
            await s.send_all(pw_cr)
            usernam_cr = (
                'USER '+" ".join([self.username]*3)+' :rainbow pie \r\n').encode()
            await s.send_all(usernam_cr)

            if self.nickserv_auth:
                auth_cr = ("PRIVMSG NickServ :IDENTIFY " +
                           nick + " "+password + ' \r\n').encode()
                await s.send_all(auth_cr)

            if self.use_sasl:
                import base64
                await s.send_all(("AUTHENTICATE PLAIN").encode())
                sep = "\x00"
                b = base64.b64encode(
                    (nick + sep+nick+sep+password).encode("utf8")).decode("utf8")
                data = s.recv(4096).decode('utf-8')
                log("Server SAYS: ", data)
                await s.send_all(("AUTHENTICATE "+b).encode())
                log("PERFORMING SASL PLAIN AUTH....")
                data = s.recv(4096).decode('utf-8')
                log("Server SAYS: ", data)
                data = s.recv(4096).decode('utf-8')
                log("Server SAYS: ", data)
                await s.send_all(("CAP END").encode())


            self.s = s
            if type(self.channels) == list:
                for c in self.channels:
                    await self.join(c)
            else:
                await self.join(self.channels)
                self.channels = [self.channels]

            async with trio.open_nursery() as nursery:
                log("Listening for messages...")
                nursery.start_soon(self.run_bot_loop, s)
                nursery.start_soon(self.__message_task_loop)
                nursery.start_soon(self.__db_operation_loop)

    async def join(self, channel):
        """joins a channel.
        :param channel: str. Channel name. Include the '#', eg. "#lobby"
        """
        log("Joining", channel)
        await self.s.send_all(('JOIN '+channel+' \r\n').encode())  # chanel

    async def send_message(self, message, channel=None):
        """Sends a text message.
        :param message: Can be a str, a list of str or a IrcBot.Message object. 
        :param channel: Can be a str or a list of str. By default it is all channels the bot constructor receives. Instead of the channel name you can pass in a user nickname to send a private message.
        """
        if channel is None:
            channel = self.channels
        if type(channel) == list:
            for chan in channel:
                await self.__send_message(message, chan)
        else:
           await self.__send_message(message, channel)

    async def __send_message(self, message, channel):
        if type(message) == str:
            await self.__enqueue_message((str('PRIVMSG ' + channel) + " :" + message + ' \r\n'))
        elif type(message) == list:
            for msg in message:
                await self.__send_message(msg, channel)
        elif type(message) == Message:
            await self.__send_message(message.message, message.channel)

    async def __message_task_loop(self):
        async with self.receive_message_channel:
            async for msg in self.receive_message_channel:
                await self.__send_data(msg)

    async def __enqueue_message(self, message):
        await self.send_message_channel.send(message)

    async def __send_data(self, data):
        s = self.s
        debug("Sending: ", data)
        await trio.sleep(0)
        await s.send_all(data.encode())

    async def check_tables(self):
        debug("Cheking tables")
        for table in self.tables:
            if table._queue:
                table_copy = persistentData(table.filename, table.name, table.keys)
                table_copy._queue = table._queue
                await self.__enqueue_db_task(table_copy)
            debug("qeue", table._queue)
            table.clear()

    def fetch_tables(self):
        debug("Fetching tables")
        for table in self.tables:
            table.fetch()

    async def __enqueue_db_task(self, table):
        debug("db task", str(table._queue))
        await self.send_db_operation_channel.send(table)

    async def __db_operation_loop(self):
        async with self.receive_db_operation_channel:
            async for table in self.receive_db_operation_channel:
                for op in table._queue:
                    if op.op == dbOperation.ADD:
                        table.db.newData(op.data)
                    if op.op == dbOperation.REMOVE:
                        table.db.deleteData(op.id)
                    if op.op == dbOperation.UPDATE:
                        table.db.update(op.id, op.data)

            
    async def run_bot_loop(self, s):
        """ Starts main bot loop waiting for messages.
        """
        async with self.send_message_channel, self.send_db_operation_channel:
            async for data in s:
                data = data.decode('utf-8') 
                debug("DECODED DATA FROM SERVER: \n", 40*"-", "\n", data, 40*"-", "\n")
                async with trio.open_nursery() as nursery:
                    self.fetch_tables()
                    for msg in data.split("\r\n"):
                        nursery.start_soon(self.data_handler, s, msg)

    async def process_result(self, result, channel, sender_nick, is_private):
        if type(result) == ReplyIntent:
            if result.message:
                await self.send_message(result.message, sender_nick if is_private else channel)
                if type(result.message) == Message:
                    if result.message.channel not in self.replyIntents:
                        self.replyIntents[result.message.channel] = {}
                    debug("Saving message intent")
                    self.replyIntents[result.message.channel][result.message.sender_nick] = result
                    return

            if channel not in self.replyIntents:
                self.replyIntents[channel] = {}
            self.replyIntents[channel][sender_nick] = result
            debug("Saving basic intent")
        else:
            await self.send_message(result, sender_nick if is_private else channel)

        await self.check_tables()

    async def data_handler(self, s, data):
        nick = self.nick
        host = self.host
        if len(data) <= 1:
            return
        debug("received -> ", data)
        try:
            if data.find("PING") != -1 and len(data.split(":")) >= 3 and 'PING' in data.split(":")[2]:
                msg = str('PONG ' + data.split(':')
                          [1].split("!~")[0] + '\r\n')
                debug("ponging: ", msg)
                # await s.send_all(msg.encode())
                await self.__enqueue_message(msg)
                if data.find("PRIVMSG") != -1:
                    msg = str(f':{nick} PRIVMSG ' + data.split(':')
                              [1].split("!~")[0] + " :PONG " + data.split(" ")[-1] + '\r\n')
                    # await s.send_all(msg.encode())
                    await self.__enqueue_message(msg)
                    debug("Sending privmsg: " + msg)
                log('PONG sent \n')
                return

            elif data.strip().startswith("PING"):
                msg = str('PONG ' + host + '\r\n')
                debug("ponging: ", msg)
                # await s.send_all(msg.encode())
                await self.__enqueue_message(msg)
                log('PONG sent \n')
                return

            if len(data.split()) >= 3:
                channel = data.split()[2].strip()
                sender_nick = data.split()[0].split("!~")[0][1:].strip()
                debug("sent by:", sender_nick)
                splitter = "PRIVMSG "+channel+" :"
                msg = splitter.join(data.split(splitter)[1:]).strip()
                is_private = channel == self.nick
                channel = channel if channel != self.nick else sender_nick
                matched = False

                if channel in self.replyIntents and sender_nick in self.replyIntents[channel]:
                    result = self.replyIntents[channel][sender_nick].func(Message(channel, sender_nick, msg, is_private))
                    del self.replyIntents[channel][sender_nick]
                    await self.process_result(result, channel, sender_nick, is_private)
                    return

                for i, cmd in enumerate(utils.regex_commands): 
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg) #, flags=re.IGNORECASE)
                        if m:
                            if cmd in utils.regex_commands:
                                if is_private and not utils.regex_commands_accept_pm[i]:
                                    continue
                                await trio.sleep(0)
                                result = cmd[reg](m)
                            if result:
                                await self.process_result(result, channel, sender_nick, is_private)
                                matched = True
                                continue

                for i, cmd in enumerate(utils.regex_commands_with_message):
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg) #, flags=re.IGNORECASE)
                        if m:
                            if cmd in utils.regex_commands_with_message:
                                if is_private and not utils.regex_commands_with_message_accept_pm[i]:
                                    continue
                                debug("sending to", sender_nick)
                                if utils.regex_commands_with_message_pass_data[i]:
                                    await trio.sleep(0)
                                    result = cmd[reg](m, Message(channel, sender_nick, msg, is_private))
                                else:
                                    await trio.sleep(0)
                                    result = cmd[reg](m, Message(channel, sender_nick, msg, is_private))

                            if result:
                                await self.process_result(result, channel, sender_nick, is_private)
                                matched = True
                                continue

                for word in msg.split(" "):
                    if len(word) < 6:
                        continue
                    result = None
                    word = word.strip()
                    if word[-1] in [" ", "?", ",", ";", ":", "\\"]:
                        word = word[:-1]
                    if utils.validateUrl(word):
                        await trio.sleep(0)
                        result = utils.url_commands[-1](word)
                    if result:
                        self.send_message(result, channel)

            await self.check_tables()

        except Exception as e:
            log("ERROR IN MAINLOOP: ", e)
            logger.exception(e)

    def __del__(self):
        try:
            self.s.close()
        except:
            pass

    def close(self):
        """Stops the bot and loop if running."""
        self.__del__()

class NotAsyncIrcBot(object):
    """IrcBot."""

    def __init__(self, host, port=6665, nick="bot", channel=[], username=None, password='', nickserv_auth=False, use_sasl=False):
        """Creates a bot instance joining to the channel if specified
        :param host: str. Server hostname. ex: "irc.freenode.org"
        :param port: int. Server port. default 6665
        :param nick: str. Bot nickname. If this is set but username is not set then this will be used as the username for authentication if password is set.
        :param channel: List of strings of channels to join or string for a single channel. You can leave this empty can call .join manually.
        :param username: str. Username for authentication.
        :param password: str. Password for authentication.
        :param nickserv_auth: bool. Authenticate with 'PRIVMSG NickServ :IDENTIFY' . Should work in most servers.
        :param use_sasl: bool. Use sasl autentication. (Still not working. Don't use this!)
        """

        self.s = None
        if not username:
            username = nick
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(1)
        log('soc created |', s)
        remote_ip = socket.gethostbyname(host)
        log('ip of irc server is:', remote_ip)

        s.connect((host, port))

        log('connected to: ', host, port)

        if use_sasl:
            s.send(("CAP REQ :sasl").encode())

        nick_cr = ('nick ' + nick + '\r\n').encode()
        s.send(nick_cr)
        pw_cr = ('PASS' + password + '\r\n').encode()
        s.send(pw_cr)
        usernam_cr = (
            'USER '+" ".join([username]*3)+' :rainbow pie \r\n').encode()
        s.send(usernam_cr)

        if nickserv_auth:
            auth_cr = ("PRIVMSG NickServ :IDENTIFY " +
                       nick + " "+password + ' \r\n').encode()
            s.send(auth_cr)

        if use_sasl:
            import base64
            s.send(("AUTHENTICATE PLAIN").encode())
            sep = "\x00"
            b = base64.b64encode(
                (nick + sep+nick+sep+password).encode("utf8")).decode("utf8")
            data = s.recv(4096).decode('utf-8')
            log("Server SAYS: ", data)
            s.send(("AUTHENTICATE "+b).encode())
            log("PERFORMING SASL PLAIN AUTH....")
            data = s.recv(4096).decode('utf-8')
            log("Server SAYS: ", data)
            data = s.recv(4096).decode('utf-8')
            log("Server SAYS: ", data)
            s.send(("CAP END").encode())

        self.s = s
        self.nick = nick
        self.password = password
        self.username = username
        self.host = host
        self.port = port

        if type(channel) == list:
            self.channels = channel
            for c in channel:
                self.join(c)
        else:
            self.channels = [channel]
            self.join(channel)

    def join(self, channel):
        """joins a channel.
        :param channel: str. Channel name. Include the '#', eg. "#lobby"
        """
        self.s.send(('JOIN '+channel+' \r\n').encode())  # chanel

    def send_message(self, message, channel=None):
        """Sends a text message.
        :param message: Can be a str, a list of str or a IrcBot.Message object. 
        :param channel: Can be a str or a list of str. By default it is all channels the bot constructor receives. Instead of the channel name you can pass in a user nickname to send a private message.
        """
        if channel is None:
            channel = self.channels
        if type(channel) == list:
            for chan in channel:
                self.__send_message(message, chan)
        else:
            self.__send_message(message, channel)

    def __send_message(self, message, channel):
        s = self.s
        if type(message) == str:
            s.send((str('PRIVMSG ' + channel) + " :" + message + ' \r\n').encode())
        elif type(message) == list:
            for msg in message:
                self.__send_message(msg, channel)
        elif type(message) == Message:
            self.__send_message(message.message, channel)

    def run(self):
        """ Starts main bot loop waiting for messages.
        """
        asyncio.run(self.run_server_loop())

    async def run_server_loop(self):
        s = self.s
        while 1:
            data = s.recv(BUFFSIZE).decode('utf-8')
            await self.data_handler(data)

    async def data_handler(self, data):
        s = self.s
        nick = self.nick
        host = self.host

        if len(data) <= 1:
            return
        debug("received -> ", data)
        try:
            if data.find("PING") != -1 and len(data.split(":")) >= 3 and 'PING' in data.split(":")[2]:
                msg = str('PONG ' + data.split(':')
                          [1].split("!~")[0] + '\r\n')
                debug("ponging: ", msg)
                s.send(msg.encode())
                if data.find("PRIVMSG") != -1:
                    msg = str(f':{nick} PRIVMSG ' + data.split(':')
                              [1].split("!~")[0] + " :PONG " + data.split(" ")[-1] + '\r\n')
                    s.send(msg.encode())
                    debug("Sending privmsg: " + msg)
                log('PONG sent \n')
                return

            elif data.strip().startswith("PING"):
                msg = str('PONG ' + host + '\r\n')
                debug("ponging: ", msg)
                s.send(msg.encode())
                log('PONG sent \n')
                return

            if len(data.split()) >= 3:
                channel = data.split()[2]
                sender_nick = data.split()[0].split("!~")[0][1:]
                debug("sent by:", sender_nick)
                splitter = "PRIVMSG "+channel+" :"
                msg = splitter.join(data.split(splitter)[1:]).strip()
                matched = False

                is_private = channel == self.nick
                for i, cmd in enumerate(utils.regex_commands): 
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg) #, flags=re.IGNORECASE)
                        if m:
                            if cmd in utils.regex_commands:
                                if is_private and not utils.regex_commands_accept_pm[i]:
                                    continue
                                result = cmd[reg](m)
                            if result:
                                self.send_message(result, sender_nick if is_private else channel)
                                matched = True
                                continue

                for i, cmd in enumerate(utils.regex_commands_with_message):
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg) #, flags=re.IGNORECASE)
                        if m:
                            if cmd in utils.regex_commands_with_message:
                                if is_private and not utils.regex_commands_with_message_accept_pm[i]:
                                    continue
                                debug("sending to", sender_nick)
                                result = cmd[reg](m, Message(self, channel, sender_nick, msg, is_private))
                            if result:
                                self.send_message(result, sender_nick if is_private else channel)
                                matched = True
                                continue

                for word in msg.split(" "):
                    if len(word) < 6:
                        continue
                    result = None
                    word = word.strip()
                    if word[-1] in [" ", "?", ",", ";", ":", "\\"]:
                        word = word[:-1]
                    if utils.validateUrl(word):
                        result = utils.url_commands[-1](word)
                    if result:
                        self.send_message(result, channel)
                

        except Exception as e:
            log("ERROR IN MAINLOOP: ", e)
            logger.exception(e)

    def __del__(self):
        try:
            self.s.close()
        except:
            pass

    def close(self):
        """Stops the bot and loop if running."""
        self.__del__()
