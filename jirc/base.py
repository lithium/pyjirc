
from jirc.irc import JircIrcClient
from jirc.jabber import JircJabberClient

from handler import Handler, Message

from objdict import ObjDict
import re

import logging

__all__ = ['Jirc']


class Jirc(object):
    def __init__(self, settings):
        self.handler = Handler(self.handle_message)
        self.settings = settings
        self.state = ObjDict({
            'irc_format': '<%(resource)s%%xmpp> ',
            'jabber_format': '<%(nick)s%%irc> ',
        })
        self._irc_sender_re = re.compile("(?P<nick>[^!]+)!(?P<user>[^@]+)@(?P<host>.+)")
        self._jabber_sender_re = re.compile("(?P<node>[^@]+)@(?P<domain>[^/]+)/(?P<resource>.+)")
       
        self.jjc = JircJabberClient(settings.JABBER_JID, password=settings.JABBER_PASSWORD, server=settings.JABBER_SERVER, port=self.settings.get('JABBER_PORT', 5222))
        self.jjc.set_handler(self.handler)

        self.jic = JircIrcClient()
        self.jic.set_handler(self.handler)

        self.jabber_channels = {}
        self.irc_channels = {}

    def connect(self):
        self.jjc.connect()
        self.jic.open(self.settings.IRC_SERVER, port=self.settings.get('IRC_PORT', 6667));
        self.jic.connect_server(self.settings.IRC_SERVERNAME, self.settings.IRC_PASSWORD, info=self.settings.get('IRC_DESCRIPTION',None))

    def tick(self):
        self.jjc.tick()
        self.jic.tick()
        self.handler.tick(block=False)
        return True

    def disconnect(self):
        self.jjc.disconnect()
        self.jic.disconnect()

    def handle_message(self, msg):
        logging.info(msg)
        if msg.what == 'IRC_CHANNEL_MESSAGE':
            jid = self.jabber_channels.get(msg.subject, None)
            logging.info(jid)
            if jid is not None:
                matches = self._irc_sender_re.match(msg.sender)
                if matches:
                    prefix = self.state.jabber_format % matches.groupdict()
                    self.jjc.send_to_channel(jid, '%s%s' % (prefix, msg.body))

        if msg.what == 'JABBER_CHANNEL_MESSAGE':
            chan = self.irc_channels.get(msg.subject, None)
            logging.info(chan)
            if chan is not None:
                matches = self._jabber_sender_re.match(msg.sender)
                if matches:
                    prefix = self.state.irc_format % matches.groupdict()
                    self.jic.send_to_channel(chan, '%s%s' % (prefix, msg.body))

        if msg.what == 'IRC_CONNECT':
            for channel in self.settings.CHANNELS:
                chan = channel['irc']
                self.jabber_channels[chan] = channel['jabber']
                self.jic.join_channel(chan)

        if msg.what == 'JABBER_CONNECT':
            for channel in self.settings.CHANNELS:
                jid = channel['jabber']
                self.irc_channels[jid] = channel['irc']
                self.jjc.join_room(jid, nick=self.settings.get('JABBER_NICK', None))
