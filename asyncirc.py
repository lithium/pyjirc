import asyncore
import asynchat
import socket
import StringIO
import datetime

import logging

__all__ = ['AsyncIrcClient']


class AsyncIrcClient(asynchat.async_chat):

    def __init__(self):
        asynchat.async_chat.__init__(self)
        self.buffer = StringIO.StringIO()

    def open(self, host, port=None):
        self.host = host
        self.port = port or 6667
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self.host, self.port) )
        self.set_terminator("\n")

    def connect_user(self, nick, password=None, username=None, info=None):
        self.nick = nick
        self.password = password
        self.username = username or nick
        self.info = info or "*"

        if self.password:
            self.output("PASS", self.password)
        self.output("NICK", self.nick)
        self.output("USER", self.username, '*', '*', ':'+self.info)

    def connect_server(self, servername, password, info=None, ts_supported=True):
        self.servername = servername
        self.password = password
        self.info = info or servername
        
        self.output("PASS", self.password, ":TS" if ts_supported else "")
        self.output("CAPAB", "SSJOIN", "NOQUIT", "NICKIP", "TSMODE" if ts_supported else "")
        self.output("SERVER", servername, "1", ':'+self.info)
        if ts_supported:
            self.output("SVINFO", "5", "3", "0", ':'+self.TS)


    @property
    def TS(self):
        return datetime.datetime.now().strftime('%s')
        

    def collect_incoming_data(self, data):
        self.buffer.write(data)

    def found_terminator(self):
        self.buffer.seek(0)
        line = self.buffer.read()
        self.buffer.truncate(0)
        
        prefix, command, args = self._parse_msg(line)

        logging.debug(":AsyncIrc:IN: %s" % ((prefix,command,args),) )

        handler = getattr(self, 'handle_%s' % (command.lower(),), None)
        if handler is not None and callable(handler):
            handler(prefix, command, args)


    def output(self, *args):
        out = ' '.join(args)
        out = out.encode('ascii','xmlcharrefreplace')
        logging.debug(":AsyncIrc:OUT: %s" %(out,))
        self.push(out+"\r\n")

    def tick(self, timeout=1):
        asyncore.loop(timeout=timeout, count=1)

    def loop(self, timeout=1):
        asyncore.loop(timeout=timeout)

    def join_channel(self, channel):
        self.output("JOIN", channel)

    def _parse_msg(self,s):
        s = s.strip()
        prefix = ''
        trailing = []
        if not s:
            return None
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0)
        return prefix, command, args

    def handle_ping(self, prefix, cmd, args):
        self.output("PONG", ':'+args[0])


