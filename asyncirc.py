import asyncore
import asynchat
import socket
import StringIO

import logging

__all__ = ['AsyncIrcClient']

class AsyncIrcClient(asynchat.async_chat):

    def __init__(self, nick, user, host, port=6667, password=None):
        asynchat.async_chat.__init__(self)
        self.nick = nick
        self.user = user
        self.host = host
        self.port = port
        self.password = password
        self.buffer = StringIO.StringIO()

    def open(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self.host, self.port) )
        self.set_terminator("\r\n")

        if self.password:
            self.output("PASS", self.password)
        self.output("NICK", self.nick)
        self.output("USER", self.user, '*', '*', ':'+self.user)

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
        logging.debug(":AsyncIrc:OUT: %s" %(out,))
        self.push(out+"\r\n")

    def tick(self, timeout=1):
        asyncore.loop(timeout=timeout, count=1)

    def loop(self, timeout=1):
        asyncore.loop(timeout=timeout)

    def join_channel(self, channel):
        self.output("JOIN", channel)

    def _parse_msg(self,s):
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


