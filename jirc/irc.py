from asyncirc import AsyncIrcClient
import logging
import re
from handler import HasHandlerMixin, Message
from objdict import ObjDict

class JircIrcClient(AsyncIrcClient, HasHandlerMixin):
    def __init__(self):
        AsyncIrcClient.__init__(self)
        self.network_users = {}
        self.network_channels = {}
        self.ping_count = 0

    def handle_privmsg(self, prefix, cmd, args):
        target = args[0]
        line = ' '.join(args[1:])

        logging.info("<%s> %s" % (prefix, line))

        if self.handler:
            self.handler.post(Message("IRC_CHANNEL_MESSAGE", subject=target, sender=prefix, body=line))

    #def handle_266(self, prefix, cmd, args):
        #end of LUSERS command
        #self.handler.post(Message("IRC_CONNECT"))


    def handle_nick(self, prefix, cmd, args):
        nick = args[0]
        if prefix:
            #changing nick
            # ARGS = nickname, ts
            data = self.network_users[prefix]
            self.network_users[nick] = data
            self.network_users[nick].ts = args[1]
            del self.network_users[prefix]
        else:
            #introduction of nick
            # ARGS = nickname, hopcount, timestamp, mode, username, hostname, servername, servicesid, longip, realname
            self.network_users[nick] = ObjDict(ts=args[2], mode=args[3], username=args[4], hostname=args[5], server=args[6], info=args[7])

    def handle_sjoin(self, prefix, cmd, args):
        timestamp, channel = args[:2]
        if len(args) > 2:
            #introduction of channel
            # ARGS = timestamp, channel, mode, members
            self.network_channels[channel] = ObjDict(ts=timestamp, mode=args[2], members={})
            for member in args[3].split(' '):
                matches = re.match(r'(^\W+)(\w+)', member)
                if matches:
                    # contains a mode prefix
                    mode, nick = matches.groups()
                else:
                    mode, nick = '', member
                self.network_channels[channel].members[nick] = mode
        else:
            #user join channel
            # ARGS = timestamp, channel
            self.network_channels[channel].members[prefix] = ''

    def handle_ping(self, *args, **kwargs):
        AsyncIrcClient.handle_ping(self, *args, **kwargs)
        self.ping_count += 1
        if self.ping_count >= 3:
            self.handler.post(Message("IRC_CONNECT"))

    def introduce_nick(self, nick, username=None, hostname=None, info=None, mode="+i"):
        self.output(':'+self.servername, "NICK", nick, "1", self.TS, mode, username or nick, hostname or self.servername, self.servername, "0", "2130706433", ':'+(info or nick))

    def join_channel(self, nick, channel):
        self.output(':'+nick, "SJOIN", self.TS, channel)

    def send_to_channel(self, prefix, channel, message):
        self.output(':'+prefix, "PRIVMSG", channel, ':'+message)


    def unique_nick(self, nick, suffix='_xmpp'):
        if nick not in self.network_users.keys():
            return nick
        nick += suffix
        while nick in self.network_users.keys():
            nick += '_'
        return nick
