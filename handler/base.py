
import Queue as queue

__all__ = ['Handler', 'Message', 'HasHandlerMixin']


class Message(object):
    def __init__(self, what, **args):
        self.what = what
        self.args = args

    def __unicode__(self):
        return repr(self)

    def __repr__(self):
        return '<Message %s:%s>' % (self.what, self.args)

    def __getattr__(self, name):
        if name in self.args:
            return self.args[name]
        raise AttributeError(name)
    


class Handler(object):

    def __init__(self, callback=None):
        self.queue = queue.Queue()
        self.callback = None
        if callback is not None:
            self.set_callback(callback)

    def set_callback(self, callback):
        if not callable(callback):
            raise ValueError("callback must be callable")
        self.callback = callback

    def handle_message(self, msg):
        if self.callback:
            self.callback(msg)
            return
        raise NotImplementedError("You must subclass handle_message")

    def post(self, msg, block=True, timeout=None):
        if not isinstance(msg, Message):
            msg = Message(unicode(msg))
        self.queue.put(msg, block=block, timeout=timeout)

    def tick(self, block=True, timeout=None):
        try:
            msg = self.queue.get(block=block, timeout=timeout)
            self.handle_message(msg)
        except queue.Empty:
            pass

    def loop(self, *args, **kwargs):
        while True:
            self.tick(*args, **kwargs)



class HasHandlerMixin(object):
    def __init__(self,*args,**kwargs):
        pass

    def set_handler(self, handler):
        self._handler = handler

    @property
    def handler(self):
        return getattr(self, '_handler', None)

