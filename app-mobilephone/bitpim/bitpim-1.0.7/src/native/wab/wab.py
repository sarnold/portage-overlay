import pywabimpl

class WABException(Exception):
    def __init__(self,str):
        Exception.__init__(self,str)

class MAPIException(Exception):
    def __init__(self, code, str):
        self.code=code
        Exception.__init__(self,str)

def doexception():
    code=pywabimpl.cvar.errorcode
    for i in dir(constants):
        if (i.startswith('MAPI_E') or i.startswith('MAPI_W')) and \
               getattr(constants,i)==code:
            raise MAPIException(code, i)
    raise WABException(pywabimpl.cvar.errorstring)

constants=pywabimpl.constants

class WAB:

    def __init__(self, enableprofiles=True, filename=None):
        if filename is None:
            filename=""
        # ::TODO:: - the filename is ignored if enableprofiles is true, so
        # exception if one is supplied
        # Double check filename exists if one is supplied since
        # the wab library doesn't actually error on non-existent file
        self._wab=pywabimpl.Initialize(enableprofiles, filename)
        if self._wab is None:
            raise doexception()

    def rootentry(self):
        return pywabimpl.entryid()

    def getpabentry(self):
        pe=self._wab.getpab()
        if pe is None:
            raise doexception()
        return pe

    def getrootentry(self):
        return pywabimpl.entryid()

    def openobject(self, entryid):
        x=self._wab.openobject(entryid)
        if x is None:
            raise doexception()
        if x.gettype()==constants.MAPI_ABCONT:
            return Container(x)
        return x

class Table:
    def __init__(self, obj):
        self.obj=obj

    def __iter__(self):
        return self

    def enableallcolumns(self, bruteforce=False):
        if bruteforce:
            props=[]
            for i in dir(constants):
                if i.startswith('PR_'):
                    if i.endswith("_A") or i.endswith("_W"):
                        continue
                    props.append(getattr(constants,i))
            p=pywabimpl.proptagarray(len(props))
            for num,value in zip(range(len(props)), props):
                p.setitem(num, value)
            if not self.obj.enablecolumns(p):
                raise doexception()
        else:
            if not self.obj.enableallcolumns():
                raise doexception()

    def next(self):
        row=self.obj.getnextrow()
        if row is None:
            raise doexception()
        if row.IsEmpty():
            raise StopIteration()
        # we return a dict, built from row
        res={}
        for i in range(row.numproperties()):
            k=row.getpropertyname(i)
            if len(k)==0:
                continue
            v=self._convertvalue(k, row.getpropertyvalue(i))
            if v is not None:
                res[k]=v
        return res

    def count(self):
        i=self.obj.getrowcount()
        if i<0:
            raise doexception()
        return i

    def _convertvalue(self,key,v):
        x=v.find(':')
        t=v[:x]
        v=v[x+1:]
        if t=='int':
            return int(v)
        elif t=='string':
            return v
        elif t=='PT_ERROR':
            return None
        elif t=='bool':
            return bool(v)
        elif key=='PR_ENTRYID':
            v=v.split(',')
            return self.obj.makeentryid(int(v[0]), int(v[1]))
        elif t=='binary':
            v=v.split(',')
            return self.obj.makebinarystring(int(v[0]), int(v[1]))
        elif t=='strings':
            res=[]
            pos=0
            while pos<len(v):
                ll=0
                while v[pos]>='0' and v[pos]<='9':
                    ll=ll*10+int(v[pos])
                    pos+=1
                assert v[pos]==':'
                pos+=1
                res.append(v[pos:pos+ll])
                pos+=ll
            return res
        print "Dunno how to handle key %s type %s value %s" % (key,t,v)
        return "%s:%s" % (t,v)

class Container:

    def __init__(self, obj):
        self.obj=obj

    def items(self, flags=0):
        """Returns items in the container

        @param flags: WAB_LOCAL_CONTAINERS,WAB_PROFILE_CONTENTS
        """
        x=self.obj.getcontentstable(flags)
        if x is None:
            raise doexception()
        return Table(x)



if __name__=='__main__':
    import sys
    fn=None
    if len(sys.argv)>1:
        fn=sys.argv[1]
        wab=WAB(False, fn)
    else:
        wab=WAB()
    root=wab.openobject(wab.getrootentry())
    for container in root.items(constants.WAB_LOCAL_CONTAINERS|constants.WAB_PROFILE_CONTENTS):
        print container['PR_DISPLAY_NAME']
        people=wab.openobject(container['PR_ENTRYID'])
        items=people.items()
        items.enableallcolumns(True) # we use brute force since the correct WAB way doesn't work
        
        for i in items:
            print " ",i['PR_DISPLAY_NAME']
            keys=i.keys()
            keys.sort()
            for k in keys:
                if k=='PR_DISPLAY_NAME':
                    continue
                s="    "+k+"  "+`i[k]`
                if len(s)>78:
                    s=s[:78]
                print s

    
    
    
