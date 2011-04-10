
from pyxmpp.all import JID, Presence
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler
from asyncjabber import AsyncJabberClient
from handler import HasHandlerMixin, Message
import logging

class JircRoomHandler(MucRoomHandler):
    def __init__(self, jid):
        self.jid = jid
        MucRoomHandler.__init__(self)

class JircJabberClient(AsyncJabberClient, HasHandlerMixin):

    def handle_connect(self):
        self.request_roster()
        presence = Presence()
        self.stream.send(presence)

        if self.handler:
            self.handler.post(Message('JABBER_CONNECT'))

    def handle_presence(self, stanza):
        if stanza.get_type() in ('subscribe','subscribed','unsubscribe','unsubscribed'):
            self.stream.send(stanza.make_accept_response())
            return True


        sender = stanza.get_from()
        to = stanza.get_to()

        detail = dict((attr.name, attr.content) for attr in stanza.xpath_eval('user:x/user:item/@*', {'user': "http://jabber.org/protocol/muc#user"}))

        self.handler.post(Message("JABBER_CHANNEL_USER", channel=sender.bare().as_utf8(), nick=sender.resource, sender=sender.as_utf8(), **detail))

        #logging.info("PRESENCE from: %s  to: %s  (%s)" % (sender.as_utf8(), to.as_utf8(), detail))
        #logging.info(stanza.serialize())

    def handle_message(self, stanza):
        subject = stanza.get_subject()
        body = stanza.get_body()
        sender = stanza.get_from()

        #logging.info(stanza.serialize())

        room = self.rooms.get(sender.bare(), None)
        if room is not None:
            if room.get_nick() != sender.resource:
                self.handler.post(Message("JABBER_CHANNEL_MESSAGE", subject=room.room_jid.bare().as_utf8(), body=body, sender=sender.as_utf8()))
        return True


    def send_to_channel(self, jid, message):
        if not isinstance(jid, JID):
            jid = JID(jid)
        room = self.rooms.get(jid.bare(), None)
        if room is not None:
            room.send_message(message)
