from asyncirc import AsyncIrcClient
import logging
from handler import HasHandlerMixin, Message

class JircIrcClient(AsyncIrcClient, HasHandlerMixin):

    def handle_privmsg(self, prefix, cmd, args):
        target = args[0]
        line = ' '.join(args[1:])

        logging.info("<%s> %s" % (prefix, line))

        if self.handler:
            self.handler.post(Message("IRC_CHANNEL_MESSAGE", subject=target, sender=prefix, body=line))
        #self.output("PRIVMSG", target, ":<%s> %s" % (prefix, line))

    def handle_266(self, prefix, cmd, args):
        #end of LUSERS command
        self.handler.post(Message("IRC_CONNECT"))

    def send_to_channel(self, channel, message):
        self.output("PRIVMSG", channel, ':'+message)
