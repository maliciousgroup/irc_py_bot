import socket
import select
import random
import string
import queue
import ssl
import re


NoneType = type(None)
IRC_MSG_REGEX = r'^(:(\S+) )?(\S+)( (?!:)(.+?))?( :(.+))?$'
IRC_NICK_REGEX = r'^[a-z|A-Z|_|\\|\[|\]|\{|\}][a-z|A-Z|0-9|_| |\\|\[|\]|\{|\}]{2,16}$'
IRC_CHANNEL_REGEX = r'^[#&!+][^\x00\x07\x0A\x0D, ]+$'


class Bot(object):

    def __init__(self):
        self._sock = self._setup_socket()
        self._host = None
        self._port = None
        self._nick = self._random_string(6)
        self._user = self._random_string(6)
        self._opers = []
        self._channel = None
        self._channels = []
        self._ssl_flag = False

        self._r_queue = queue.Queue(maxsize=0)
        self._w_queue = queue.Queue(maxsize=0)

    '''Method to return a valid socket'''
    @staticmethod
    def _setup_socket():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(True)
            return sock
        except socket.error as e:
            raise

    '''Method to generate a random string'''
    @staticmethod
    def _random_string(length: int):
        return "{}".format(''.join(random.choices(string.ascii_letters, k=length)))

    '''Host Property Getter'''
    @property
    def host(self):
        return self._host

    '''Host Property Setter'''
    @host.setter
    def host(self, hostname: str):
        try:
            self._host = socket.gethostbyname(hostname)
        except socket.error:
            raise

    '''Port Property Getter'''
    @property
    def port(self):
        return self._port

    '''Port Property Setter'''
    @port.setter
    def port(self, port: str):
        if int(port) in range(1, 65535):
            self._port = port

    '''User Property Getter'''
    @property
    def user(self):
        return self._user

    '''User Property Setter'''
    @user.setter
    def user(self, username: str):
        self._user = username

    '''Nick Property Getter'''
    @property
    def nick(self):
        return self._nick

    '''Nick Property Setter'''
    @nick.setter
    def nick(self, nickname: str):
        if re.search(IRC_NICK_REGEX, nickname):
            self._nick = nickname

    '''Channel Property Getter'''
    @property
    def channel(self):
        return " ".join(self._channels) if self._channels else None

    '''Channel Property Setter'''
    @channel.setter
    def channel(self, chan: str):
        if re.search(IRC_CHANNEL_REGEX, chan):
            if chan not in self._channels:
                self._channel = chan
                self._channels.append(chan.lower())

    '''SSL Flag Property Getter'''
    @property
    def ssl_flag(self):
        return self._ssl_flag

    '''SSL Flag Property Setter'''
    @ssl_flag.setter
    def ssl_flag(self, flag: bool):
        self._ssl_flag = flag

    '''Connect to IRC Server and Port'''
    def connect(self):
        if not self._host or not self._port:
            return False
        if self._ssl_flag or self._port is '6697':
            self._sock = ssl.wrap_socket(self._sock)
        try:
            self._sock.connect((self._host, int(self._port)))
            self._data_handler()
        except socket.error:
            raise

    '''Main Data Handler for Communication Queues'''
    def _data_handler(self):
        while True:
            read, write, _ = select.select([self._sock], [self._sock], [])
            if self._sock in read:
                data = self._sock.recv(512).decode('unicode_escape')
                if '\r\n' not in data:
                    continue
                for line in data.split('\r\n'):
                    self._r_queue.put(line)
                    self._message_parser()
                    self._r_queue.task_done()
            if self._sock in write:
                if self._w_queue.empty() is not True:
                    stub = self._w_queue.get()
                    self.socket_send(stub)
                    self._w_queue.task_done()

    '''Main Message Parser'''
    def _message_parser(self):
        if self._r_queue.empty() is not True:
            data = self._r_queue.get()
            if not data:
                return
            valid_msg = re.match(IRC_MSG_REGEX, data, re.M | re.I)
            if not valid_msg:
                return
            full = valid_msg.group()
            prefix = valid_msg.group(2)
            command = valid_msg.group(3)
            params = valid_msg.group(5)
            trailing = valid_msg.group(6)

            '''DEBUG'''
            print(full)
            '''DEBUG'''

            '''Handle Ping Responses'''
            if command.lower().startswith('ping'):
                self.irc_pong(trailing)

            '''Join Channels on connection'''
            if command == "396":
                for chan in self._channels:
                    self.irc_join(chan)

            '''Set Nickname on connection'''
            if command == "432":
                self.irc_nick(self._nick)

            if command.lower().startswith("notice"):
                if 'found your hostname' in trailing.lower():
                    self.irc_nick(self._nick)
                    self.irc_user(self._user, "We are Malicious Group")

            '''Send the incoming message to custom handler for parsing by user'''
            self.custom_handler(full, prefix, command, params, trailing)

    '''Custom Handler to be overriden by User'''
    def custom_handler(self, full, prefix, command, params, trailing):
        pass

    '''Send Message Data over Socket'''
    def socket_send(self, message: str):
        try:
            data = "{}\r\n".format(message).encode('utf-8')
            self._sock.sendall(data)
        except socket.error:
            raise

    '''Reply with PONG and Server String'''
    def irc_pong(self, server_string: str):
        self._w_queue.put("PONG {}".format(server_string.lstrip(' :')))

    '''Join an IRC Channel'''
    def irc_join(self, channel: str):
        self._w_queue.put("JOIN {}".format(channel))

    '''Part a IRC Channel'''
    def irc_part(self, channel: str):
        self._w_queue.put("PART {}".format(channel))

    '''Change IRC nickname'''
    def irc_nick(self, nickname: str):
        self._w_queue.put("NICK {}".format(nickname))

    '''Set the IRC Username'''
    def irc_user(self, user: str, message: str):
        if not message:
            message = "Act like you know"
        self._w_queue.put("USER {} {} {} :{}".format(user, 8, 0, message))

    '''Send Message to IRC Target'''
    def irc_message(self, target: str, message: str):
        self._w_queue.put(":null PRIVMSG {} :{}".format(target, message))
