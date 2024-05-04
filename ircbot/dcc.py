# Simple dcc related functions
import socket
import struct
from enum import Enum

from ircbot.utils import debug, log

BUFFSIZE = 2048


class DccServer(Enum):
    SEND = 0
    GET = 1


# Stolen from https://github.com/jaraco/irc/blob/5ee34d886507aea3a9edb045d258098a78d1117b/irc/client.py
def ip_num_to_quad(num: int):
    """Convert an IP number as an integer given in ASCII representation to an
    IP address string."""
    packed = struct.pack(">L", int(num))
    bytes = struct.unpack("BBBB", packed)
    return ".".join(map(str, bytes))


# Stolen from https://github.com/jaraco/irc/blob/5ee34d886507aea3a9edb045d258098a78d1117b/irc/client.py
def ip_quad_to_num(ip: str):
    """Convert an IP address string (e.g. '192.168.0.1') to an IP number as a
    base-10 integer given in ASCII representation."""
    bytes = map(int, ip.split("."))
    packed = struct.pack("BBBB", *bytes)
    return str(struct.unpack(">L", packed)[0])


def get_chunk_sizes_list(size: int, buffsize: int):
    return size // buffsize * [buffsize] + [size % buffsize]


def is_port_available(ip, port):
    result = False
    with socket.socket() as s:
        try:
            s.bind((ip, port))
            result = True
        except:
            pass
    return result


class DccHelper:
    def __init__(
        self,
        nick: str = "",
        filename: str = "",
        ip: str = "",
        port: int = 0,
        size: int = 0,
        token=None,
    ):
        """Helper for dealing with dcc send request. You can pass in the re.match object that
        the 'dccsend' or 'dccserversend' custom_handlers takes in.
        Example:
        ```
        from IrcBot.dcc import dccSenderHelper
        @utils.custom_handler("dccsend")
        def onDccSend(**m):
            dccSenderHelper(**m).download(f"/home/user/Download/{m['filename']}")
        ```

        :param nick: Nick of the user sending the request
        :type nick: str
        :param filename: Name of the file
        :type filename: str
        :param ip: Host ip of the file being offered
        :type ip: str
        :param port: tcp port of the file being offered
        :type port: int
        :param size: Size of the file in bytes
        :type size: int
        """
        self.nick = nick
        self.filename = filename
        self.ip = ip
        self.port = port
        self.size = size
        self.token = token
        self.is_passive = self.token is not None  # and self.port == 0 or self.ip == "1.1.1.1" ?
        self.download_progress = 0

    def to_message(self):
        return {
            "nick": self.nick,
            "filename": self.filename,
            "ip": self.ip,
            "port": self.port,
            "size": self.size,
            "token": self.token,
        }

    def download(self, filepath, progress_callback=None, buffsize=BUFFSIZE):
        """Performs the download of the offered file. This will be performed
        blocking, use bot.dcc_get() otherwise.

        :param filepath: String absolute file path
        :type str:
        :param progress_callback: Optinal function to call as each chunk of the file is received, the progress callback: pcb(total_received: int, progress: float) ---> total_received is the number of bytes received so far
        """
        if not self.is_passive:
            with socket.socket() as e:
                s.connect((self.ip, self.port))
                with open(filepath, "wb") as f:
                    s_list = get_chunk_sizes_list(self.size, buffsize)
                    for i, bsize in enumerate(s_list):
                        bytes_read = s.recv(bsize)
                        if not bytes_read:
                            break
                        f.write(bytes_read)
                        self.download_progress = i / len(s_list)

                        if callable(progress_callback):
                            progress_callback(i * buffsize, self.download_progress)

                self.download_progress = 1
                if callable(progress_callback):
                    progress_callback(i * buffsize, self.download_progress)
            return

        log("PASSIVE BLOCKING DCC SEND DOWNLOAD!!!")
        with socket.socket() as s:
            s.bind((self.ip, self.port))
            s.listen(1)
            debug(f"Listening on to: {self.ip} {self.port}")
            c, a = s.accept()
            with open(filepath, "wb") as f:
                s_list = get_chunk_sizes_list(self.size, buffsize)
                for i, bsize in enumerate(s_list):
                    bytes_read = c.recv(bsize)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    self.download_progress = i / len(s_list)

                    if callable(progress_callback):
                        progress_callback(i * buffsize, self.download_progress)
            c.shutdown(2)
            c.close()


"""
EXAMPLE PASSIVE COMMUNICATION

    PRIVMSG file :.DCC SEND pdf.pdf 16843009 0 393400 48.\r
    :file!mattf@27558C24.CA1B7A0A.DB9752B6.IP PRIVMSG matheus :.DCC SEND pdf.pdf 758672010 4985 393400 48.\r

:matheus_!matheus@92499B0D.A546DD36.6DE2D5CC.IP PRIVMSG matheus :.DCC SEND debian-sid-hurd-i386-CD-1.iso 16843009 0 677980160 36.\r
PRIVMSG matheus_ :.DCC SEND debian-sid-hurd-i386-CD-1.iso 2130706433 35313 677980160 36.\r
"""
