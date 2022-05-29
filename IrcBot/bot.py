# -*- coding: utf-8 -*-

#########################################################################
#  Matheus Fillipe -- 13, December of 2020                              #
#                                                                       #
#########################################################################
#  Description: Simple bot framework that will handle the very basics   #
# of the IRC and DCC protocol                                           #
#                                                                       #
#########################################################################
#  Depends on: `pip3 install -r requirements.txt`                       #
#                                                                       #
#########################################################################


import inspect
import random
import re
import socket
from copy import copy, deepcopy
from functools import partial
from math import ceil
from pathlib import Path

import trio
import trio_asyncio
from cachetools import TTLCache

from IrcBot import dcc, utils
from IrcBot.message import Message, ReplyIntent
from IrcBot.sqlitedb import DB
from IrcBot.utils import debug, log, logger

Message = Message
ReplyIntent = ReplyIntent

BUFFSIZE = 2048
MAX_MESSAGE_LEN = 410


class BotConnectionError(Exception):
    pass


class Color(object):
    """Colorcodes enum."""

    esc = "\003"
    white = "00"
    black = "01"
    navy = "02"
    green = "03"
    red = "04"
    maroon = "05"
    purple = "06"
    orange = "07"
    yellow = "08"
    light_green = "09"
    teal = "10"
    cyan = "11"
    blue = "12"
    magenta = "13"
    gray = "14"
    light_gray = "15"

    COLORS = [
        "00",
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
    ]

    def __init__(self, text, fg=white, bg=None):
        if bg is not None:
            self.text = "{}{},{}{}".format(self.esc, fg, bg, text)
        else:
            self.text = "{}{}{}".format(self.esc, fg, text)
        self.str = self.text + Color.esc

    @classmethod
    def random(cls):
        return random.choice(cls.COLORS)

    @classmethod
    def colors(cls):
        """Returns the color names."""
        return [
            k
            for k in Color.__dict__
            if not (
                k.startswith("_")
                or k in ["esc", "COLORS", "colors", "getcolors", "random"]
            )
        ]

    def __str__(self):
        return self.str


class dbOperation(object):
    ADD = 1
    UPDATE = 0
    REMOVE = -1

    def __init__(self, data={}, id={}, op=UPDATE):
        self.data = data
        self.id = id
        self.op = op


class tempData(object):
    def __init__(self):
        """Initializes a temporary data object that can be retrieved from the
        same user and channel."""
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
        """push. Add new items to the table.

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
        assert type(id) == int, "id needs to be an int!"
        self._queue.append(dbOperation(id=id, op=dbOperation.REMOVE))

    def update(self, id, item):
        """update.

        :param id: id of item to update, change.
        :param item: New item to replace with. This dict doesn't need to have all keys/columns, just the ones to be changed.
        """
        assert type(item) == dict, "item must be either list or dict"
        assert type(id) == int, "id needs to be an int!"
        self._queue.append(dbOperation(id=id, data=item, op=dbOperation.UPDATE))

    def clear(self):
        """Clear all the proposed modifications."""
        self._queue = []


class IrcBot(object):
    """IrcBot."""

    def __init__(
        self,
        host,
        port=6667,
        nick="bot",
        channels=None,
        username=None,
        password="",
        server_password="",
        use_sasl=False,
        use_ssl=False,
        delay=False,
        accept_join_from=None,
        tables=None,
        custom_handlers=None,
        strip_messages=True,
        dcc_ports=None,
        dcc_host=False,
        dcc_announce_host=None
    ):
        """Creates a bot instance joining to the channel if specified.

        :param host: str. Server hostname. ex: "irc.freenode.org"
        :param port: int. Server port. default 6665
        :param nick: str. Bot nickname. If this is set but username is not set then this will be used as the username for authentication if password is set.
        :param channel: List of strings of channels to join or string for a single channel. You can leave this empty can call .join manually.
        :param username: str. Username for authentication.
        :param password: str. Password for authentication.
        :param server_password: str. Authenticate with the server.
        :param use_sasl: bool. Use sasl autentication. (Still not working. Don't use this!)
        :param delay: int. Delay after nickserv authentication
        :param accept_join_from: str. Who to accept invite command from ([])
        :param tables: List of persistentData to be registered on the bot.
        :param strip_messages: bool. Should messages be stripped (for *_with_message decorators)
        :param custom_handlers:{type: function, ...} Dict with function values to be called to handle custom server messages. Possible types (keys) are:
            type             kwargs
            'privmsg' -> {'nick', 'channel', 'text'}
            'ping' -> {'ping'}
            'names' -> {'channel', 'names'}
            'channel' -> {'channel', 'channeldescription'}
            'join' -> {'nick', 'channel'}
            'quit' -> {'nick', 'text'}
            'part' -> {'nick', 'channel'}
            'dccsend' -> {'nick', 'filename', 'ip', 'port', 'size', 'token'}
        :param dcc_ports: list of ports numbers to use for dcc
        :param dcc_host: ip address to bind to for passive dcc file receiving and dcc send.
        :param dcc_announce_host: ip address to announce for passive dcc file receiving and dcc send.
        type: str ip or None to bind to the wildcard address. Default will try to guess (LAN IP)
        """

        if channels is None:
            channels = []
        if accept_join_from is None:
            accept_join_from = []
        if tables is None:
            tables = []
        if custom_handlers is None:
            custom_handlers = {}
        if dcc_ports is None:
            dcc_ports = list(range(4990, 5000))
        if dcc_announce_host is None:
            dcc_announce_host = dcc_host

        self.nick = nick
        self.password = password
        self.server_password = server_password
        self.username = username
        self.host = host
        self.port = port
        self.channels = channels
        self.use_sasl = use_sasl
        self.use_ssl = use_ssl
        self.tables = tables
        self.delay = delay
        self.accept_join_from = accept_join_from
        self.custom_handlers = utils.custom_handlers
        self.custom_handlers.update(custom_handlers)
        self.strip_messages = strip_messages
        self.dcc_ports = dcc_ports
        self.dcc_host = dcc_host
        self.dcc_announce_host = dcc_announce_host
        self._dcc_busy_ports = {}
        if self.dcc_host is False:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.dcc_host = s.getsockname()[0]

            s.close()

        self._awaiting_messages = {}

        self.connected = False
        self.server_channels = {}
        self.channel_names = {}

        if utils.arg_commands_with_message:
            new_commands = deepcopy(utils._defined_command_dict)
            new_commands.update(utils.arg_commands_with_message)
            utils.setCommands(new_commands, prefix=utils.command_prefix)

        (
            self.send_message_channel,
            self.receive_message_channel,
            self.send_db_operation_channel,
            self.receive_db_operation_channel,
        ) = [None] * 4
        self.replyIntents = {}

        self.ping_delay = 30  # seconds

        self.is_running_with_callback = False
        self.async_callback = None
        self.retry_connecting = False
        self.nursery = None

        if not self.username:
            self.username = self.nick

    async def _mainloop(self, async_callback=None):
        self.is_running_with_callback = True if async_callback else None
        self.async_callback = async_callback
        while True:
            (
                self.send_message_channel,
                self.receive_message_channel,
            ) = trio.open_memory_channel(0)
            (
                self.send_db_operation_channel,
                self.receive_db_operation_channel,
            ) = trio.open_memory_channel(0)
            try:
                async with trio.open_nursery() as nursery:
                    self.nursery = await nursery.start(self._main_task)
            except (BotConnectionError, socket.gaierror):
                log(f"Attempting to reconnect in {self.ping_delay}...")
                await trio.sleep(self.ping_delay)

    async def _main_task(self, task_status=trio.TASK_STATUS_IGNORED):
        async with trio.open_nursery() as nursery:
            with trio.CancelScope() as scope:
                task_status.started(scope)
                if self.async_callback is None:
                    self.nursery = nursery.start_soon(self.connect)
                else:
                    self.nursery = nursery.start_soon(self.start_with_callback)

    def runWithCallback(self, async_callback):
        """starts the bot with an async callback.

        Useful if you want to use bot.send without user interaction.
        param: async_callback: async function to be called.
        """
        trio_asyncio.run(self._mainloop, async_callback)

    async def start_with_callback(self):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.connect)
            nursery.start_soon(self._wait_and_async_cb_task)

    async def _wait_and_async_cb_task(self):
        while not self.connected:
            await trio.sleep(1)
        await self.async_callback(self)

    def run(self, async_callback=None):
        """Simply starts the bot.

        param: async_callback: async function to be called.
        """
        trio_asyncio.run(self._mainloop, async_callback)

    async def sleep(self, time):
        """Waits for time.

        Asynchronous wrapper for trip.sleep
        """
        await trio.sleep(time)

    async def ping_confirmation(self, s):
        MAX = 10
        c = 0
        log("AWAITING PING CONFIRMATION.....")
        async for data in s:
            data = data.decode("utf-8")
            for msg in data.split("\r\n"):
                debug("RECV --------- " + msg)
                if c > MAX:
                    return
                if "001 " + self.nick + " :" in msg:
                    return
                if data.find("PING") != -1 and len(data.split(":")) >= 2:
                    msg = str("PONG :" + data.split(":")[-1])
                    debug("Registration pong: ", msg)
                    await s.send_all(msg.encode())
                    return
                c += 1

    async def connect(self):
        remote_ip = socket.gethostbyname(self.host)
        log("ip of irc server is:", remote_ip)
        if self.use_ssl:
            log("Using SSL connection")
            import ssl

            ssl_context = ssl.SSLContext()
            s = await trio.open_ssl_over_tcp_stream(
                remote_ip, self.port, https_compatible=True, ssl_context=ssl_context
            )
        else:
            s = await trio.open_tcp_stream(remote_ip, self.port)
        log("connected to: ", self.host, self.port)

        async with s:
            if self.use_sasl:
                await s.send_all(("CAP REQ :sasl").encode())

            if self.server_password:
                pw_cr = ("PASS " + self.server_password + "\r\n").encode()
                await s.send_all(pw_cr)

            nick_cr = ("NICK " + self.nick + "\r\n").encode()
            await s.send_all(nick_cr)

            usernam_cr = (
                "USER " + " ".join([self.username] * 3) + " :" + self.nick + " \r\n"
            ).encode()
            await s.send_all(usernam_cr)

            ping_confirmed = False
            try:
                with trio.fail_after(5):
                    await self.ping_confirmation(s)
                    ping_confirmed = True
                    log("SUBMITTING PING COOKIE CONFIRMATION")
            except trio.TooSlowError:
                log("NO PING CONFIRMATION!!!!!")

            if self.password:
                log("IDENTIFYING")
                auth_cr = (
                    "PRIVMSG NickServ :IDENTIFY " + self.password + "\r\n"
                ).encode()
                await s.send_all(auth_cr)

            if self.delay:
                await trio.sleep(self.delay)
            if self.use_sasl:
                import base64

                await s.send_all(("AUTHENTICATE PLAIN").encode())
                sep = "\x00"
                b = base64.b64encode(
                    (self.nick + sep + self.nick + sep + self.password).encode("utf8")
                ).decode("utf8")
                data = s.recv(4096).decode("utf-8")
                log("Server SAYS: ", data)
                await s.send_all(("AUTHENTICATE " + b).encode())
                log("PERFORMING SASL PLAIN AUTH....")
                data = s.recv(4096).decode("utf-8")
                log("Server SAYS: ", data)
                data = s.recv(4096).decode("utf-8")
                log("Server SAYS: ", data)
                await s.send_all(("CAP END").encode())

            self.s = s
            if type(self.channels) == list:
                for c in self.channels:
                    await self.join(c)
            else:
                await self.join(self.channels)
                self.channels = [self.channels]

            self.connected = True
            async with trio.open_nursery() as nursery:
                log("Listening for messages...")
                nursery.start_soon(self.run_bot_loop, s)
                nursery.start_soon(self.message_task_loop)
                if self.tables:
                    nursery.start_soon(self.db_operation_loop)
                nursery.start_soon(self.check_reconnect)

    async def check_reconnect(self):
        await self.sleep(self.ping_delay)
        while True:
            if not self.connected:
                break
            self.connected = False
            await self.send_raw(f"PING {self.host}\r\n")
            await self.sleep(self.ping_delay)
        log("Disconnected!! Attempting to reconnect...")
        await self.s.aclose()
        raise BotConnectionError("Bot Disconnected: No ping response from server")
        # self.nursery.cancel()

    async def send_raw(self, data: str):
        """send_raw. Sends a string to the irc server.

        :param data:
        :type data: str
        """
        if not data.endswith("\r\n"):
            data += "\r\n"
        await self._enqueue_message(data)

    async def join(self, channel):
        """joins a channel.

        :param channel: str. Channel name. Include the '#', eg. "#lobby"
        """
        log("Joining", channel)
        await self.s.send_all(("JOIN " + channel + " \r\n").encode())  # chanel

    async def list_channels(self):
        """list_channels of the irc server.

        They will be available as a list of strings under:
        bot.server_channels
        """
        await self._send_data("LIST")
        await self.sleep(1)
        return self.server_channels

    async def list_names(self, channel):
        """Lists users nicks in channel.

        Also check bot.channel_names for a non sanitized version(like starting with ~ & % @ + for operators, moderators, etc; if you want to detect them)

        :param channel:str channel name
        """
        # await self._send_data(f"NAMES {channel}")
        # await self.sleep(2)
        special_symbols = [
            "~",
            "&",
            "%",
            "@",
            "+",
        ]
        names = self.channel_names[channel]
        names = [
            name[1:] if any([name.startswith(s) for s in special_symbols]) else name
            for name in names
        ]
        return names

    async def send_message(self, message, channel=None):
        """Sends a text message. The message will be enqueued and sent whenever
        the messaging loop arrives on it.

        :param message: Can be a str, a list of str or a IrcBot.Message object.
        :param channel: Can be a str or a list of str. By default it is all channels the bot constructor receives. Instead of the channel name you can pass in a user nickname to send a private message.
        """
        if channel is None:
            channel = self.channels

        if type(channel) == list and type(message) != Message:
            for chan in channel:
                await self._send_message(message, chan)
        else:
            await self._send_message(message, channel)

    async def _send_message(self, message, channel):
        if type(message) == str:
            message = message.replace("\n", "    ")
            message = message.replace("\r", "")
            await self._enqueue_message(
                (str("PRIVMSG " + channel) + " :" + message + " \r\n")
            )
        elif type(message) == Color:
            await self._send_message(message.str, channel)
        elif type(message) == list:
            for msg in message:
                await self._send_message(msg, channel)
        elif type(message) == Message:
            await self._send_message(message.message, message.channel)

    async def message_task_loop(self):
        async with self.receive_message_channel:
            async for msg in self.receive_message_channel:
                await self._send_data(msg)

    async def _enqueue_message(self, message):
        await self.send_message_channel.send(message)

    async def _send_data(self, data):
        s = self.s
        debug("Sending: ", f"{data=}")
        await trio.sleep(0)
        await s.send_all(data.encode())

    async def check_tables(self):
        debug("Checking tables")
        for table in self.tables:
            if table._queue:
                table_copy = persistentData(table.filename, table.name, table.keys)
                table_copy._queue = table._queue
                await self._enqueue_db_tsk(table_copy)
            debug("qeue", table._queue)
            table.clear()

    def fetch_tables(self):
        debug("Fetching tables")
        for table in self.tables:
            table.fetch()

    async def _enqueue_db_tsk(self, table):
        debug("db task", str(table._queue))
        await self.send_db_operation_channel.send(table)

    async def db_operation_loop(self):
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
        """Starts main bot loop waiting for messages."""
        async with trio.open_nursery() as nursery:
            async with self.send_message_channel, self.send_db_operation_channel:
                async for data in s:
                    data = data.decode("utf-8")
                    debug(
                        "\n>>>> DECODED DATA FROM SERVER: \n",
                        60 * "-",
                        "\n",
                        f"{data=}\n",
                        60 * "-",
                        "\n",
                    )
                    self.fetch_tables()
                    for msg in data.split("\r\n"):
                        nursery.start_soon(self.data_handler, s, msg)

    async def process_result(self, result, channel, sender_nick, is_private):
        if type(result) == ReplyIntent:
            if result.message:
                await self.send_message(
                    result.message, sender_nick if is_private else channel
                )
                if type(result.message) == Message:
                    if result.message.channel not in self.replyIntents:
                        self.replyIntents[result.message.channel] = {}
                    debug("Saving message intent")
                    self.replyIntents[result.message.channel][
                        result.message.sender_nick
                    ] = result
                    return

            if channel not in self.replyIntents:
                self.replyIntents[channel] = {}
            self.replyIntents[channel][sender_nick] = result
            debug("Saving basic intent")
        else:
            await self.send_message(result, sender_nick if is_private else channel)

        if self.tables:
            await self.check_tables()

    async def _start_dcc_server(
        self, server_type: dcc.DccServer, dcc_data, progress_callback=None
    ):
        filename = dcc_data["filename"]
        is_sender = dcc.DccServer.SEND == server_type
        ip = dcc_data["ip"]
        port = dcc_data["port"]
        size = Path(filename).stat().st_size if is_sender else dcc_data["size"]
        success = False

        async def handler(client_stream):
            nonlocal success
            try:
                s_list = dcc.get_chunk_sizes_list(size, BUFFSIZE)
                log(f"DCC {'SENDING' if is_sender else 'RECEIVING'} FILE BYTES")
                total_b = 0
                last_ = 0
                has_callback = callable(progress_callback)
                log(f"{has_callback}")

                async def progress_handler():
                    nonlocal last_
                    if not has_callback:
                        return
                    # TODO maybe there is a better way than just call progress on each 1% ?
                    current_progress = ceil(total_b / size * 100)
                    if current_progress <= last_:
                        return
                    last_ = current_progress
                    await progress_callback(self, total_b / size)

                with open(filename, "rb") if is_sender else open(filename, "wb") as f:
                    with trio.CancelScope() as cancel_scope:
                        self._dcc_busy_ports[port]["scopes"].append(cancel_scope)
                        cancel_scope.shield = True
                        if is_sender:
                            for bsize in s_list:
                                await client_stream.send_all(f.read(bsize))
                                total_b += bsize
                                await progress_handler()

                        else:
                            while total_b < size:
                                bytes_read = await client_stream.receive_some()
                                if not bytes_read:
                                    break
                                f.write(bytes_read)
                                total_b += len(bytes_read)
                                await progress_handler()

                await self.sleep(1)
                # await client_stream.aclose()
                success = True
                if has_callback:
                    await progress_callback(self, 1)
                dcc_scope.cancel()
            except trio.BrokenResourceError:
                log("DCC SEND BrokenResourceError")
            except BrokenPipeError:
                log("DCC SEND BrokenPipeError")
            except ConnectionResetError:
                log("DCC SEND ConnectionResetError")
            log("DCC SEND FINISHED")
            log(f"Sent {total_b} bytes")

        with trio.move_on_after(120) as dcc_scope:
            self._dcc_busy_ports[port] = {
                "scopes": [dcc_scope],
                **dcc_data,
                "type": server_type,
            }
            async with trio.open_nursery() as nursery:
                await nursery.start(partial(trio.serve_tcp, host=self.dcc_host), handler, port)
        log(f"Finished dcc server with {success=}")
        return success

    def _dcc_get_available_port(self, take_port=True):
        for pt in self.dcc_ports:
            if pt not in self._dcc_busy_ports and dcc.is_port_available(
                self.dcc_host, pt
            ):
                if take_port:
                    self._dcc_busy_ports[pt] = None
                return pt

    def _dcc_free_port(self, port):
        if port in self._dcc_busy_ports:
            return self._dcc_busy_ports.pop(port)

    async def dcc_send(self, nick, filename, port=None, progress_callback=None):
        """Starts the tcp server for sending a file and sends the ctcp message
        to nick.

        :param nick: Nick to offer the file to
        :type str:
        :param filename: File absolute path
        :type str:
        :param port: Port to use or 0 to let the kernel pick an open port. Default will choose the first available port in dcc_ports.
        :type int:
        :param progress_callback: async function to be called after each 1 % of data is sent. Must accept the bot and float that indicates the transfer progress.
        """
        if port is None:
            port = self._dcc_get_available_port()
        if port is None:
            log("ERROR! No ports available for dcc!")
            await self.dcc_reject(dcc.DccServer.GET, nick, filename)
            raise BaseException("No available ports for dcc send")

        size = Path(filename).stat().st_size
        message = {
            "nick": nick,
            "filename": filename,
            "ip": self.dcc_announce_host,
            "port": port,
            "size": size,
        }
        await self._dcc_send(message)
        send_result = await self._start_dcc_server(
            dcc.DccServer.SEND, message, progress_callback
        )
        if not send_result:
            await self.dcc_reject(dcc.DccServer.GET, nick, filename)
        self._dcc_free_port(port)
        return send_result

    async def dcc_get(self, download_path, m, progress_callback=None):
        """Downloads file being offered by a nick using the dcc protocol.
        Supports passive protocol.

        :param download_path: Path to download file into
        :type download_path: str
        :param m: match from custom_handler('dccsend') or dcc.DccHelper instance
        :type Union(DccHelper, dict):
        :param progress_callback: async function to be called after each 1 % of data is sent. Must accept the bot and float that indicates the transfer progress.
        :returns bool: Indicating download success or failure
        """
        helper = None
        if isinstance(m, dcc.DccHelper):
            message = m.to_message()
            helper = m
        else:
            message = m
            helper = dcc.DccHelper(**m)

        # DCC PASSIVE GET SERVER
        if helper.is_passive:
            ip = self.dcc_announce_host
            port = self._dcc_get_available_port()
            log(f"{message.get('nick')=}")
            message.update({"ip": ip, "port": port})
            if port is None:
                log("ERROR! No ports available for dcc!")
                await self.dcc_reject(dcc.DccServer.SEND, m=message)
                return
            await self._dcc_send(message)
            m.update({"filename": download_path})
            if not await self._start_dcc_server(
                dcc.DccServer.GET, message, progress_callback
            ):
                await self.dcc_reject(dcc.DccServer.GET, m=message)
            self._dcc_free_port(port)
            return True

        # DCC GET CLIENT
        try:
            s = await trio.open_tcp_stream(message["ip"], message["port"])
        except:
            return
        total_b = 0
        size = message["size"]
        last_ = 0
        log("DCC GET CLIENT")
        log(f"downloading {size} bytes")
        with open(download_path, "wb") as f:
            try:
                async for data in s:
                    total_b += len(data)
                    f.write(data)

                    # TODO maybe there is a better way than just call progress on each 1% ?
                    if total_b >= size:
                        break
                    current_progress = ceil(total_b / size * 100)
                    if current_progress <= last_:
                        continue
                    last_ = current_progress
                    if callable(progress_callback):
                        await progress_callback(self, total_b / size)

                log("DCC GET FINISHED")
                await s.aclose()
                if callable(progress_callback):
                    await progress_callback(self, 1)

            except trio.BrokenResourceError:
                log("DCC SEND BrokenResourceError")
                return
            except BrokenPipeError:
                log("DCC SEND BrokenPipeError")
                return
            except ConnectionResetError:
                log("DCC SEND ConnectionResetError")
                return

        return True

    async def dcc_reject(
        self, dcc_type: dcc.DccServer, nick=None, filename=None, m=None
    ):
        """Sends a DCC REJECT to nick for the offered filename or receiving
        filename.

        :param dcc_type: wither DccServer.GET or DccServer.SEND
        :type dcc_type: dcc.DccServer
        :param nick: Nick of the user.
        :type nick: str
        :param filename: File Name
        :type filename: str
        :param m: Match dictionary from e.g. custom_handler("dccsend")
        """
        if [nick, filename] == [None, None] and m is None:
            raise BaseException("Must pass Either nick and filename or m")
        if [nick, filename] == [None, None]:
            nick = m["nick"]
            filename = m["filename"]

        await self.send_raw(
            f"NOTICE {nick} :\x01DCC REJECT {dcc_type.name} {Path(filename).name}\x01\r\n"
        )

    async def _dcc_send(self, message):
        await self.send_raw(
            f'PRIVMSG {message["nick"]} :\x01DCC SEND {Path(message["filename"]).name} {dcc.ip_quad_to_num(message["ip"])} {message["port"]} {message["size"]}{" " + str(message["token"]) if message.get("token") else ""}\x01\r\n'
        )

    def _wait_msg_key(self, type, nick):
        if nick is None:
            nick = "#"
        return f"{type}_#{nick}#"

    def jls_extract_def(self, wait_for):
        return wait_for

    async def wait_for(
        self,
        type: str,
        from_nick: str = None,
        timeout: int = 0,
        cache_ttl: int = 0,
        filter_func=None,
    ) -> dict:
        """Will wait for a response of type check custom handler types from
        nick. Will return the message dict.

        :param type: Message type (dccsend, dccreject, privmsg, ping, channel, names)
        :type type: str
        :param from_nick: Optional nick to match from
        :type from_nick: str
        :param timeout: Seconds to timeout and return None. Defaults to wait forever. It is very recommendable to pass a number to this even if high.
        :type timeout: int
        :param cache_ttl: if <= 0 will not cache the result, if > 0 will be the time in seconds to cache the result for the specified request.
        :type int:
        :param filter_func: Function to filter on taking the message as argument and return bool. Must be non async.
        :type callable:
        :return dict: Empty dict if timeout occurs
        """

        # Format: self._awaiting_messages[key][idx] --> {message: msg, info: ...}
        use_cache = cache_ttl and cache_ttl > 0
        key = self._wait_msg_key(type, from_nick)
        idx = random.randint(0, 1000000)
        if (
            use_cache
            and key in self._awaiting_messages
            and "cache" in self._awaiting_messages[key]
        ):

            message = self._awaiting_messages[key]["cache"]
            try:
                if not callable(filter_func) or (
                    callable(filter_func) and filter_func(message)
                ):
                    debug(f"WAIT FOR: using cached result for {from_nick}")
                    return message
            except Exception as e:
                log(
                    f"ATTENTION! Error in wait_for -> your {filter_func=} failed with {str(e)}"
                )

        if key not in self._awaiting_messages:
            self._awaiting_messages[key] = {}
        if use_cache:
            log("WAIT FOR: creating cache for {key=}")
            self._awaiting_messages[key] = TTLCache(maxsize=8192, ttl=cache_ttl)
        self._awaiting_messages[key][idx] = {}
        self._awaiting_messages[key][idx]["message"] = {}
        self._awaiting_messages[key][idx]["filter_func"] = filter_func
        self._awaiting_messages[key][idx]["type"] = type
        self._awaiting_messages[key][idx]["timeout"] = timeout
        self._awaiting_messages[key][idx]["nick"] = from_nick
        self._awaiting_messages[key][idx]["cache_ttl"] = cache_ttl
        self._awaiting_messages[key][idx]["use_cache"] = use_cache
        send_stream, receive_stream = trio.open_memory_channel(0)
        self._awaiting_messages[key][idx]["send_stream"] = send_stream

        async def await_message():
            async for msg in receive_stream:
                break
            await send_stream.aclose()
            await receive_stream.aclose()
            self._awaiting_messages[key][idx]["message"] = msg
            if use_cache and "cache" not in self._awaiting_messages[key]:
                self._awaiting_messages[key]["cache"] = msg

        if timeout and timeout > 0:
            with trio.move_on_after(timeout):
                await await_message()
        else:
            await await_message()

        msg = self._awaiting_messages.get(key)
        if msg:
            msg = msg.get(idx)
        else:
            return {}
        if not use_cache:
            self._awaiting_messages[key].pop(idx)
        return msg["message"] if msg else {}

    # MAIN DATA RECEIVING HANDLER
    async def data_handler(self, s, data):
        nick = self.nick
        host = self.host
        self.connected = True

        IRC_P = {
            # DCC
            r"^:(\S+)!.*\s+PRIVMSG\s+"
            + self.nick
            + r"\s+:"
            + "\x01"
            + r"DCC\s+"
            + r"SEND\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
            + "\x01"
            + r"\s*$": lambda g: {
                "type": "dccsend",
                "nick": g[1],
                "filename": g[2],
                "ip": dcc.ip_num_to_quad(g[3]),
                "port": int(g[4]),
                "size": int(g[5]),
                "token": int(g[6]),
            },
            r"^:(\S+)!.*\s+NOTICE\s+"
            + self.nick
            + r"\s+:"
            + "\x01"
            + r"DCC\s+"
            + r"REJECT\s+(\S+)\s+(\S+)\s*"
            + "\x01"
            + r"\s*$": lambda g: {
                "type": "dccreject",
                "nick": g[1],
                "reject": g[2],
                "filename": g[3],
            },
            r"^:(\S+)!.*\s+PRIVMSG\s+"
            + self.nick
            + r"\s+:"
            + "\x01"
            + r"DCC\s+"
            + r"SEND\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)"
            + "\x01"
            + r"\s*$": lambda g: {
                "type": "dccsend",
                "nick": g[1],
                "filename": g[2],
                "ip": dcc.ip_num_to_quad(g[3]),
                "port": int(g[4]),
                "size": int(g[5]),
                "token": None,
            },
            # IRC
            r"^:(.*)!.*PRIVMSG (\S+) :(.*)$": lambda g: {
                "type": "privmsg",
                "nick": g.group(1),
                "channel": g.group(2),
                "text": g.group(3),
            },
            r"^:(.*)!.*NOTICE (\S+) :(\S+) (.*)$": lambda g: {
                "type": "notice",
                "nick": g.group(1),
                "channel": g.group(2),
                "notice": g.group(3),
                "text": g.group(4),
            },
            r"^\s*PING \s*"
            + self.nick
            + r"\s*$": lambda g: {"type": "ping", "ping": self.nick},
            r"^:\S+\s+PONG\s+\S+\s+:(\S+).*$": lambda g: {"type": "pong", "nick": g[1]},
            r"^:\S* 353 "
            + self.nick
            + r" = (\S+) :(.*)\s*$": lambda g: {
                "type": "names",
                "channel": g.group(1),
                "names": g.group(2).split(),
            },
            r"^:\S* 322 "
            + self.nick
            + r" (\S+) (\d+) :(.+)\s*$": lambda g: {
                "type": "channel",
                "channel": g.group(1),
                "chandescription": g.group(3),
            },
            r"^:(.+)!.* QUIT :(.*)\s*$": lambda g: {
                "type": "quit",
                "nick": g[1],
                "text": g[2],
            },
            r"^:(.+)!.* JOIN :?(\S+)\s*$": lambda g: {
                "type": "join",
                "nick": g[1],
                "channel": g[2],
            },
            r"^:(.+)!.* PART (\S+)( :.*\s*)?$": lambda g: {
                "type": "part",
                "nick": g[1],
                "channel": g[2],
                "text": g[3],
            },
            r"^:(.+) 433 (\S*) (\S*) :(.*)\s*$": lambda g: {
                "type": "nickinuse",
                "reply": g,
            },
            r"^:"
            + self.nick
            + r"!.* QUIT (.*)\s*$": lambda g: {
                "type": "selfquit",
                "reply": f"*{g[1]}: You have quit*",
            },
            r"^:(\S+)!.* NICK :?(\S+)\s*$": lambda g: {
                "type": "nickchange",
                "nick": g[1],
                "nickchange": g[2],
            },
        }

        message = None
        for pattern in IRC_P:
            g = re.match(pattern, data)
            if g:
                message = IRC_P[g.re.pattern](g)
                break

        if message:
            debug(f"{message['type']=}")
            if message["type"] in self.custom_handlers:
                m_copy = copy(message)
                m_copy.pop("type")
                result = await self._call_cb(
                    self.custom_handlers[message["type"]], **m_copy
                )
                if result:
                    await self.send_message(result)

            # Match wait_for
            akey = self._wait_msg_key(message["type"], message.get("nick"))
            debug(f"{self._awaiting_messages=}")
            if self._awaiting_messages.get(akey) is not None:
                for idx in self._awaiting_messages[akey]:
                    if idx == "cache":
                        continue
                    filter_func = self._awaiting_messages[akey][idx]["filter_func"]
                    use_cache = self._awaiting_messages[akey][idx]["use_cache"]
                    try:
                        if callable(filter_func) and not filter_func(message):
                            continue
                    except Exception as e:
                        log(
                            f"ATTENTION! Error in wait_for -> your {filter_func=} failed with {str(e)}"
                        )
                        continue
                    debug(
                        f"Found match for awaiting message {idx=} {self._awaiting_messages[akey][idx]=}"
                    )
                    debug(f"{message=}")
                    try:
                        await self._awaiting_messages[akey][idx]["send_stream"].send(
                            message
                        )
                    except trio.ClosedResourceError:
                        continue
                    if not use_cache:
                        return

            if message["type"] == "dccreject":
                items = self._dcc_busy_ports.items()
                free_ports = []
                for port, dcc_data in items:
                    if (
                        message["nick"] == dcc_data["nick"]
                        and message["filename"] == Path(dcc_data["filename"]).name
                        and message["reject"] == dcc_data["type"].name
                    ):
                        log(f"DCC REJECT: canceling f{dcc_data=}")
                        free_ports.append(port)
                        for scope in dcc_data["scopes"][::-1]:
                            scope.cancel()
                for port in free_ports:
                    dcc_data = self._dcc_free_port(port)

            if message["type"] == "names":
                self.channel_names[message["channel"]] = message["names"]
                return

            if message["type"] == "nickchange":
                for channel in self.channel_names:
                    if message["nick"] in self.channel_names[channel]:
                        self.channel_names[channel].remove(message["nick"])
                    if message["nickchange"] not in self.channel_names[channel]:
                        self.channel_names[channel].append(message["nickchange"])

            if message["type"] == "join":
                if not message["channel"] in self.channel_names:
                    self.channel_names[message["channel"]] = []
                if not message["nick"] in self.channel_names[message["channel"]]:
                    self.channel_names[message["channel"]].append(message["nick"])
                return

            if message["type"] == "part":
                if not message["channel"] in self.channel_names:
                    self.channel_names[message["channel"]] = []
                if message["nick"] in self.channel_names[message["channel"]]:
                    self.channel_names[message["channel"]].remove(message["nick"])
                return

            if message["type"] == "quit":
                for chan in self.channel_names:
                    if message["nick"] in self.channel_names[chan]:
                        self.channel_names[chan].remove(message["nick"])
                return

            if message["type"] == "channel":
                self.server_channels[message["channel"]] = message["chandescription"]
                return

        if len(data) <= 1:
            return
        debug("processing -> ", data)
        try:
            # TODO clear this mess
            # This is for replying to users's ping requests
            if (
                data.find("PING") != -1
                and len(data.split(":")) >= 3
                and "PING" in data.split(":")[2]
                and message["type"] == "privmsg"
                and message["channel"] == self.nick
            ):
                msg = str("PONG " + data.split(":")[1].split("!~")[0] + "\r\n")
                debug("ponging: ", msg)
                await self._enqueue_message(msg)

                if data.find("PRIVMSG") != -1:
                    msg = str(
                        f":{nick} PRIVMSG "
                        + data.split(":")[1].split("!~")[0]
                        + " :PONG "
                        + data.split(" ")[-1]
                        + "\r\n"
                    )
                    # await s.send_all(msg.encode())
                    await self._enqueue_message(msg)
                    debug(f"Sending privmsg: {msg=}")
                log("PONG sent \n")
                return

            if message and message["type"] == "ping":
                msg = str("PONG " + host + "\r\n")
                debug("ponging: ", msg)
                # await s.send_all(msg.encode())
                await self._enqueue_message(msg)
                log("PONG sent \n")
                return

            if len(data.split()) >= 3:
                match = re.match(r":(\S+)!\S* INVITE (\S+) (\S+)", data)
                if match and match[2] == self.nick:
                    log("Invited to " + match[3])
                    if match[1] in self.accept_join_from:
                        await self.join(match[3])

                if message is None or message["type"] != "privmsg":
                    debug("Regex command parser Ignoring: " + data)
                    return

                channel = message["channel"]
                sender_nick = message["nick"]
                if sender_nick.startswith("@"):
                    sender_nick = sender_nick[1:]
                debug("sent by:", sender_nick)
                splitter = "PRIVMSG " + channel + " :"
                if self.strip_messages:
                    msg = splitter.join(data.split(splitter)[1:]).strip()
                else:
                    msg = splitter.join(data.split(splitter)[1:])
                is_private = channel == self.nick
                channel = channel if channel != self.nick else sender_nick
                matched = False

                # Eliminate colors
                msg = re.sub(r"\003\d\d(?:,\d\d)?", "", msg)
                debug(f"PARSED MESSAGE: {msg}")

                if (
                    channel in self.replyIntents
                    and sender_nick in self.replyIntents[channel]
                ):
                    result = await self._call_cb(
                        self.replyIntents[channel][sender_nick].func,
                        Message(channel, sender_nick, msg, is_private),
                    )
                    del self.replyIntents[channel][sender_nick]
                    await self.process_result(result, channel, sender_nick, is_private)
                    return

                for i, cmd in enumerate(
                    utils.regex_commands[::-1]
                    if not utils.parse_order
                    else utils.regex_commands
                ):
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg)
                        if m:
                            if cmd in utils.regex_commands:
                                if is_private and not utils.regex_commands_accept_pm[i]:
                                    continue
                                await trio.sleep(0)
                                result = await self._call_cb(cmd[reg], m)
                            if result:
                                await self.process_result(
                                    result, channel, sender_nick, is_private
                                )
                                matched = True
                            if utils.single_match:
                                matched = True
                                break

                if matched and utils.single_match:
                    await self.check_tables()
                    return

                for i, cmd in enumerate(
                    utils.regex_commands_with_message[::-1]
                    if not utils.parse_order
                    else utils.regex_commands_with_message
                ):
                    if matched:
                        break
                    for reg in cmd:
                        m = re.match(reg, msg)  # , flags=re.IGNORECASE)
                        if m:
                            if cmd in utils.regex_commands_with_message:
                                if (
                                    is_private
                                    and not utils.regex_commands_with_message_accept_pm[
                                        i
                                    ]
                                ):
                                    continue
                                debug("sending to", sender_nick)
                                if utils.regex_commands_with_message_pass_data[i]:
                                    await trio.sleep(0)
                                    result = await self._call_cb(
                                        cmd[reg],
                                        m,
                                        Message(
                                            channel,
                                            sender_nick,
                                            msg,
                                            is_private,
                                            strip=self.strip_messages,
                                        ),
                                    )
                                else:
                                    await trio.sleep(0)
                                    result = await self._call_cb(
                                        cmd[reg],
                                        m,
                                        Message(
                                            channel,
                                            sender_nick,
                                            msg,
                                            is_private,
                                            strip=self.strip_messages,
                                        ),
                                    )

                            if result:
                                await self.process_result(
                                    result, channel, sender_nick, is_private
                                )
                                matched = True
                            if utils.single_match:
                                matched = True
                                break

                if matched and utils.single_match:
                    await self.check_tables()
                    return

                # URL MATCHER
                if utils.url_commands:
                    for word in msg.split(" "):
                        if len(word) < 6:
                            continue
                        result = None
                        word = word.strip()
                        if word[-1] in [" ", "?", ",", ";", ":", "\\"]:
                            word = word[:-1]
                        if utils.validateUrl(word):
                            await trio.sleep(0)
                            debug("Checking url: " + str(word))
                            result = await self._call_cb(utils.url_commands[-1], word)
                        if result:
                            await self.send_message(result, channel)

            await self.check_tables()

        except Exception as e:
            log("ERROR IN MAINLOOP: ", e)
            logger.exception(e)

    async def _call_cb(self, cb, *args, **kwargs):
        if inspect.iscoroutinefunction(cb):
            return await cb(self, *args, **kwargs)
        return cb(*args, **kwargs)

    def __del__(self):
        try:
            self.s.close()
        except:
            pass

    def close(self):
        """Stops the bot and loop if running."""
        self.__del__()
