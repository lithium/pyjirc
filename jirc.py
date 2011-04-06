
from pyxmpp.all import JID, Presence
from pyxmpp.jabber.client import JabberClient
from pyxmpp.jabber.muc import MucRoomState, MucRoomManager, MucRoomHandler
from pyxmpp import streamtls


import asyncore
import asynchat
import socket
import StringIO




import pprint
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class AsyncIrcClient(asynchat.async_chat):

    def __init__(self, nick, user, host, port=6667, password=None):
        asynchat.async_chat.__init__(self)
        self.nick = nick
        self.user = user
        self.host = host
        self.port = port
        self.password = password
        self.buffer = StringIO.StringIO()

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self.host, self.port) )

        self.set_terminator("\r\n")

        if password:
            self.output("PASS", self.password)
        self.output("NICK", self.nick)
        self.output("USER", self.user, '*', '*', ':'+self.user)

    def collect_incoming_data(self, data):
        self.buffer.write(data)

    def found_terminator(self):
        self.buffer.seek(0)
        line = self.buffer.read()
        self.buffer.truncate(0)
        
        prefix, command, args = self._parse_msg(line)

        logger.info( "IRC: %s" % ((prefix,command,args),) )

        handler = getattr(self, 'handle_%s' % (command.lower(),), None)
        if handler is not None and callable(handler):
            handler(prefix, command, args)


    def output(self, *args):
        self.push(' '.join(args)+"\r\n")

    def tick(self, timeout=1):
        asyncore.loop(timeout=timeout, count=1)

    def loop(self, timeout=1):
        asyncore.loop(timeout=timeout)


    def _parse_msg(self,s):
        prefix = ''
        trailing = []
        if not s:
            return None
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0)
        return prefix, command, args




class JircIrcClient(AsyncIrcClient):

    def join_channel(self, channel):
        self.output("JOIN", channel)

    def handle_376(self, prefix, command, args):
        logger.info("END OF MOTD!!!!!")

    def handle_privmsg(self, prefix, cmd, args):
        logger.info("<%s> %s" % (prefix, args[1]))




class JircRoomHandler(MucRoomHandler):
    def __init__(self, jid):
        self.jid = jid
        MucRoomHandler.__init__(self)


class JircJabberClient(JabberClient):
    #JabberClient is not a new-style class, super() doesnt work!

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

        self.request_roster()
        presence = Presence()
        self.stream.send(presence)

        self.stream.set_presence_handler('subscribe', self.presence)
        self.stream.set_presence_handler('subscribed', self.presence)
        self.stream.set_presence_handler('unsubscribe', self.presence)
        self.stream.set_presence_handler('unsubscribed', self.presence)
        self.stream.set_message_handler('normal', self.message)

        self.room_manager = MucRoomManager(self.stream)

        self.join_room('jirc@conference.literat.us')


    def presence(self, stanza):
        self.stream.send(stanza.make_accept_response())

        logger.info("presence: %s" % (stanza,))
        return True

    def message(self, stanza):
        subject = stanza.get_subject()
        body = stanza.get_body()
        sender = stanza.get_from()

        logger.info("message: <%s> %s: %s " % (subject, body, sender.as_utf8()))

        room = self.rooms.get(sender.bare(), None)
        if room is not None:
            if room.get_nick() != sender.resource:
                room.send_message("<%s> %s" % (sender.resource, body))
        


        return True

    def join_room(self, jid, nick=None, **options):
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

        handler = JircRoomHandler(jid)
        self.rooms[jid] = self.room_manager.join(jid, nick, handler, **kwargs)







if __name__ == '__main__':


    jjc = JircJabberClient("jirc@literat.us/bridge", password="Eel7Xeiz", server="literat.us")
    jjc.connect()


    jic = JircIrcClient("jirc", "jirc", "literat.us")
    jic.join_channel("#jirc")


    # main loop
    running = True
    try:
        while running:
            jjc.tick()
            jic.tick()
    except KeyboardInterrupt:
        pass

    jjc.disconnect()
    jic.disconnect()


