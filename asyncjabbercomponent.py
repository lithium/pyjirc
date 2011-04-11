from pyxmpp.jabberd.component import Component
from pyxmpp.all import JID, Presence
from pyxmpp.jabber.client import JabberClient
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler
from pyxmpp import streamtls

class AsyncJabberComponent(Component):
    def __init__(self, jid, secret, server, port, **options):
        if not isinstance(jid, JID):
            jid = JID(jid)

        kwargs = {
            'disco_name':"pyjirc",
            'disco_category':"x-service",
            'disco_type':"bridge",
        }
        kwargs.update(options)
        Component.__init__(self, jid, secret, server, port, **kwargs)
        self.disco_info.add_feature("jabber:iq:version")


    def tick(self, timeout=1):
        stream = self.get_stream()
        if not stream:
            return -1
        ret = stream.loop_iter(timeout)
        if not ret:
            self.idle()


    def stream_state_changed(self,state,arg):
        """This one is called when the state of stream connecting the component
        to a server changes. This will usually be used to let the administrator
        know what is going on."""
        print "*** State changed: %s %r ***" % (state,arg)

    def authenticated(self):
        Component.authenticated(self)

        handle_presence = getattr(self, 'handle_presence', None)
        if callable(handle_presence):
            self.stream.set_presence_handler(None, handle_presence)

        handle_error = getattr(self, 'handle_error', None)
        if callable(handle_error):
            self.stream.set_presence_handler("error", handle_error)

        handle_message = getattr(self, 'handle_message', None)
        if callable(handle_message):
            self.stream.set_message_handler('normal', handle_message)
 
        handle_connect = getattr(self, 'handle_connect', None)
        if callable(handle_connect):
            handle_connect()


