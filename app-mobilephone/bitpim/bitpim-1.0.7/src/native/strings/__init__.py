# There is a Python and a C implementation of Jaro/Winkler available in this
# directory - we try for C first

if __debug__:
    try:
        import jarow as j
    except:
        print "Using (slow) Python version of Jaro/Winkler.  Build C module in native/strings."
        import jarowpy as j
    jarow=j.jarow
    del j
else:
    # production must always use native version
    import jarow as j
    jarow=j.jarow
    del j
