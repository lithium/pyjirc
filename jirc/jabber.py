
from pyxmpp.all import JID, Presence, Iq, Message
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler, MucPresence
#from asyncjabber import AsyncJabberClient
from asyncjabbercomponent import AsyncJabberComponent
from handler import HasHandlerMixin, Message as HandlerMessage
import logging

class JircRoomHandler(MucRoomHandler):
    def __init__(self, jid):
        self.jid = jid
        MucRoomHandler.__init__(self)

class JircJabberClient(AsyncJabberComponent, HasHandlerMixin):
    def handle_connect(self):
        self.handler.post(HandlerMessage('JABBER_CONNECT'))

    def join_room(self, room_jid, jid, nick=None):
        if not isinstance(room_jid, JID):
            room_jid = JID(room_jid)
        if not isinstance(jid, JID):
            jid = JID(jid)
        if nick is None:
            nick = jid.resource
        my_sender = JID(room_jid.node, room_jid.domain, nick)
        p = MucPresence(from_jid=jid.bare(), to_jid=my_sender)
        p.make_join_request(history_maxchars=0)
        self.stream.send(p)
        return my_sender

    def part_room(self, room_jid, jid):
        if not isinstance(room_jid, JID):
            room_jid = JID(room_jid)
        if not isinstance(jid, JID):
            jid = JID(jid)
        presence = MucPresence(from_jid=jid.bare(), to_jid=room_jid.bare(),stanza_type='unavailable')
        self.stream.send(presence)

    def send_to_room(self, room_jid, jid, body):
        if not isinstance(room_jid, JID):
            room_jid = JID(room_jid)
        if not isinstance(jid, JID):
            jid = JID(jid)
        msg = Message(from_jid=jid.bare(), to_jid=room_jid.bare(), body=body, stanza_type="groupchat")
        self.stream.send(msg)


    def handle_presence(self, stanza):
        sender = stanza.get_from()
        to = stanza.get_to()

        if stanza.get_type() in ('subscribe','subscribed','unsubscribe','unsubscribed'):
            self.stream.send(stanza.make_accept_response())
            return True

        detail = dict((attr.name, attr.content) for attr in stanza.xpath_eval('user:x/user:item/@*', {'user': "http://jabber.org/protocol/muc#user"}))
        self.handler.post(HandlerMessage("JABBER_CHANNEL_USER", channel=sender.bare().as_utf8(), nick=sender.resource, sender=sender.as_utf8(), **detail))
        return True

    def handle_error(self, stanza):
        if stanza.xpath_eval('a:error/b:conflict', {'a':"http://pyxmpp.jajcus.net/xmlns/common", 'b':"urn:ietf:params:xml:ns:xmpp-stanzas"}):
            self.handler.post(HandlerMessage("JABBER_NICK_CONFLICT", sender=stanza.get_from().as_utf8(), to=stanza.get_to().as_utf8()))
        return True


    def handle_message(self, stanza):
        subject = stanza.get_subject()
        body = stanza.get_body()
        sender = stanza.get_from()

        #logging.info(stanza.serialize())

        if not stanza.xpath_eval('delay:x', {'delay': 'jabber:x:delay'}):
            self.handler.post(HandlerMessage("JABBER_CHANNEL_MESSAGE", subject=sender.bare().as_utf8(), body=body, sender=sender.as_utf8()))
        return True


