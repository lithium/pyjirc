from asyncirc import AsyncIrcClient
import logging

class JircIrcClient(AsyncIrcClient):

    def handle_privmsg(self, prefix, cmd, args):
        logging.info("<%s> %s" % (prefix, ' '.join(args[1:])))
        self.output("PRIVMSG", args[0], ":<%s> %s" % (prefix, ' '.join(args[1:])))




