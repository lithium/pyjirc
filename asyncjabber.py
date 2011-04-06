
from pyxmpp.all import JID, Presence
from pyxmpp.jabber.client import JabberClient
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler
from pyxmpp import streamtls

import logging

class AsyncJabberClient(JabberClient):
    def __init__(self, jid, password, **options):
        if not isinstance(jid, JID):
            jid = JID(jid)

        self.jid = jid
        self.rooms = {}

        kwargs = {
            'tls_settings': streamtls.TLSSettings(require=True, verify_peer=False),
            'auth_methods': ('sasl:PLAIN',),
            'disco_name': "pyjirc",
            'disco_type': "bot"
        }
        kwargs.update(options)
        JabberClient.__init__(self, jid, password, **kwargs)

        self.disco_info.add_feature("jabber:iq:version")

    def tick(self, timeout=1):
        stream = self.get_stream()
        if not stream:
            return -1
        ret = stream.loop_iter(timeout)
        if not ret:
            self.idle()

    def session_started(self):
        JabberClient.session_started(self)
        self.room_manager = MucRoomManager(self.stream)

        handle_presence = getattr(self, 'handle_presence', None)
        if callable(handle_presence):
            self.stream.set_presence_handler('subscribe', handle_presence)
            self.stream.set_presence_handler('subscribed', handle_presence)
            self.stream.set_presence_handler('unsubscribe', handle_presence)
            self.stream.set_presence_handler('unsubscribed', handle_presence)

        handle_message = getattr(self, 'handle_message', None)
        if callable(handle_message):
            self.stream.set_message_handler('normal', handle_message)

        handle_connect = getattr(self, 'handle_connect', None)
        if callable(handle_connect):
            handle_connect()



    def handle_presence(self, stanza):
        self.stream.send(stanza.make_accept_response())
        return True

    def handle_message(self, stanza):
        return True

    def handle_connect(self):
        return True

    def join_room(self, jid, nick=None, handler=None, **options):
        if not isinstance(jid, JID):
            jid = JID(jid)

        if nick is None:
            nick = self.jid.node

        kwargs = {
            'history_maxchars': 0,
        }
        kwargs.update(options)

        if jid in self.rooms:
            return

        if handler is None:
            handler = MucRoomHandler()
        self.rooms[jid] = self.room_manager.join(jid, nick, handler, **kwargs)
