
from jirc.irc import JircIrcClient
from jirc.jabber import JircJabberClient


import pprint
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)



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


