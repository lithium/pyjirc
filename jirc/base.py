
from pyxmpp.all import JID
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
       
        self.jjc = JircJabberClient(settings.JABBER_JID, settings.JABBER_PASSWORD, server=settings.JABBER_SERVER, port=self.settings.get('JABBER_PORT', 5222))
        self.jjc.set_handler(self.handler)

        self.jic = JircIrcClient()
        self.jic.set_handler(self.handler)

        self.jabber_channels = {}
        self.irc_channels = {}
        self.irc_users = {}
        self.jabber_users = {}
        self.irc_connected = False
        self.jabber_connected = False


        for channel in self.settings.CHANNELS:
            self.jabber_channels[channel['irc']] = channel['jabber']
            self.irc_channels[channel['jabber']] = channel['irc']


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
        for nick, data in self.jabber_users.items():
            self.jjc.part_room(data.room_jid, data.jid)

        self.jjc.disconnect()
        self.jic.disconnect()


    def _fully_connected(self):
        for channel in self.settings.CHANNELS:
            irc_chan = self.jic.network_channels[channel['irc']]
            for nick in irc_chan.members.keys():
                jid = JID(nick, domain=self.settings.JABBER_JID, resource=nick)
                sender = self.jjc.join_room(channel['jabber'], jid)
                self.jabber_users[nick] = ObjDict(jid=jid, sender=sender, room_jid=channel['jabber'])

    def handle_message(self, msg):
        logging.info(msg)
        if msg.what == 'IRC_CONNECT':
            self.irc_connected = True
            if self.jabber_connected:
                self._fully_connected()
        elif msg.what == 'JABBER_CONNECT':
            self.jabber_connected = True
            if self.irc_connected:
                self._fully_connected()
        
        elif msg.what == 'IRC_CHANNEL_MESSAGE':
            jid = self.jabber_channels.get(msg.subject, None)
            if jid is not None:
                jabber_user = self.jabber_users.get(msg.sender, None)
                if jabber_user:
                    self.jjc.send_to_room(jabber_user.room_jid, jabber_user.jid, msg.body)

        elif msg.what == 'JABBER_CHANNEL_MESSAGE':
            chan = self.irc_channels.get(msg.subject, None)
            if chan is not None:
                irc_user = self.irc_users.get(msg.sender, None)
                if irc_user:
                    self.jic.send_to_channel(irc_user.irc_nick, irc_user.irc_channel, msg.body)

        elif msg.what == 'JABBER_CHANNEL_USER':
            irc_nick = self.jic.unique_nick(msg.nick)

            jid = getattr(msg, 'jid', '%s@%s/%s' % (msg.nick, self.settings.JABBER_JID, irc_nick))
            jid = self._jid_re.match(jid).groupdict()
            channel = self._jid_re.match(msg.channel).groupdict()['node']


            if JID(msg.sender) not in [j.sender for j in self.jabber_users.values()]:
                # dont create IRC users for our own jabber users presence stanzas
                self.irc_users[msg.sender] = ObjDict(jid=jid, irc_nick=irc_nick, irc_channel=channel, 
                                                     xmpp_nick=msg.nick, role=msg.role, affiliation=msg.affiliation)
                self.jic.introduce_nick(irc_nick, username=jid['node'], hostname=jid['domain'], info=jid['resource'])
                self.jic.join_channel(irc_nick, channel) 
        
