import asyncio
import os
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection

import pytest
from ircbot.client import IrcBot
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

CHANNELS = ["#bots"]


@pytest.fixture(scope="session", autouse=True)
def setup_server(request: pytest.FixtureRequest):
    with DockerContainer("ghcr.io/ergochat/ergo:stable").with_bind_ports(6667, 6667).with_bind_ports(
        6697, 6697
    ) as container:
        wait_for_logs(container, "Server running")

    request.addfinalizer(container.stop)
    container.start()


# TODO: Would be easier and faster with a synchronous watcher
class WatcherBot(IrcBot):
    def __init__(
        self,
        *args,
        pipe_connection: Connection,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pipe_connection = pipe_connection

    async def read_pipe(self):
        self.pipe_connection.send("ready")

        while True:
            await asyncio.sleep(1)
            if self.pipe_connection.poll():
                obj = self.pipe_connection.recv()
                if isinstance(obj, tuple):
                    await self.send_message(*obj)
                    return
                print(f"---------> SENDING: {obj}")
                await self.send_message(obj)

    async def _mainloop(self, async_callback: IrcBot.AsyncCallback | None):
        @self.regex_cmd_with_message(r".*", True)
        def watch_all(args, message):
            self.pipe_connection.send(message)

        await super()._mainloop(self.read_pipe)


def flush_connection(conn: Connection):
    while conn.poll():
        conn.recv()


@pytest.fixture(scope="session", autouse=True)
def setup_watcher(setup_server, request: pytest.FixtureRequest) -> tuple[Connection, Connection]:
    parent_conn, child_conn = Pipe()
    bot = WatcherBot(
        "localhost",
        6667,
        "watcher",
        CHANNELS,
        pipe_connection=child_conn,
        retry_connecting=False,
    )

    p = Process(target=bot.run, daemon=True)

    def cleanup():
        if not p or not p.is_alive():
            return
        p.terminate()
        if p.pid:
            os.kill(p.pid, 9)

    request.addfinalizer(cleanup)
    p.start()

    # Wait for the bot to be ready
    assert parent_conn.recv() == "ready"
    return parent_conn, child_conn


@pytest.fixture(scope="function")
def watcher(setup_watcher: tuple[Connection, Connection]) -> Connection:
    parent_conn, child_conn = setup_watcher
    flush_connection(parent_conn)
    flush_connection(child_conn)
    return parent_conn


@pytest.fixture(scope="function")
def bot(setup_server) -> IrcBot:
    return IrcBot("localhost", 6667, "testbot", CHANNELS, retry_connecting=False)


@pytest.fixture(scope="function")
def ssl_ircbot(setup_server) -> IrcBot:
    return IrcBot("localhost", 6697, "testbot_ssl", CHANNELS, use_ssl=True, retry_connecting=False)
