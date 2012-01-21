# module definer

try:
    # if we can't import the module then we won't work
    from outlook import *
except:
    raise ImportError()
