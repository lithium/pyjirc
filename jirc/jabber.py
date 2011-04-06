
from pyxmpp.all import JID, Presence
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler
from asyncjabber import AsyncJabberClient
import logging

class JircRoomHandler(MucRoomHandler):
    def __init__(self, jid):
        self.jid = jid
        MucRoomHandler.__init__(self)

class JircJabberClient(AsyncJabberClient):

    def handle_connect(self):
        self.request_roster()
        presence = Presence()
        self.stream.send(presence)

        self.join_room('jirc@conference.literat.us')

    def handle_message(self, stanza):
        subject = stanza.get_subject()
        body = stanza.get_body()
        sender = stanza.get_from()

        logging.info("message: <%s> %s: %s " % (subject, body, sender.as_utf8()))

        room = self.rooms.get(sender.bare(), None)
        if room is not None:
            if room.get_nick() != sender.resource:
                room.send_message("<%s> %s" % (sender.resource, body))
        return True
