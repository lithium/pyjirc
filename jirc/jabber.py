
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

    def handle_message(self, stanza):
        subject = stanza.get_subject()
        body = stanza.get_body()
        sender = stanza.get_from()

        logging.info("message: <%s> %s: %s " % (subject, body, sender.as_utf8()))

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
