

__all__ = ['ObjDict']

class ObjDict(dict):
    def __getattr__(self, name):
        return self.get(name, '')
    def __setattr__(self, name, value):
        self[name] = value
    def __delattr__(self, name):
        del self[name]

