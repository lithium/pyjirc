
from jirc.irc import JircIrcClient
from jirc.jabber import JircJabberClient

from handler import Handler, Message

import logging

__all__ = ['Jirc']


class Jirc(object):
    def __init__(self, settings):
        self.handler = Handler(self.handle_message)
        self.settings = settings
       
        self.jjc = JircJabberClient(settings.JABBER_JID, password=settings.JABBER_PASSWORD, server=settings.JABBER_SERVER, port=getattr(settings, 'JABBER_PORT', 5222))
        self.jjc.set_handler(self.handler)

        self.jic = JircIrcClient(getattr(settings, 'IRC_NICK', 'jirc'), getattr(settings, 'IRC_USER', 'jirc'), 
                settings.IRC_SERVER, port=getattr(settings, 'IRC_PORT', 6667))
        self.jic.set_handler(self.handler)

        self.jabber_channels = {}
        self.irc_channels = {}

    def connect(self):
        self.jjc.connect()
        self.jic.open()

    def tick(self):
        self.jjc.tick()
        self.jic.tick()
        self.handler.tick(block=True, timeout=0.2)
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
                self.jjc.send_to_channel(jid, '<%s> %s' % (msg.sender, msg.body))

        if msg.what == 'JABBER_CHANNEL_MESSAGE':
            chan = self.irc_channels.get(msg.subject, None)
            logging.info(chan)
            if chan is not None:
                self.jic.send_to_channel(chan, '<%s> %s' % (msg.sender, msg.body))

            self.jic.send_to_channel('#jirc', 'wtf')

        if msg.what == 'IRC_CONNECT':
            for channel in self.settings.CHANNELS:
                chan = channel['irc']
                self.jabber_channels[chan] = channel['jabber']
                self.jic.join_channel(chan)

        if msg.what == 'JABBER_CONNECT':
            for channel in self.settings.CHANNELS:
                jid = channel['jabber']
                self.irc_channels[jid] = channel['irc']
                self.jjc.join_room(jid)
