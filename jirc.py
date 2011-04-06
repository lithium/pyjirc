
from jirc.irc import JircIrcClient
from jirc.jabber import JircJabberClient


import pprint
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


import local_settings as settings



if __name__ == '__main__':


    jjc = JircJabberClient(settings.JABBER_JID, password=settings.JABBER_PASSWORD, server=settings.JABBER_SERVER, 
        port=getattr(settings, 'JABBER_PORT', 5222))
    jjc.connect()


    jic = JircIrcClient(getattr(settings, 'IRC_NICK', 'jirc'), getattr(settings, 'IRC_USER', 'jirc'), settings.IRC_SERVER, 
        port=getattr(settings, 'IRC_PORT', 6667))

    jic.join_channel(settings.IRC_CHANNEL)


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


