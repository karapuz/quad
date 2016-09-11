'''

'''

class ObjStream(object):
    def __init__(self, impl, options=None):
        self._impl      = impl
        self._options   = options

    def write(self, specs, obj, options=None):
        self._impl.write(obj={'specs':specs, 'obj': obj}, options=options)

