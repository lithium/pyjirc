
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
        self._prefix_re = re.compile("(?P<nick>[^!]+)!(?P<user>[^@]+)@(?P<host>.+)")
        self._jid_re = re.compile("(?P<node>[^@]+)@(?P<domain>[^/]+)(/(?P<resource>.+))?")
       
        self.jjc = JircJabberClient(settings.JABBER_JID, password=settings.JABBER_PASSWORD, server=settings.JABBER_SERVER, port=self.settings.get('JABBER_PORT', 5222))
        self.jjc.set_handler(self.handler)

        self.jic = JircIrcClient()
        self.jic.set_handler(self.handler)

        self.jabber_channels = {}
        self.irc_channels = {}
        self.irc_users = {}
        self.jabber_users = {}

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
        if msg.what == 'IRC_CONNECT':
            for channel in self.settings.CHANNELS:
                chan = channel['irc']
                self.jabber_channels[chan] = channel['jabber']
                self.jic.join_channel(chan)

        elif msg.what == 'JABBER_CONNECT':
            for channel in self.settings.CHANNELS:
                jid = channel['jabber']
                self.irc_channels[jid] = channel['irc']
                self.jjc.join_room(jid, nick=self.settings.get('JABBER_NICK', None))
        
        elif msg.what == 'IRC_CHANNEL_MESSAGE':
            jid = self.jabber_channels.get(msg.subject, None)
            if jid is not None:
                pass

        elif msg.what == 'JABBER_CHANNEL_MESSAGE':
            chan = self.irc_channels.get(msg.subject, None)
            if chan is not None:
                irc_user = self.irc_users.get(msg.sender, None)
                if irc_user:
                    self.jic.send_to_channel(irc_user.irc_nick, irc_user.irc_channel, msg.body)

        elif msg.what == 'JABBER_CHANNEL_USER':
            irc_nick = self.jic.unique_nick(msg.nick)
            jid = self._jid_re.match(msg.jid).groupdict()
            channel = self._jid_re.match(msg.channel).groupdict()['node']

            self.irc_users[msg.sender] = ObjDict(jid=jid, irc_nick=irc_nick, irc_channel=channel, 
                                                 xmpp_nick=msg.nick, role=msg.role, affiliation=msg.affiliation)

            self.jic.introduce_nick(irc_nick, username=jid['node'], hostname=jid['domain'], info=jid['resource'])
            self.jic.join_channel(irc_nick, channel) 
        
